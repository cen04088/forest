import { computed, reactive, ref } from 'vue';
import { fetchCourses, fetchDisasterZones, fetchWeather, fetchRecommendations } from '../api.js';
import { useLocation } from './useLocation.js';
import { addDays, addMinutes, formatDateForInput, formatTimeForInput } from '../utils/dateHelpers.js';

// ── 싱글톤 상태 ─────────────────────────────────────────────────────────────
export const publicCourses = ref([]);
export const recommendations = ref([]);
export const alternatives = ref([]);
export const selectedCourse = ref(null);
export const weatherData = ref(null);
export const disasterZones = ref([]);
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
  companion: 'vulnerable',
  experience: 'beginner',
  condition: 4,
  intensity: 'moderate',
  purpose: 'balanced',
  transport: 'public',
  maxDistanceKm: 30,
});

export const { location, gpsStatus, gpsError, detectGPS } = useLocation();

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
    publicCourses.value = data.courses || [];
  } catch { publicCourses.value = []; }
}

export async function loadWeather() {
  const mountain = mountainOptions.value.find((m) => m.name === profile.mountainName);
  const lat = location.value?.lat ?? mountain?.lat ?? 37.5665;
  const lng = location.value?.lng ?? mountain?.lng ?? 126.978;
  try {
    weatherData.value = await fetchWeather({ lat, lng });
  } catch {}
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
