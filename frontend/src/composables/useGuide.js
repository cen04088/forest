import { computed, reactive, ref } from 'vue';
import { fetchCourses, fetchDisasterZones, fetchWeather, fetchRecommendations, fetchVWorldTrails, fetchOSMTrails, fetchMountains, fetchMountainRecommendations, fetchMlRisk } from '../api.js';
import { fallbackCourses } from '../data/fallbackCourses.js';
import { fallbackMountainDescriptions } from '../data/fallbackMountainDescriptions.js';
import { fallbackMountains } from '../data/fallbackMountains.js';

// 경로 geometry 캐시 (courseId → { geometry, source })
const _geometryCache = new Map();

function _bestMatch(items, course) {
  if (!items?.length) return null;
  const courseNorm = (course.name || '').replace(/코스$/, '').replace(/\s/g, '').toLowerCase();
  const mountainNorm = (course.mountain || '').replace(/\s/g, '').toLowerCase();
  return (
    items.find((item) => {
      const n = (item.name || '').replace(/\s/g, '').toLowerCase();
      return courseNorm && n.includes(courseNorm);
    }) ||
    items.find((item) => {
      const n = (item.name || '').replace(/\s/g, '').toLowerCase();
      return mountainNorm && n.includes(mountainNorm);
    }) ||
    items[0]
  );
}

export async function fetchCourseGeometry(course) {
  if (!course?.lat || !course?.lng) return null;
  if (Array.isArray(course.route_geometry) && course.route_geometry.length >= 2) return course.route_geometry;

  const key = course.id || `${course.lat},${course.lng}`;
  if (_geometryCache.has(key)) return _geometryCache.get(key);

  // 1단계: VWorld API
  try {
    const result = await fetchVWorldTrails({
      mountainName: course.mountain || '',
      lat: course.lat,
      lng: course.lng,
      radius: 2,
    });
    const best = _bestMatch(result?.items, course);
    if (best?.route_geometry?.length >= 2) {
      _geometryCache.set(key, best.route_geometry);
      return best.route_geometry;
    }
  } catch {}

  // 2단계: OSM Overpass (VWorld 결과 없을 때)
  try {
    const osmResult = await fetchOSMTrails({
      lat: course.lat,
      lng: course.lng,
      mountainName: course.mountain || '',
      radius: 3000,
    });
    const best = _bestMatch(osmResult?.items, course);
    if (best?.route_geometry?.length >= 2) {
      _geometryCache.set(key, best.route_geometry);
      return best.route_geometry;
    }
  } catch {}

  // 둘 다 실패
  _geometryCache.set(key, null);
  return null;
}
import { useLocation } from './useLocation.js';
import { addDays, addMinutes, formatDateForInput, formatTimeForInput } from '../utils/dateHelpers.js';

// ── 싱글톤 상태 ─────────────────────────────────────────────────────────────
export const guideStep = ref('browse'); // 'browse' | 'courses'
export const publicCourses = ref([]);
export const publicMountains = ref([]);
export const recommendedMountains = ref([]);
export const alternativeMountains = ref([]);
export const selectedMountain = ref(null);
export const recommendations = ref([]);
export const alternatives = ref([]);
export const selectedCourse = ref(null);
export const weatherData = ref(null);
export const disasterZones = ref([]);
export const localMlRisk = ref(null);
export const resultState = ref('idle');
export const agentSummary = ref('산과 출발 조건을 선택하면 실제 탐방로, 날씨, 일몰, 위험 데이터를 종합해 안전 등급을 계산합니다.');
export const alternativeActions = ref([]);
export const loading = ref(false);
export const guideError = ref('');

const _initial = addMinutes(new Date(), 5);
export const minDepartureDate = formatDateForInput(_initial);
export const maxDepartureDate = formatDateForInput(addDays(_initial, 3));

export const profile = reactive({
  mountainName: '',
  departureDate: minDepartureDate,
  departureTime: formatTimeForInput(_initial),
  availableMinutes: 240,
  desiredHikingMinutes: 120,
  experience: 'beginner',
  difficultyFilter: 'all',
  transport: 'public',
  maxDistanceKm: 30,
  purpose: 'balanced',
});

const _PROFILE_FIELDS = ['experience', 'maxDistanceKm', 'availableMinutes', 'purpose'];
export const profileIsExplicitlySet = ref(localStorage.getItem('olla_profile_saved') === 'true');

try {
  const _saved = JSON.parse(localStorage.getItem('olla_user_profile') || '{}');
  for (const k of _PROFILE_FIELDS) {
    if (_saved[k] !== undefined) profile[k] = _saved[k];
  }
} catch {}

export function applyAndSaveProfile(updates) {
  for (const k of _PROFILE_FIELDS) {
    if (updates[k] !== undefined) profile[k] = updates[k];
  }
  try {
    localStorage.setItem('olla_user_profile', JSON.stringify(Object.fromEntries(_PROFILE_FIELDS.map(k => [k, profile[k]]))));
    localStorage.setItem('olla_profile_saved', 'true');
  } catch {}
  profileIsExplicitlySet.value = true;
}

export const { location, gpsStatus, gpsError, detectGPS } = useLocation();

// 사용자가 직접 지정한 출발지 (null이면 GPS 위치 사용)
export const customStartLocation = ref(null); // { lat, lng, name }

export const TAG_ICONS = {
  '조망': '🗻', '계곡': '💧', '단풍': '🍂', '야생화': '🌸',
  '역사문화': '🏯', '암릉': '🪨', '숲치유': '🌲', '일출·일몰': '🌅',
  '설경': '❄️', '호수·강뷰': '🌊', '억새': '🌾', '철쭉': '🌺',
  '야경': '🌃', '능선종주': '🏔', '100대명산': '🏆',
};

export const mountainSearch = ref('');

export function diffDotColor(difficulty) {
  if (difficulty === 'easy') return '#22c55e';
  if (difficulty === 'medium') return '#f97316';
  if (difficulty === 'hard') return '#ef4444';
  return '#9ca3af';
}

export const filteredMountains = computed(() => {
  const search = mountainSearch.value.trim().toLowerCase();
  const normalizedSearch = search.replace(/\s/g, '');
  const diff = profile.difficultyFilter;
  const safetyMap = new Map(
    [...recommendedMountains.value, ...alternativeMountains.value].map((m) => [m.id, m])
  );

  let base = publicMountains.value.map((m) => {
    const scored = safetyMap.get(m.id);
    return scored ? { ...m, ...scored } : m;
  });

  if (diff && diff !== 'all' && !search) {
    base = base.filter((m) => m.difficulty === diff);
  }

  if (search) {
    base = base.filter(
      (m) =>
        m.name.toLowerCase().replace(/\s/g, '').includes(normalizedSearch) ||
        (m.region || '').toLowerCase().replace(/\s/g, '').includes(normalizedSearch),
    );
  }

  return base.sort((a, b) => {
    if (search) {
      const aRank = searchRank(a, normalizedSearch);
      const bRank = searchRank(b, normalizedSearch);
      if (aRank !== bRank) return aRank - bRank;
    }
    const aRanked = !!a.safety_decision;
    const bRanked = !!b.safety_decision;
    if (aRanked !== bRanked) return aRanked ? -1 : 1;
    if (aRanked && bRanked) {
      const order = { recommend: 0, caution: 1, not_recommended: 2 };
      return (order[a.safety_decision] ?? 3) - (order[b.safety_decision] ?? 3);
    }
    return (b.crowding || 0) - (a.crowding || 0);
  });
});

export const mlRiskInfo = computed(() => {
  const m = selectedMountain.value;
  if (!m) return null;
  const scored = [...recommendedMountains.value, ...alternativeMountains.value].find((r) => r.id === m.id);
  return scored?.ml_risk_info || localMlRisk.value || null;
});

export const mlTrainingNote = computed(() => {
  const training = mlRiskInfo.value?.training;
  const rows = training?.rows;
  const years = training?.year_range;
  if (rows && Array.isArray(years) && years.length === 2) {
    return `${years[0]}-${years[1]}년 소방청 산악사고 ${Number(rows).toLocaleString()}건`;
  }
  return '2010-2024년 소방청 산악사고 112,902건';
});

export function resetLocalMlRisk() {
  localMlRisk.value = null;
}

export function loadLocalMlRiskIfNeeded(mountain) {
  const alreadyScored = [...recommendedMountains.value, ...alternativeMountains.value].find(
    (r) => r.id === mountain?.id,
  );
  if (alreadyScored) return;
  fetchMlRisk()
    .then((d) => { localMlRisk.value = d; })
    .catch(() => {});
}

function searchRank(mountain, normalizedSearch) {
  const name = (mountain.name || '').toLowerCase().replace(/\s/g, '');
  const region = (mountain.region || '').toLowerCase().replace(/\s/g, '');
  if (name === normalizedSearch) return 0;
  if (name.startsWith(normalizedSearch)) return 1;
  if (name.includes(normalizedSearch)) return 2;
  if (region.includes(normalizedSearch)) return 3;
  return 4;
}

export const mountainOptions = computed(() => {
  const buckets = new Map();
  for (const course of publicCourses.value) {
    const name = course.mountain || '산 정보 없음';
    if (!buckets.has(name)) buckets.set(name, { name, count: 0, lat: course.lat, lng: course.lng });
    const item = buckets.get(name);
    item.count += 1;
    if (!item.lat && course.lat) item.lat = course.lat;
    if (!item.lng && course.lng) item.lng = course.lng;
  }
  return [...buckets.values()]
    .filter((i) => i.name && i.name !== '산 정보 없음' && i.name !== '국립공원')
    .sort((a, b) => b.count - a.count)
    .slice(0, 40);
});

export const normalizedSelectedMountain = computed(() =>
  String(profile.mountainName || '').replace(/\s/g, '').toLowerCase(),
);

export const matchedRecommendations = computed(() =>
  recommendations.value.filter((c) => _isSelectedMountainCourse(c)),
);
export const strictMountainMatch = computed(() => matchedRecommendations.value.length > 0);
export const displayPrimaryCourses = computed(() =>
  (strictMountainMatch.value ? matchedRecommendations.value : recommendations.value).slice(0, 3),
);
export const nearbyAlternativeCourses = computed(() => {
  const seen = new Set(displayPrimaryCourses.value.map((c) => c.id));
  return [...recommendations.value, ...alternatives.value]
    .filter((c) => !seen.has(c.id) && !_isSelectedMountainCourse(c))
    .slice(0, 3);
});

function _isSelectedMountainCourse(course) {
  const target = normalizedSelectedMountain.value;
  if (!target) return false;
  const norm = (v) => String(v || '').replace(/\s/g, '').toLowerCase();
  return norm(course.mountain).includes(target) || norm(course.name).includes(target);
}

export async function loadCourses() {
  try {
    const data = await fetchCourses();
    publicCourses.value = data.courses?.length ? data.courses : fallbackCourses;
  } catch {
    publicCourses.value = fallbackCourses;
  }
}

export async function loadMountains() {
  try {
    const data = await fetchMountains();
    publicMountains.value = withFallbackMountainDescriptions(data.mountains?.length ? data.mountains : fallbackMountains);
  } catch {
    publicMountains.value = withFallbackMountainDescriptions(fallbackMountains);
  }
}

function withFallbackMountainDescriptions(mountains) {
  return (mountains || []).map((mountain) => {
    const fallbackIntro = fallbackMountainDescriptions[mountain.name];
    if (!fallbackIntro) return mountain;
    const currentIntro = mountain.intro || mountain.description || '';
    const looksGeneric = currentIntro.includes('위치 명산') || currentIntro.length < 35;
    if (!looksGeneric) return mountain;
    return {
      ...mountain,
      intro: fallbackIntro,
      description: fallbackIntro,
      description_source: 'seed_mountain_descriptions',
    };
  });
}

export async function submitMountainRecommendation() {
  loading.value = true;
  guideError.value = '';
  try {
    const weather = weatherData.value;
    const effectiveLocation = customStartLocation.value || location.value;
    const data = await fetchMountainRecommendations({
      profile,
      location: effectiveLocation,
      weather,
    });
    recommendedMountains.value = data.mountains || [];
    alternativeMountains.value = data.alternatives || [];
    resultState.value = recommendedMountains.value.length ? 'has_recommendations' : 'no_safe_course';
    agentSummary.value = _buildMountainSummary(recommendedMountains.value, profile);
    selectedMountain.value = recommendedMountains.value[0] || null;
  } catch (err) {
    const isNetwork = !navigator.onLine || err.message?.includes('fetch');
    guideError.value = isNetwork
      ? '네트워크에 연결되지 않았습니다. 인터넷 연결을 확인하고 다시 시도해 주세요.'
      : (err.message || '산 추천 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.');
  } finally {
    loading.value = false;
  }
}

function _buildMountainSummary(mountains, profile) {
  if (!mountains.length) return '현재 조건에 맞는 추천 산이 없습니다.';
  const top = mountains[0];
  return `${top.name}(${top.region.split(' ')[0]})이 가장 적합합니다. 해발 ${top.elevation_m}m, 소요시간 ${Math.floor(top.walk_time_min / 60)}~${Math.floor(top.walk_time_max / 60)}시간 코스입니다.`;
}

export async function loadWeather(overrideLat, overrideLng, mountainName) {
  const mountain = mountainOptions.value.find((m) => m.name === profile.mountainName);
  const lat = overrideLat ?? location.value?.lat ?? mountain?.lat ?? 37.5665;
  const lng = overrideLng ?? location.value?.lng ?? mountain?.lng ?? 126.978;
  try {
    const data = await fetchWeather({ lat, lng, mountain: mountainName || '' });
    weatherData.value = data;
  } catch {
    weatherData.value = {
      source: 'mock',
      lat,
      lng,
      mountain: mountainName || '',
      temperature_c: 24,
      wind_speed_ms: 2.4,
      rainfall_mm: 0,
      humidity_pct: 50,
      wildfire_risk: 'medium',
      pm10_ugm3: 13,
      pm25_ugm3: 8,
      grade_pm10: '보통',
      grade_pm25: '보통',
      sunrise: '05:12',
      sunset: '19:57',
    };
  }
}

export function syncLocationToMountain() {
  const selected = mountainOptions.value.find((i) => i.name === profile.mountainName);
  if (selected?.lat && selected?.lng) location.value = { lat: selected.lat, lng: selected.lng };
}

export async function submit() {
  loading.value = true;
  guideError.value = '';
  try {
    const [data, zonesData] = await Promise.all([
      fetchRecommendations({ profile, location: location.value }),
      fetchDisasterZones(profile.mountainName).catch(() => ({ zones: [] })),
    ]);
    recommendations.value = data.recommendations || [];
    alternatives.value = data.alternatives || [];
    resultState.value = data.result_state || 'has_recommendations';
    agentSummary.value = data.agent_summary || recommendations.value[0]?.agent_briefing || '';
    alternativeActions.value = data.alternative_actions || [];
    weatherData.value = data.weather || recommendations.value[0]?.weather || weatherData.value;
    disasterZones.value = zonesData.zones || [];
    selectedCourse.value = displayPrimaryCourses.value[0] || recommendations.value[0] || null;
  } catch (err) {
    guideError.value = err.message || '추천 데이터를 불러오지 못했습니다.';
  } finally {
    loading.value = false;
  }
}
