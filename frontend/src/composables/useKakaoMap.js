/**
 * 카카오 지도 렌더링 Composable
 * SDK 로딩, 상세 지도, 세이프링크 지도, Fallback SVG 지도를 담당한다.
 */
import { ref } from 'vue';

// 모듈 레벨에서 Promise 캐시 (SDK는 한 번만 로딩)
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
      if (!appKey) {
        reject(new Error('Missing Kakao map app key'));
        return;
      }
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
        window.kakao.maps.load(() => {
          window.clearTimeout(timeout);
          resolve(window.kakao);
        });
      };
      script.onerror = () => {
        window.clearTimeout(timeout);
        reject(new Error('Failed to load Kakao Maps SDK script'));
      };
      document.head.appendChild(script);
    });
    return kakaoMapLoadPromise;
  }

  function kakaoRoutePath(kakao, course) {
    return (course?.route_geometry || [])
      .filter((p) => Number.isFinite(Number(p.lat)) && Number.isFinite(Number(p.lng)))
      .map((p) => new kakao.maps.LatLng(Number(p.lat), Number(p.lng)));
  }

  // ─── 상세 지도 ───────────────────────────────────────────────────────────
  async function renderDetailMap(detailMapEl, selectedCourse, routePoints) {
    if (!detailMapEl) return;
    if (!selectedCourse?.lat || !selectedCourse?.lng) {
      renderCourseFallbackMap(detailMapEl, selectedCourse, '지도 좌표가 부족해 코스 단계로 표시합니다.', { safeLink: false });
      mapStatus.value = '지도 좌표가 부족해 코스 단계로 표시합니다.';
      return;
    }
    if (routePoints.length < 2) {
      renderCourseFallbackMap(detailMapEl, selectedCourse, '정확한 등산로 선형이 없어 코스 프리뷰로 표시합니다.', { safeLink: false });
      mapStatus.value = '정확한 등산로 선형이 없어 JavaScript 코스 프리뷰로 표시합니다.';
      return;
    }
    mapStatus.value = '카카오 지도를 불러오는 중입니다.';
    try {
      const kakao = await loadKakaoMapSdk();
      const center = new kakao.maps.LatLng(selectedCourse.lat, selectedCourse.lng);
      const map = new kakao.maps.Map(detailMapEl, { center, level: 5 });
      new kakao.maps.Marker({ map, position: center, title: selectedCourse.name });
      const routePath = kakaoRoutePath(kakao, selectedCourse);
      if (routePath.length >= 2) {
        new kakao.maps.Polyline({
          map,
          path: routePath,
          strokeWeight: 6,
          strokeColor: selectedCourse.safety_decision === 'not_recommended' ? '#cf3528' : '#23864b',
          strokeOpacity: 0.9,
          strokeStyle: selectedCourse.safety_decision === 'recommend' ? 'solid' : 'shortdash',
        });
        const bounds = new kakao.maps.LatLngBounds();
        routePath.forEach((p) => bounds.extend(p));
        map.setBounds(bounds);
        mapStatus.value = '';
      } else {
        mapStatus.value = '정확한 등산로 선형이 없어 중심 위치만 표시합니다.';
      }
      new kakao.maps.Circle({
        map,
        center,
        radius: 180,
        strokeWeight: 2,
        strokeColor: '#d29a12',
        strokeOpacity: 0.9,
        strokeStyle: 'dashed',
        fillColor: '#d29a12',
        fillOpacity: 0.18,
      });
    } catch (err) {
      console.error('Kakao map detail render failed', err);
      renderCourseFallbackMap(detailMapEl, selectedCourse, '카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.', { safeLink: false });
      mapStatus.value = '카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.';
    }
  }

  // ─── 세이프링크 지도 ─────────────────────────────────────────────────────
  async function renderSafeLinkMap(safeLinkMapEl, selectedCourse, routePoints) {
    if (!safeLinkMapEl) return;
    if (!selectedCourse?.lat || !selectedCourse?.lng) {
      renderCourseFallbackMap(safeLinkMapEl, selectedCourse, '선택된 코스의 지도 좌표가 부족합니다.', { safeLink: true });
      safeLinkMapStatus.value = '선택된 코스의 지도 좌표가 부족합니다.';
      return;
    }
    if (routePoints.length < 2) {
      renderCourseFallbackMap(safeLinkMapEl, selectedCourse, '정확한 등산로 선형이 없어 코스 프리뷰로 표시합니다.', { safeLink: true });
      safeLinkMapStatus.value = '정확한 등산로 선형이 없어 JavaScript 코스 프리뷰로 표시합니다.';
      return;
    }
    safeLinkMapStatus.value = '카카오 지도를 불러오는 중입니다.';
    try {
      const kakao = await loadKakaoMapSdk();
      const courseLat = selectedCourse.lat;
      const courseLng = selectedCourse.lng;
      const start = new kakao.maps.LatLng(courseLat - 0.004, courseLng - 0.004);
      const current = new kakao.maps.LatLng(courseLat, courseLng);
      const next = new kakao.maps.LatLng(courseLat + 0.003, courseLng + 0.004);
      const map = new kakao.maps.Map(safeLinkMapEl, { center: current, level: 5 });
      new kakao.maps.Marker({ map, position: current, title: '공유 대상 현재 위치' });
      const routePath = kakaoRoutePath(kakao, selectedCourse);
      new kakao.maps.Polyline({
        map,
        path: routePath.length >= 2 ? routePath : [start, current, next],
        strokeWeight: 5,
        strokeColor: '#23864b',
        strokeOpacity: 0.9,
        strokeStyle: 'solid',
      });
      if (routePath.length >= 2) {
        const bounds = new kakao.maps.LatLngBounds();
        routePath.forEach((p) => bounds.extend(p));
        map.setBounds(bounds);
      }
      new kakao.maps.Circle({
        map,
        center: next,
        radius: 160,
        strokeWeight: 2,
        strokeColor: '#cf3528',
        strokeOpacity: 0.9,
        strokeStyle: 'dashed',
        fillColor: '#cf3528',
        fillOpacity: 0.16,
      });
      safeLinkMapStatus.value = '';
    } catch (err) {
      console.error('Kakao map Safe Link render failed', err);
      renderCourseFallbackMap(safeLinkMapEl, selectedCourse, '카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.', { safeLink: true });
      safeLinkMapStatus.value = '카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.';
    }
  }

  // ─── Fallback SVG 지도 ───────────────────────────────────────────────────
  function renderCourseFallbackMap(container, course, statusText = '', { safeLink = false } = {}) {
    if (!container) return;
    void safeLink;
    const timeline = (course?.highlights || []).map(parseTimelineHighlight).filter(Boolean);
    const routePoints = normalizeSvgRoutePoints(course?.route_geometry || []);
    const displayPoints =
      routePoints.length >= 2 ? routePoints : [{ x: 38, y: 122 }, { x: 146, y: 82 }, { x: 252, y: 116 }];
    const routePath = displayPoints.map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`).join(' ');
    const hasGeometry = routePoints.length >= 2;
    const stops = buildFallbackRouteStops(timeline, displayPoints);
    const stopCircleMarkup = stops
      .map(
        (s) =>
          `<circle class="fallback-node ${s.type}" cx="${s.point.x}" cy="${s.point.y}" r="${s.type === 'waypoint' ? 5 : 7}" />`,
      )
      .join('');
    const stopMarkup = stops
      .map(
        (s) => `
        <div class="fallback-stop ${s.type}" style="left:${toPercent(s.labelPoint.x, 290)}%; top:${toPercent(s.labelPoint.y, 180)}%">
          <span>${escapeHtml(s.label)}</span>
        </div>`,
      )
      .join('');

    const statusOverlay = statusText
      ? `<div class="fallback-status-overlay">ℹ️ ${escapeHtml(statusText)}</div>`
      : '';

    container.innerHTML = `
      <div class="fallback-map ${hasGeometry ? 'has-geometry' : 'estimated'}">
        <svg viewBox="0 0 290 180" aria-hidden="true">
          <defs>
            <linearGradient id="routeGradient" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#11a361" />
              <stop offset="100%" stop-color="#2563eb" />
            </linearGradient>
          </defs>
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
    const endLabel =
      timeline.find((item) => item.label.includes('도착'))?.value || timeline.at(-1)?.value || '도착';
    const waypointItems = timeline
      .filter((item) => item.value && !item.label.includes('출발') && !item.label.includes('도착'))
      .slice(0, 3);
    const stops = [{ type: 'start', label: shortStopLabel(startLabel), point: pointAtRouteFraction(points, 0) }];
    waypointItems.forEach((item, index) => {
      stops.push({
        type: 'waypoint',
        label: shortStopLabel(item.value),
        point: pointAtRouteFraction(points, (index + 1) / (waypointItems.length + 1)),
      });
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

  function normalizeSvgRoutePoints(points) {
    const valid = points
      .filter((p) => Number.isFinite(Number(p.lat)) && Number.isFinite(Number(p.lng)))
      .slice(0, 24);
    if (valid.length < 2) return [];
    const lats = valid.map((p) => Number(p.lat));
    const lngs = valid.map((p) => Number(p.lng));
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    const latSpan = maxLat - minLat || 1;
    const lngSpan = maxLng - minLng || 1;
    return valid.map((p) => ({
      x: 28 + ((Number(p.lng) - minLng) / lngSpan) * 234,
      y: 152 - ((Number(p.lat) - minLat) / latSpan) * 124,
    }));
  }

  function toPercent(value, max) { return (value / max) * 100; }
  function clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }
  function escapeHtml(value) {
    return String(value || '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  return { mapStatus, safeLinkMapStatus, renderDetailMap, renderSafeLinkMap };
}
