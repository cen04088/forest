import { ref } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Leaflet 기본 마커 아이콘 경로 버그 수정 (Vite 환경)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: '', iconUrl: '', shadowUrl: '' });

// 지도 인스턴스 재사용 (DOM 엘리먼트 키)
const _instances = new WeakMap();

// 코스 개요 지도 (전체 핀 보기) — 싱글톤
const _overviewMarkers = new Map(); // courseId → L.Marker
let _overviewMapEl = null;
let _overviewMapInst = null;
let _overviewRangeCircle = null;
let _overviewStartMarker = null;
let _overviewTrailLayer = null;

// 출발지 지도 선택 모드
let _pickClickHandler = null;
let _pickMarker = null;

// OSM 타일 레이어
function _osmTile() {
  return L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://openstreetmap.org">OpenStreetMap</a>',
    maxZoom: 18,
  });
}

function _getOrCreateMap(el, center, zoom) {
  if (_instances.has(el)) {
    const m = _instances.get(el);
    // 레이어 전부 제거 (타일 제외)
    m.eachLayer((layer) => { if (!(layer instanceof L.TileLayer)) m.removeLayer(layer); });
    m.setView(center, zoom);
    return m;
  }
  const map = L.map(el, { center, zoom, zoomControl: true, attributionControl: true });
  _osmTile().addTo(map);
  _instances.set(el, map);
  return map;
}

// 난이도 색상
function _difficultyColor(difficulty) {
  return { easy: '#22c55e', medium: '#f97316', hard: '#ef4444' }[difficulty] ?? '#22c55e';
}

// 위험 요인에 따른 구간별 색상
function _segmentColor(course, segIndex, totalSegs) {
  const risks = course.risk_factors || [];
  const hasHighRisk = risks.some((r) =>
    ['강수량', '강풍', '낙석', '추락', '급경사', '붕괴'].some((kw) => r.includes(kw)),
  );
  const hasMediumRisk = risks.length > 0;
  const third = Math.floor(totalSegs / 3);
  if (hasHighRisk && segIndex >= third && segIndex < third * 2) return '#ef4444';
  if (hasMediumRisk && (segIndex < third || segIndex >= third * 2)) return '#f97316';
  return _difficultyColor(course.difficulty);
}

export function useLeafletMap() {
  const mapStatus = ref('');
  const safeLinkMapStatus = ref('');

  // ─── 코스 상세 지도 ───────────────────────────────────────────────────────
  async function renderDetailMap(el, course, disasterZones = []) {
    if (!el) return;
    if (!course?.lat || !course?.lng) {
      mapStatus.value = '좌표 정보가 없어 지도를 표시할 수 없습니다.';
      return;
    }
    mapStatus.value = '';

    const center = [course.lat, course.lng];
    const geometry = course.route_geometry;
    const hasRoute = Array.isArray(geometry) && geometry.length >= 2;
    const map = _getOrCreateMap(el, center, hasRoute ? 13 : 14);

    if (hasRoute) {
      const points = geometry.map((p) => [p.lat, p.lng]);
      const totalSegs = points.length - 1;

      // 구간별 위험도 색상
      for (let i = 0; i < totalSegs; i++) {
        const color = _segmentColor(course, i, totalSegs);
        const isDanger = color === '#ef4444';
        L.polyline([points[i], points[i + 1]], {
          color, weight: isDanger ? 5 : 4,
          opacity: 0.9,
          dashArray: isDanger ? '8 4' : null,
        }).addTo(map);
      }

      // 위험 구간 마커
      const risks = course.risk_factors || [];
      if (risks.length && totalSegs >= 2) {
        const mid = points[Math.floor(totalSegs / 2)];
        const label = risks[0].length > 14 ? risks[0].slice(0, 14) + '…' : risks[0];
        L.marker(mid, {
          icon: L.divIcon({
            html: `<div style="background:#ef4444;color:#fff;font-size:11px;padding:3px 7px;border-radius:8px;white-space:nowrap;font-weight:700;box-shadow:0 1px 4px rgba(0,0,0,0.3);">⚠ ${label}</div>`,
            className: '',
            iconAnchor: [0, 0],
          }),
        }).addTo(map);
      }

      // 출발점 마커
      L.circleMarker(points[0], {
        radius: 8, color: '#166534', fillColor: '#22c55e', fillOpacity: 0.9, weight: 2,
      }).addTo(map).bindTooltip('🏁 출발', { permanent: false });

      // 도착점 마커
      L.circleMarker(points[totalSegs], {
        radius: 8, color: '#7c3aed', fillColor: '#a78bfa', fillOpacity: 0.9, weight: 2,
      }).addTo(map).bindTooltip('🎯 도착', { permanent: false });

      map.fitBounds(L.latLngBounds(points), { padding: [24, 24] });
    } else {
      // 경로 없음: 출발지 원
      L.circle(center, {
        radius: 300,
        color: _difficultyColor(course.difficulty),
        fillOpacity: 0.08,
        dashArray: '6 4',
      }).addTo(map);
      L.circleMarker(center, {
        radius: 8, color: '#166534', fillColor: '#22c55e', fillOpacity: 0.9, weight: 2,
      }).addTo(map).bindTooltip(course.name || '코스 위치', { permanent: false });
    }

    // 재난위험지구 오버레이
    if (disasterZones.length) {
      _addDisasterZoneOverlays(map, disasterZones, course.lat, course.lng);
    }
  }

  // ─── 안전공유 지도 ─────────────────────────────────────────────────────────
  async function renderSafeLinkMap(el, course) {
    if (!el) return;
    if (!course?.lat || !course?.lng) {
      safeLinkMapStatus.value = '선택된 코스의 좌표가 없습니다.';
      return;
    }
    safeLinkMapStatus.value = '';

    const center = [course.lat, course.lng];
    const geometry = course.route_geometry;
    const hasRoute = Array.isArray(geometry) && geometry.length >= 2;
    const map = _getOrCreateMap(el, center, hasRoute ? 13 : 14);

    if (hasRoute) {
      const points = geometry.map((p) => [p.lat, p.lng]);
      L.polyline(points, { color: '#22c55e', weight: 4, opacity: 0.75 }).addTo(map);
      map.fitBounds(L.latLngBounds(points), { padding: [24, 24] });
    }

    L.circleMarker(center, {
      radius: 10, color: '#166534', fillColor: '#22c55e', fillOpacity: 0.9, weight: 2,
    }).addTo(map).bindTooltip('🏁 등산로 입구', { permanent: false });
  }

  // ─── 보호자 실시간 지도 ────────────────────────────────────────────────────
  async function renderGuardianMap(el, session) {
    if (!el || !session) return;
    const lat = session.current_lat ?? session.course_lat;
    const lng = session.current_lng ?? session.course_lng;
    if (!lat || !lng) {
      el.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#9ca3af;font-size:13px;">위치 정보 없음</div>';
      return;
    }

    const center = [lat, lng];
    const trail = Array.isArray(session.trail) ? session.trail : [];
    const zoom = trail.length >= 2 ? 14 : 15;
    const map = _getOrCreateMap(el, center, zoom);

    // 매 갱신마다 이전 레이어 제거 후 재그리기
    if (!map._guardianLayerGroup) {
      map._guardianLayerGroup = L.layerGroup().addTo(map);
    }
    map._guardianLayerGroup.clearLayers();

    const lg = map._guardianLayerGroup;

    // ── 궤적 선 ────────────────────────────────
    if (trail.length >= 2) {
      const pts = trail.map((p) => [p.lat, p.lng]);
      L.polyline(pts, { color: '#3b82f6', weight: 3, opacity: 0.75 }).addTo(lg);
      map.fitBounds(L.latLngBounds(pts), { padding: [40, 40], maxZoom: 15 });
    }

    // ── 5분 간격 waypoint 점 ───────────────────
    const fmt = (ts) => {
      if (!ts) return '시간 미상';
      const d = new Date(ts * 1000);
      const hh = String(d.getHours()).padStart(2, '0');
      const mm = String(d.getMinutes()).padStart(2, '0');
      const elapsed = Math.floor((Date.now() / 1000 - ts) / 60);
      const ago = elapsed < 1 ? '방금' : elapsed < 60 ? `${elapsed}분 전` : `${Math.floor(elapsed/60)}시간 ${elapsed%60}분 전`;
      return `${hh}:${mm} (${ago})`;
    };

    trail.forEach((p, i) => {
      const isFirst = i === 0;
      const isLast = i === trail.length - 1;
      const label = isFirst ? '🚩 출발' : `📍 ${i}번째 기록`;
      const timeStr = fmt(p.recorded_at);

      if (!isLast) {
        L.circleMarker([p.lat, p.lng], {
          radius: isFirst ? 7 : 5,
          color: '#1d4ed8',
          fillColor: isFirst ? '#facc15' : '#93c5fd',
          fillOpacity: 0.9,
          weight: 2,
        }).addTo(lg).bindPopup(
          `<div style="font-size:12px;text-align:center;line-height:1.6">
            <div style="font-weight:700">${label}</div>
            <div style="color:#6b7280">${timeStr}</div>
          </div>`,
          { maxWidth: 160 }
        );
      }
    });

    // ── 현재 위치 마커 (파란 점) ───────────────
    L.circleMarker(center, {
      radius: 12, color: '#1d4ed8', fillColor: '#3b82f6', fillOpacity: 0.85, weight: 3,
    }).addTo(lg).bindPopup(
      `<div style="font-size:12px;text-align:center;line-height:1.6">
        <div style="font-weight:700">📍 현재 위치</div>
        <div style="color:#6b7280">${fmt(session.location_ts)}</div>
      </div>`,
      { maxWidth: 160 }
    );

    if (trail.length < 2) map.setView(center, zoom);
  }

  // ─── 재난위험지구 오버레이 ─────────────────────────────────────────────────
  function _addDisasterZoneOverlays(map, zones, courseLat, courseLng) {
    const offsets = [[0.003, 0.002], [-0.004, 0.005], [0.005, -0.003], [-0.002, -0.006], [0.006, 0.004]];
    zones.slice(0, 5).forEach((zone, i) => {
      const [dlat, dlng] = offsets[i % offsets.length];
      const pos = [courseLat + dlat, courseLng + dlng];
      L.circle(pos, {
        radius: 120, color: '#cf3528', fillColor: '#ef4444', fillOpacity: 0.14,
        weight: 2, dashArray: '5 4',
      }).addTo(map);
      const label = (zone.district || zone.location || '위험지구').slice(0, 10);
      L.marker(pos, {
        icon: L.divIcon({
          html: `<div style="background:#cf3528;color:#fff;font-size:10px;padding:2px 5px;border-radius:4px;white-space:nowrap;">⚠ ${label}</div>`,
          className: '',
          iconAnchor: [0, 0],
        }),
      }).addTo(map);
    });
  }

  function addDisasterZoneOverlays(map, _kakao, zones, lat, lng) {
    _addDisasterZoneOverlays(map, zones, lat, lng);
  }

  // ─── 코스 개요 지도: 전체 핀 보기 ─────────────────────────────────────────
  function _safetyPinColor(course) {
    if (course.safety_score != null) {
      if (course.safety_score >= 70) return '#22c55e';
      if (course.safety_score >= 40) return '#f97316';
      return '#ef4444';
    }
    return _difficultyColor(course.difficulty);
  }

  function _makeCourseIcon(course, isSelected) {
    const ICONS = { easy: '/marker-easy.png', medium: '/marker-medium.png', hard: '/marker-hard.png' };
    const iconUrl = ICONS[course.difficulty] ?? '/marker-easy.png';
    const opacity = course._muted ? 0.3 : 1;
    // 이미지 비율 약 1:1.34 (512x687)
    const w = isSelected ? 48 : (course._highlighted ? 40 : 34);
    const h = Math.round(w * 1.34);

    let filterVal;
    if (isSelected) {
      filterVal = 'drop-shadow(0 0 6px rgba(0,0,0,.55)) drop-shadow(0 4px 10px rgba(0,0,0,.4))';
    } else if (course._highlighted) {
      filterVal = 'drop-shadow(0 0 6px #f59e0b) drop-shadow(0 2px 6px rgba(0,0,0,.35))';
    } else {
      filterVal = 'drop-shadow(0 2px 5px rgba(0,0,0,.35))';
    }

    return L.divIcon({
      className: '',
      html: `<img src="${iconUrl}" width="${w}" height="${h}" style="opacity:${opacity};filter:${filterVal};display:block;transition:filter .15s;" />`,
      iconSize: [w, h],
      iconAnchor: [w / 2, h],
      popupAnchor: [0, -(h + 4)],
    });
  }

  function _makeCoursePopup(course) {
    const diff = { easy: '초급', medium: '중급', hard: '고급' }[course.difficulty] || '';
    const color = course._muted ? '#9ca3af' : _safetyPinColor(course);
    const safety = course.safety_label
      ? `<div style="margin-top:4px;font-size:12px">&#128737; ${course.safety_label}</div>` : '';

    // walk_time_min 속성 존재 여부로 산 vs 코스 판별 (elevation_m은 null일 수 있음)
    const isMountain = 'walk_time_min' in course;

    let statsHtml;
    if (isMountain) {
      const loH = Math.floor((course.walk_time_min || 0) / 60);
      const hiH = Math.floor((course.walk_time_max || 0) / 60);
      const elevText = course.elevation_m != null ? `${course.elevation_m}m` : '고도미상';
      const timeText = (loH || hiH) ? `${loH}~${hiH}시간` : '-';
      const trailPart = course.trail_count ? `<div style="font-size:12px;color:#374151">&#128506; ${course.trail_count}개 탐방로</div>` : '';
      const regionPart = course.region ? `<div style="font-size:12px;color:#374151">&#128205; ${course.region}</div>` : '';
      statsHtml = `
        <div style="font-size:12px;margin-top:5px;color:#374151">&#9968; ${elevText} &nbsp; &#8987; ${timeText}</div>
        ${trailPart}${regionPart}`;
    } else {
      const h = Math.floor((course.duration_min || 0) / 60);
      const m = (course.duration_min || 0) % 60;
      const dur = course.duration_min ? (h ? `${h}시간 ${m ? m + '분' : ''}` : `${m}분`) : '-';
      const distText = course.distance_km != null ? `${course.distance_km}km` : '-';
      const gainText = course.elevation_gain_m != null ? `${course.elevation_gain_m}m` : '-';
      statsHtml = `
        <div style="font-size:12px;margin-top:5px;color:#374151">&#128207; ${distText} &nbsp; &#8987; ${dur}</div>
        <div style="font-size:12px;color:#374151">&#8679; ${gainText} 고도</div>`;
    }

    const title = isMountain
      ? (course.name || '이름없음')
      : `${course.mountain || ''} · ${course.name || ''}`;
    return `
      <div style="min-width:158px;font-family:inherit;line-height:1.4">
        <div style="font-weight:700;font-size:13px;margin-bottom:5px">${title}</div>
        <span style="background:${color}22;color:${color};font-size:11px;font-weight:600;padding:2px 7px;border-radius:8px">${diff}</span>
        ${statsHtml}
        ${safety}
      </div>`;
  }

  function _renderStartRangeOverlay(startLocation, radiusKm) {
    if (!_overviewMapInst) return;
    if (_overviewRangeCircle) {
      _overviewRangeCircle.remove();
      _overviewRangeCircle = null;
    }
    if (_overviewStartMarker) {
      _overviewStartMarker.remove();
      _overviewStartMarker = null;
    }

    const lat = startLocation?.lat;
    const lng = startLocation?.lng;
    const radiusMeters = Number(radiusKm || 0) * 1000;
    if (lat == null || lng == null || !radiusMeters) return;

    const center = [lat, lng];
    _overviewRangeCircle = L.circle(center, {
      radius: radiusMeters,
      color: '#2563eb',
      weight: 2,
      opacity: 0.82,
      fillColor: '#3b82f6',
      fillOpacity: 0.08,
      dashArray: '8 6',
    }).addTo(_overviewMapInst);

    _overviewStartMarker = L.circleMarker(center, {
      radius: 7,
      color: '#1d4ed8',
      fillColor: '#2563eb',
      fillOpacity: 0.95,
      weight: 3,
    }).addTo(_overviewMapInst).bindTooltip(`시작점 · ${radiusKm}km`, { permanent: false });

    const bounds = _overviewRangeCircle.getBounds();
    if (bounds.isValid()) {
      _overviewMapInst.fitBounds(bounds, { padding: [28, 28], maxZoom: 11 });
    }
  }

  function _renderMountainTrailOverlay(trails, selectedMountain) {
    if (!_overviewMapInst) return;
    if (_overviewTrailLayer) {
      _overviewTrailLayer.remove();
      _overviewTrailLayer = null;
    }

    const validTrails = (trails || []).filter((trail) => Array.isArray(trail.route_geometry) && trail.route_geometry.length >= 2);
    if (!validTrails.length) return;

    _overviewTrailLayer = L.layerGroup().addTo(_overviewMapInst);
    const bounds = [];
    validTrails.forEach((trail, index) => {
      const points = trail.route_geometry.map((p) => [p.lat, p.lng]).filter(([lat, lng]) => lat && lng);
      if (points.length < 2) return;
      bounds.push(...points);
      const color = _difficultyColor(trail.difficulty);
      L.polyline(points, {
        color,
        weight: index < 12 ? 4 : 3,
        opacity: index < 12 ? 0.78 : 0.45,
        lineCap: 'round',
        lineJoin: 'round',
      })
        .addTo(_overviewTrailLayer)
        .bindTooltip(
          `${trail.name || '탐방로'}${trail.distance_km ? ` · ${trail.distance_km}km` : ''}`,
          { sticky: true },
        );
    });

    if (bounds.length) {
      const trailBounds = L.latLngBounds(bounds);
      if (trailBounds.isValid()) _overviewMapInst.fitBounds(trailBounds, { padding: [28, 28], maxZoom: 14 });
    } else if (selectedMountain?.lat && selectedMountain?.lng) {
      _overviewMapInst.setView([selectedMountain.lat, selectedMountain.lng], 13);
    }
  }

  function renderOverviewMap(el, courses, selectedId, onSelect, options = {}) {
    if (!el) return;

    if (_overviewMapEl !== el || !_overviewMapInst) {
      if (_overviewMapInst) { _overviewMapInst.remove(); _overviewMarkers.clear(); }
      _overviewMapInst = L.map(el, { center: [37.55, 127.02], zoom: 11 });
      _osmTile().addTo(_overviewMapInst);
      _overviewMapEl = el;
    }

    const validCourses = (courses || []).filter((c) => c.lat && c.lng);
    const ids = new Set(validCourses.map((c) => c.id));

    // 사라진 코스 마커 제거
    for (const [id, m] of _overviewMarkers) {
      if (!ids.has(id)) { m.remove(); _overviewMarkers.delete(id); }
    }

    let isFirstLoad = false;
    validCourses.forEach((course) => {
      const isSelected = course.id === selectedId;
      const icon = _makeCourseIcon(course, isSelected);

      if (_overviewMarkers.has(course.id)) {
        const m = _overviewMarkers.get(course.id);
        m.setIcon(icon);
        m.setPopupContent(_makeCoursePopup(course));
      } else {
        const m = L.marker([course.lat, course.lng], { icon })
          .addTo(_overviewMapInst)
          .bindPopup(_makeCoursePopup(course));
        m.on('click', () => { m.openPopup(); onSelect?.(course); });
        _overviewMarkers.set(course.id, m);
        isFirstLoad = true;
      }
    });

    // 첫 로드 시 전체 bounds에 맞춤
    if (isFirstLoad && validCourses.length) {
      const bounds = L.latLngBounds(validCourses.map((c) => [c.lat, c.lng]));
      if (bounds.isValid()) _overviewMapInst.fitBounds(bounds, { padding: [32, 32] });
    }

    _renderStartRangeOverlay(options.startLocation, options.radiusKm);
    _renderMountainTrailOverlay(options.trails, options.selectedMountain);
  }

  function focusOverviewCourse(course) {
    if (!_overviewMapInst || !course?.lat) return;
    _overviewMapInst.setView([course.lat, course.lng], 14, { animate: true });
    const m = _overviewMarkers.get(course.id);
    if (m) m.openPopup();
  }

  // ─── 출발지 지도 선택 모드 ────────────────────────────────────────────────
  function enableLocationPick(onPick) {
    if (!_overviewMapInst) return;
    disableLocationPick();
    _overviewMapInst.getContainer().style.cursor = 'crosshair';
    _pickClickHandler = (e) => {
      const { lat, lng } = e.latlng;
      if (_pickMarker) { _pickMarker.remove(); _pickMarker = null; }
      _pickMarker = L.marker([lat, lng], {
        icon: L.divIcon({
          className: '',
          html: `
            <div style="position:relative;width:40px;height:56px;filter:drop-shadow(0 4px 10px rgba(37,99,235,0.45))">
              <svg width="40" height="52" viewBox="0 0 40 52" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 1C9.5 1 1 9.5 1 20C1 33.5 20 51 20 51C20 51 39 33.5 39 20C39 9.5 30.5 1 20 1Z" fill="#2563eb" stroke="white" stroke-width="2"/>
                <circle cx="20" cy="20" r="9" fill="white" fill-opacity="0.95"/>
                <circle cx="20" cy="17" r="3.5" fill="#2563eb"/>
                <path d="M12 27c0-4.4 3.6-8 8-8s8 3.6 8 8" stroke="#2563eb" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <div style="position:absolute;bottom:-10px;left:50%;transform:translateX(-50%);white-space:nowrap;background:white;color:#1d4ed8;font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;border:1.5px solid #bfdbfe;letter-spacing:0.04em;box-shadow:0 1px 4px rgba(0,0,0,0.12)">출발지</div>
            </div>`,
          iconSize: [40, 66],
          iconAnchor: [20, 52],
          popupAnchor: [0, -56],
        }),
      }).addTo(_overviewMapInst);
      disableLocationPick();
      onPick({ lat, lng });
    };
    _overviewMapInst.on('click', _pickClickHandler);
  }

  function disableLocationPick() {
    if (!_overviewMapInst) return;
    if (_pickClickHandler) {
      _overviewMapInst.off('click', _pickClickHandler);
      _pickClickHandler = null;
    }
    _overviewMapInst.getContainer().style.cursor = '';
  }

  function clearLocationPickMarker() {
    if (_pickMarker) { _pickMarker.remove(); _pickMarker = null; }
  }

  // ─── 산행자 실시간 지도 (SafeLinkTab 산행 중) ─────────────────────────────
  async function renderLiveHikingMap(el, lat, lng, trail) {
    if (!el || lat == null || lng == null) return;
    await _loadLeaflet();
    const center = [lat, lng];
    const map = _getOrCreateMap(el, center, 16);

    if (!map._liveLayerGroup) {
      map._liveLayerGroup = L.layerGroup().addTo(map);
    }
    map._liveLayerGroup.clearLayers();
    const lg = map._liveLayerGroup;

    // 이동 궤적
    if (trail?.length >= 2) {
      const pts = trail.map((p) => [p.lat, p.lng]);
      L.polyline(pts, { color: '#22c55e', weight: 4, opacity: 0.85 }).addTo(lg);
    }

    // 출발점
    if (trail?.length >= 1) {
      L.circleMarker([trail[0].lat, trail[0].lng], {
        radius: 6, color: '#15803d', fillColor: '#facc15', fillOpacity: 1, weight: 2,
      }).addTo(lg).bindTooltip('출발', { permanent: false });
    }

    // 현재 위치 (파동 효과)
    L.circleMarker(center, {
      radius: 14, color: '#16a34a', fillColor: '#22c55e', fillOpacity: 0.25, weight: 2,
    }).addTo(lg);
    L.circleMarker(center, {
      radius: 7, color: '#15803d', fillColor: '#22c55e', fillOpacity: 1, weight: 2,
    }).addTo(lg).bindTooltip('현재 위치', { permanent: false });

    map.setView(center, map.getZoom());
  }

  return {
    mapStatus,
    safeLinkMapStatus,
    renderDetailMap,
    renderSafeLinkMap,
    renderGuardianMap,
    renderLiveHikingMap,
    addDisasterZoneOverlays,
    renderOverviewMap,
    focusOverviewCourse,
    enableLocationPick,
    disableLocationPick,
    clearLocationPickMarker,
  };
}
