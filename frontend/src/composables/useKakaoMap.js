import { ref } from 'vue';

let kakaoMapLoadPromise = null;

export function useKakaoMap() {
  const mapStatus = ref('');
  const safeLinkMapStatus = ref('');

  // ─── SDK 로딩 ────────────────────────────────────────────────────────────
  function loadKakaoMapSdk() {
    if (window.kakao?.maps) {
      return new Promise((resolve) => window.kakao.maps.load(() => resolve(window.kakao)));
    }
    if (kakaoMapLoadPromise) return kakaoMapLoadPromise;

    const appKey = import.meta.env.VITE_KAKAO_MAP_APP_KEY;
    kakaoMapLoadPromise = new Promise((resolve, reject) => {
      if (!appKey) { reject(new Error('Missing Kakao map app key')); return; }
      const timeout = window.setTimeout(() => reject(new Error('Kakao Maps SDK load timeout')), 7000);
      const script = document.createElement('script');
      script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&autoload=false`;
      script.async = true;
      script.onload = () => {
        if (!window.kakao?.maps) {
          window.clearTimeout(timeout);
          reject(new Error('Kakao SDK loaded but maps namespace is missing'));
          return;
        }
        window.kakao.maps.load(() => { window.clearTimeout(timeout); resolve(window.kakao); });
      };
      script.onerror = () => { window.clearTimeout(timeout); reject(new Error('Failed to load Kakao Maps SDK script')); };
      document.head.appendChild(script);
    });
    return kakaoMapLoadPromise;
  }

  // ─── 난이도별 경로 색상 ──────────────────────────────────────────────────
  function difficultyColor(difficulty) {
    return { easy: '#22c55e', medium: '#f97316', hard: '#ef4444' }[difficulty] ?? '#22c55e';
  }

  // ─── 위험도에 따른 경로 색상 ────────────────────────────────────────────
  function _segmentColor(course, segIndex, totalSegs) {
    const risks = course.risk_factors || [];
    const hasHighRisk = risks.some((r) =>
      ['강수량', '강풍', '낙석', '추락', '급경사', '붕괴'].some((kw) => r.includes(kw)),
    );
    const hasMediumRisk = risks.length > 0;
    // 전체 경로를 3구간으로 나눠 위험 구간 표시
    const third = Math.floor(totalSegs / 3);
    if (hasHighRisk && segIndex >= third && segIndex < third * 2) return '#ef4444'; // 빨강(위험)
    if (hasMediumRisk && (segIndex < third || segIndex >= third * 2)) return '#f97316'; // 주황(주의)
    return difficultyColor(course.difficulty); // 기본 난이도 색상
  }

  // ─── 상세 지도 ───────────────────────────────────────────────────────────
  async function renderDetailMap(detailMapEl, selectedCourse, disasterZones = [], userLocation = null) {
    if (!detailMapEl) return;
    if (!selectedCourse?.lat || !selectedCourse?.lng) {
      renderCourseFallbackMap(detailMapEl, selectedCourse, '지도 좌표가 부족해 코스 단계로 표시합니다.');
      mapStatus.value = '지도 좌표가 부족해 코스 단계로 표시합니다.';
      return;
    }
    mapStatus.value = '카카오 지도를 불러오는 중입니다.';
    try {
      const kakao = await loadKakaoMapSdk();
      const trailhead = new kakao.maps.LatLng(selectedCourse.lat, selectedCourse.lng);
      const geometry = selectedCourse.route_geometry;
      const hasRoute = Array.isArray(geometry) && geometry.length >= 2;

      const map = new kakao.maps.Map(detailMapEl, { center: trailhead, level: hasRoute ? 6 : 5 });
      map.addOverlayMapTypeId(kakao.maps.MapTypeId.TERRAIN);

      // ── 사용자 현재 위치 ──────────────────────────────────────────────
      const hasUserLoc = userLocation?.lat && userLocation?.lng;
      if (hasUserLoc) {
        const userPos = new kakao.maps.LatLng(userLocation.lat, userLocation.lng);
        new kakao.maps.Circle({
          map, center: userPos, radius: 60,
          strokeWeight: 2, strokeColor: '#1d4ed8', strokeOpacity: 1,
          fillColor: '#3b82f6', fillOpacity: 0.55,
        });
        new kakao.maps.CustomOverlay({
          map, position: userPos,
          content: '<div style="background:#1d4ed8;color:#fff;font-size:10px;padding:2px 6px;border-radius:8px;white-space:nowrap;margin-bottom:4px;">📍 현재 위치</div>',
          yAnchor: 2.8,
        });
        new kakao.maps.Polyline({
          map, path: [userPos, trailhead],
          strokeWeight: 2, strokeColor: '#1d4ed8', strokeOpacity: 0.5, strokeStyle: 'shortdot',
        });
      }

      if (hasRoute) {
        const routePoints = geometry.map((p) => new kakao.maps.LatLng(p.lat, p.lng));
        const totalSegs = routePoints.length - 1;

        // 경로를 구간별로 나눠 위험도 색상 적용
        for (let i = 0; i < totalSegs; i++) {
          const segColor = _segmentColor(selectedCourse, i, totalSegs);
          const isDanger = segColor === '#ef4444';
          new kakao.maps.Polyline({
            map, path: [routePoints[i], routePoints[i + 1]],
            strokeWeight: isDanger ? 5 : 4,
            strokeColor: segColor,
            strokeOpacity: 0.9,
            strokeStyle: isDanger ? 'shortdash' : 'solid',
          });
        }

        // 위험 구간 마커 (중간 지점)
        const risks = selectedCourse.risk_factors || [];
        if (risks.length && totalSegs >= 2) {
          const midIdx = Math.floor(totalSegs / 2);
          const midPos = routePoints[midIdx];
          const riskLabel = risks[0].length > 14 ? risks[0].slice(0, 14) + '…' : risks[0];
          new kakao.maps.CustomOverlay({
            map, position: midPos,
            content: `<div style="background:#ef4444;color:#fff;font-size:10px;padding:3px 7px;border-radius:8px;white-space:nowrap;font-weight:700;">⚠ ${riskLabel}</div>`,
            yAnchor: 2.5,
          });
        }

        const bounds = new kakao.maps.LatLngBounds();
        routePoints.forEach((p) => bounds.extend(p));
        if (hasUserLoc) bounds.extend(new kakao.maps.LatLng(userLocation.lat, userLocation.lng));
        map.setBounds(bounds);
      } else {
        const routeColor = difficultyColor(selectedCourse.difficulty);
        new kakao.maps.Circle({
          map, center: trailhead, radius: 400,
          strokeWeight: 2, strokeColor: routeColor, strokeOpacity: 0.6, strokeStyle: 'dashed',
          fillColor: routeColor, fillOpacity: 0.08,
        });
      }

      mapStatus.value = '';
      if (disasterZones.length) addDisasterZoneOverlays(map, kakao, disasterZones, selectedCourse.lat, selectedCourse.lng);
    } catch (err) {
      console.error('Kakao map detail render failed', err);
      renderCourseFallbackMap(detailMapEl, selectedCourse, '카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.');
      mapStatus.value = '카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.';
    }
  }

  // ─── 세이프링크 지도 ─────────────────────────────────────────────────────
  async function renderSafeLinkMap(safeLinkMapEl, selectedCourse) {
    if (!safeLinkMapEl) return;
    if (!selectedCourse?.lat || !selectedCourse?.lng) {
      renderCourseFallbackMap(safeLinkMapEl, selectedCourse, '선택된 코스의 지도 좌표가 부족합니다.');
      safeLinkMapStatus.value = '선택된 코스의 지도 좌표가 부족합니다.';
      return;
    }
    safeLinkMapStatus.value = '카카오 지도를 불러오는 중입니다.';
    try {
      const kakao = await loadKakaoMapSdk();
      const trailhead = new kakao.maps.LatLng(selectedCourse.lat, selectedCourse.lng);
      const geometry = selectedCourse.route_geometry;
      const hasRoute = Array.isArray(geometry) && geometry.length >= 2;
      const map = new kakao.maps.Map(safeLinkMapEl, { center: trailhead, level: hasRoute ? 6 : 5 });
      map.addOverlayMapTypeId(kakao.maps.MapTypeId.TERRAIN);

      if (hasRoute) {
        const routePath = geometry.map((p) => new kakao.maps.LatLng(p.lat, p.lng));
        new kakao.maps.Polyline({
          map, path: routePath,
          strokeWeight: 4, strokeColor: '#22c55e', strokeOpacity: 0.7, strokeStyle: 'solid',
        });
        const bounds = new kakao.maps.LatLngBounds();
        routePath.forEach((p) => bounds.extend(p));
        map.setBounds(bounds);
      }
      new kakao.maps.Marker({ map, position: trailhead, title: '등산로 입구' });
      safeLinkMapStatus.value = '';
    } catch (err) {
      console.error('Kakao map Safe Link render failed', err);
      renderCourseFallbackMap(safeLinkMapEl, selectedCourse, '카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.');
      safeLinkMapStatus.value = '카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.';
    }
  }

  // ─── Fallback SVG 지도 ───────────────────────────────────────────────────
  function renderCourseFallbackMap(container, course, statusText = '') {
    if (!container) return;
    const timeline = (course?.highlights || []).map(parseTimelineHighlight).filter(Boolean);
    const displayPoints = [{ x: 38, y: 122 }, { x: 146, y: 82 }, { x: 252, y: 116 }];
    const routePath = displayPoints.map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`).join(' ');
    const stops = buildFallbackRouteStops(timeline, displayPoints);
    const stopCircleMarkup = stops
      .map((s) => `<circle class="fallback-node ${s.type}" cx="${s.point.x}" cy="${s.point.y}" r="${s.type === 'waypoint' ? 5 : 7}" />`)
      .join('');
    const stopMarkup = stops
      .map((s) => `<div class="fallback-stop ${s.type}" style="left:${toPercent(s.labelPoint.x, 290)}%; top:${toPercent(s.labelPoint.y, 180)}%"><span>${escapeHtml(s.label)}</span></div>`)
      .join('');
    const statusOverlay = statusText ? `<div class="fallback-status-overlay">ℹ️ ${escapeHtml(statusText)}</div>` : '';

    container.innerHTML = `
      <div class="fallback-map estimated">
        <svg viewBox="0 0 290 180" aria-hidden="true">
          <defs><linearGradient id="routeGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#11a361" /><stop offset="100%" stop-color="#2563eb" />
          </linearGradient></defs>
          <path class="fallback-route-shadow" d="${routePath}" />
          <path class="fallback-route" d="${routePath}" />
          ${stopCircleMarkup}
        </svg>
        ${stopMarkup}
        <div class="fallback-distance">${escapeHtml(course?.distance_km ?? '-')}km</div>
        ${statusOverlay}
      </div>
    `;
  }

  // ─── Fallback 내부 헬퍼 ──────────────────────────────────────────────────
  function parseTimelineHighlight(item) {
    const text = String(item || '').trim();
    if (!text) return null;
    const [label, ...rest] = text.split(':');
    if (rest.length) return { label: label.trim(), value: rest.join(':').trim() };
    return { label: '정보', value: text };
  }

  function buildFallbackRouteStops(timeline, points) {
    const startLabel = timeline[0]?.value || '출발';
    const endLabel = timeline.find((item) => item.label.includes('도착'))?.value || timeline.at(-1)?.value || '도착';
    const waypointItems = timeline
      .filter((item) => item.value && !item.label.includes('출발') && !item.label.includes('도착'))
      .slice(0, 3);
    const stops = [{ type: 'start', label: shortStopLabel(startLabel), point: pointAtRouteFraction(points, 0) }];
    waypointItems.forEach((item, index) => {
      stops.push({ type: 'waypoint', label: shortStopLabel(item.value), point: pointAtRouteFraction(points, (index + 1) / (waypointItems.length + 1)) });
    });
    stops.push({ type: 'end', label: shortStopLabel(endLabel), point: pointAtRouteFraction(points, 1) });
    return stops.map((s, i) => ({ ...s, labelPoint: labelPointForStop(s.point, s.type, i) }));
  }

  function labelPointForStop(point, type, index) {
    const verticalOffset = type === 'waypoint' ? -22 : 20;
    const horizontalOffset = type === 'start' ? 30 : type === 'end' ? -30 : index % 2 ? 16 : -16;
    return { x: clamp(point.x + horizontalOffset, 42, 248), y: clamp(point.y + verticalOffset, 24, 156) };
  }

  function pointAtRouteFraction(points, fraction) {
    if (points.length <= 1) return points[0] || { x: 145, y: 90 };
    const clamped = Math.min(1, Math.max(0, fraction));
    const segments = points.slice(1).map((p, i) => {
      const prev = points[i];
      return { from: prev, to: p, length: Math.hypot(p.x - prev.x, p.y - prev.y) };
    });
    const total = segments.reduce((sum, s) => sum + s.length, 0) || 1;
    let target = total * clamped;
    for (const seg of segments) {
      if (target <= seg.length) {
        const ratio = seg.length ? target / seg.length : 0;
        return { x: seg.from.x + (seg.to.x - seg.from.x) * ratio, y: seg.from.y + (seg.to.y - seg.from.y) * ratio };
      }
      target -= seg.length;
    }
    return points.at(-1);
  }

  function shortStopLabel(value) {
    const text = String(value || '').replace(/\s+/g, ' ').trim();
    if (!text) return '';
    return text.length > 10 ? `${text.slice(0, 10)}...` : text;
  }

  function toPercent(value, max) { return (value / max) * 100; }
  function clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }
  function escapeHtml(value) {
    return String(value || '')
      .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
  }

  // ─── 보호자 실시간 위치 지도 (궤적 포함) ────────────────────────────────
  async function renderGuardianMap(containerEl, session) {
    if (!containerEl || !session) return;
    const lat = session.current_lat ?? session.course_lat;
    const lng = session.current_lng ?? session.course_lng;
    if (!lat || !lng) {
      containerEl.innerHTML = '<div class="guardian-map-placeholder">위치 정보 없음</div>';
      return;
    }
    try {
      const kakao = await loadKakaoMapSdk();
      const center = new kakao.maps.LatLng(lat, lng);
      const map = new kakao.maps.Map(containerEl, { center, level: 5 });
      map.addOverlayMapTypeId(kakao.maps.MapTypeId.TERRAIN);

      // 이동 궤적 폴리라인
      const trail = Array.isArray(session.trail) ? session.trail : [];
      if (trail.length >= 2) {
        const trailPath = trail.map((p) => new kakao.maps.LatLng(p.lat, p.lng));
        new kakao.maps.Polyline({
          map, path: trailPath,
          strokeWeight: 3, strokeColor: '#3b82f6', strokeOpacity: 0.7, strokeStyle: 'solid',
        });
        const bounds = new kakao.maps.LatLngBounds();
        trailPath.forEach((p) => bounds.extend(p));
        map.setBounds(bounds);
      }

      // 현재 위치 파란 원
      new kakao.maps.Circle({
        map, center, radius: 40,
        strokeWeight: 3, strokeColor: '#1d4ed8', strokeOpacity: 1,
        fillColor: '#3b82f6', fillOpacity: 0.55,
      });
      // 현재 위치 레이블
      new kakao.maps.CustomOverlay({
        map, position: center,
        content: '<div style="background:#1d4ed8;color:#fff;font-size:10px;padding:2px 6px;border-radius:8px;white-space:nowrap;margin-bottom:4px;">📍 현재 위치</div>',
        yAnchor: 2.8,
      });
    } catch {
      containerEl.innerHTML = '<div class="guardian-map-placeholder">지도 로드 실패</div>';
    }
  }

  // ─── 재난위험지구 오버레이 ───────────────────────────────────────────────
  function addDisasterZoneOverlays(map, kakao, zones, courseLat, courseLng) {
    if (!zones || !zones.length) return;
    const offsets = [[0.003, 0.002], [-0.004, 0.005], [0.005, -0.003], [-0.002, -0.006], [0.006, 0.004]];
    zones.slice(0, 5).forEach((zone, i) => {
      const [dlat, dlng] = offsets[i % offsets.length];
      const zoneCenter = new kakao.maps.LatLng(courseLat + dlat, courseLng + dlng);
      new kakao.maps.Circle({
        map, center: zoneCenter, radius: 120,
        strokeWeight: 2, strokeColor: '#cf3528', strokeOpacity: 0.9, strokeStyle: 'dashed',
        fillColor: '#ef4444', fillOpacity: 0.14,
      });
      const label = zone.district || zone.location || '위험지구';
      const overlay = new kakao.maps.CustomOverlay({
        map, position: zoneCenter,
        content: `<div style="background:#cf3528;color:#fff;font-size:10px;padding:2px 5px;border-radius:4px;white-space:nowrap;">⚠ ${label.slice(0, 10)}</div>`,
        yAnchor: 2.2,
      });
      void overlay;
    });
  }

  return { mapStatus, safeLinkMapStatus, renderDetailMap, renderSafeLinkMap, renderGuardianMap, addDisasterZoneOverlays, loadKakaoMapSdk };
}
