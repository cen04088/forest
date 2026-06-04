import { ref } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Leaflet 기본 마커 아이콘 경로 버그 수정 (Vite 환경)
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: '', iconUrl: '', shadowUrl: '' });

// 지도 인스턴스 재사용 (DOM 엘리먼트 키)
const _instances = new WeakMap();

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
  async function renderDetailMap(el, course, disasterZones = [], userLocation = null) {
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

    // 사용자 현재 위치
    if (userLocation?.lat && userLocation?.lng) {
      const userPos = [userLocation.lat, userLocation.lng];
      L.circleMarker(userPos, {
        radius: 10, color: '#1d4ed8', fillColor: '#3b82f6', fillOpacity: 0.7, weight: 2,
      }).addTo(map).bindTooltip('📍 현재 위치', { permanent: false });

      L.polyline([userPos, center], {
        color: '#1d4ed8', weight: 2, opacity: 0.5, dashArray: '6 4',
      }).addTo(map);
    }

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

      // 경로 전체가 보이도록 자동 확대
      const bounds = L.latLngBounds(points);
      if (userLocation?.lat) bounds.extend([userLocation.lat, userLocation.lng]);
      map.fitBounds(bounds, { padding: [24, 24] });
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

    // 이동 궤적
    if (trail.length >= 2) {
      const trailPoints = trail.map((p) => [p.lat, p.lng]);
      L.polyline(trailPoints, { color: '#3b82f6', weight: 3, opacity: 0.7 }).addTo(map);
      map.fitBounds(L.latLngBounds(trailPoints), { padding: [32, 32] });
    }

    // 현재 위치 마커
    L.circleMarker(center, {
      radius: 12, color: '#1d4ed8', fillColor: '#3b82f6', fillOpacity: 0.75, weight: 3,
    }).addTo(map).bindTooltip('📍 현재 위치', { permanent: false });

    map.setView(center);
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

  return {
    mapStatus,
    safeLinkMapStatus,
    renderDetailMap,
    renderSafeLinkMap,
    renderGuardianMap,
    addDisasterZoneOverlays,
  };
}
