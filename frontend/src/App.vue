<template>
  <main class="app-shell">
    <header class="app-header">
      <div>
        <p class="eyebrow">AI Forest Safety</p>
        <h1>ForestRx</h1>
        <p>실제 탐방로 데이터 기반 안전 등급 산행 가이드</p>
      </div>
      <button class="icon-btn" type="button" title="새로고침" @click="loadEverything">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M21 12a9 9 0 0 1-15.5 6.2M3 12A9 9 0 0 1 18.5 5.8M18 3v4h-4M6 21v-4h4" />
        </svg>
      </button>
    </header>

    <section class="hero-map" aria-label="안전 등급 지도 미리보기">
      <div class="hero-map-grid"></div>
      <svg viewBox="0 0 420 220" aria-hidden="true">
        <path class="hero-route route-green" d="M34 162 C88 126 120 72 178 88 C230 102 250 142 326 108" />
        <path class="hero-route route-yellow" d="M178 88 C214 96 238 118 250 142" />
        <circle class="hero-zone" cx="250" cy="142" r="34" />
        <circle class="hero-pin" cx="214" cy="111" r="9" />
      </svg>
      <div class="hero-copy">
        <span :class="['safety-badge', heroBadgeClass]">{{ heroBadgeLabel }}</span>
        <strong>{{ selectedMountainName || "실제 산 선택" }}</strong>
        <span>{{ selectedMountainSummary }}</span>
      </div>
    </section>

    <nav class="tabbar">
      <button :class="{ active: activeTab === 'guide' }" type="button" @click="activeTab = 'guide'">안전 추천</button>
      <button :class="{ active: activeTab === 'safeLink' }" type="button" @click="activeTab = 'safeLink'">Safe Link</button>
      <button :class="{ active: activeTab === 'admin' }" type="button" @click="activeTab = 'admin'">관리</button>
      <button :class="{ active: activeTab === 'data' }" type="button" @click="activeTab = 'data'">데이터</button>
    </nav>

    <section v-if="activeTab === 'guide'" class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Step 1</p>
          <h2>오늘의 안전 산행 진단</h2>
        </div>
        <span class="mini-status">{{ publicCourses.length.toLocaleString() }}개 코스</span>
      </div>

      <form class="planner" @submit.prevent="submit">
        <label>
          산 선택
          <select v-model="profile.mountainName" @change="handleMountainChange">
            <option v-for="mountain in mountainOptions" :key="mountain.name" :value="mountain.name">
              {{ mountain.name }} · {{ mountain.count }}개 코스
            </option>
          </select>
        </label>
        <label>
          출발 일자
          <input v-model="profile.departureDate" type="date" :min="minDepartureDate" :max="maxDepartureDate" />
        </label>
        <label>
          출발 시간
          <input v-model="profile.departureTime" type="time" />
        </label>
        <label>
          이동 가능 시간
          <select v-model.number="profile.availableMinutes">
            <option :value="60">1시간</option>
            <option :value="120">2시간</option>
            <option :value="180">3시간</option>
            <option :value="240">4시간</option>
          </select>
        </label>
        <label>
          등산 소요 시간
          <select v-model.number="profile.desiredHikingMinutes">
            <option :value="60">1시간</option>
            <option :value="120">2시간</option>
            <option :value="180">3시간</option>
            <option :value="240">4시간</option>
          </select>
        </label>
        <button class="primary-btn wide" type="submit" :disabled="loading">
          {{ loading ? "안전 등급 계산 중" : "실제 코스로 안전 진단" }}
        </button>
      </form>

      <article v-if="resultState === 'no_safe_course'" class="empty-state">
        <span class="safety-badge red">비추천</span>
        <h3>현재 조건에서 안전한 코스가 없습니다</h3>
        <p>{{ agentSummary }}</p>
        <div class="chip-row">
          <button v-for="action in alternativeActions" :key="action" type="button">{{ action }}</button>
        </div>
      </article>

      <article v-else-if="recommendations.length" class="agent-brief">
        <div class="agent-mark">AI</div>
        <div>
          <p class="eyebrow">ForestRx 안전 에이전트</p>
          <strong>{{ agentSummary }}</strong>
        </div>
      </article>

      <section v-if="recommendations.length" class="course-list">
        <article
          v-for="course in recommendations"
          :key="course.id"
          :class="['course-card', selectedCourse?.id === course.id ? 'selected' : '']"
          @click="selectCourse(course)"
        >
          <div class="course-card-head">
            <span :class="['safety-badge', safetyClass(course)]">{{ course.safety_label || fallbackSafetyLabel(course) }}</span>
            <span class="vulnerable-copy">{{ course.safe_for_vulnerable ? "취약자 적합" : "취약자 주의" }}</span>
          </div>
          <h3>{{ course.name }}</h3>
          <p>{{ course.mountain }} · {{ course.distance_km }}km · 약 {{ durationLabel(course.duration_min) }}</p>
          <div class="risk-tags">
            <span v-for="factor in (course.risk_factors || []).slice(0, 3)" :key="factor">{{ factor }}</span>
          </div>
        </article>
      </section>

      <section v-if="selectedCourse" class="detail-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Course Detail</p>
            <h2>{{ selectedCourse.name }}</h2>
          </div>
          <button class="outline-btn" type="button" @click="activeTab = 'safeLink'">Safe Link</button>
        </div>
        <div class="detail-map">
          <div ref="detailMapEl" class="kakao-map" aria-label="선택 코스 카카오 지도"></div>
          <p v-if="mapStatus" class="map-status">{{ mapStatus }}</p>
          <div class="legend">
            <span><i class="line green-line"></i>안전</span>
            <span><i class="line yellow-line"></i>주의</span>
            <span><i class="line red-line"></i>위험 마커</span>
          </div>
        </div>
        <div class="decision-grid">
          <span><strong>하산 여유</strong>{{ daylightLabel(selectedCourse.daylight_margin_min) }}</span>
          <span><strong>우회 필요</strong>{{ selectedCourse.safety_decision === "recommend" ? "낮음" : "권장" }}</span>
          <span><strong>접근 거리</strong>{{ selectedCourse.distance_from_user_km ?? "-" }}km</span>
        </div>
        <p class="detail-copy">{{ selectedCourse.agent_briefing }}</p>
      </section>
    </section>

    <section v-else-if="activeTab === 'safeLink'" class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Step 2</p>
          <h2>실시간 세이프 링크</h2>
        </div>
        <span class="mini-status">SDK 내장형 데모</span>
      </div>

      <article class="safe-link-map">
        <div ref="safeLinkMapEl" class="kakao-map" aria-label="세이프 링크 카카오 지도"></div>
        <p v-if="safeLinkMapStatus" class="map-status">{{ safeLinkMapStatus }}</p>
        <div class="safe-link-status">
          <span :class="['safety-badge', selectedCourse ? safetyClass(selectedCourse) : 'yellow']">
            {{ selectedCourse?.safe_link_preview?.status || "주의 모니터링" }}
          </span>
          <strong>FRX-2941</strong>
          <p>마지막 위치 동기화: 방금 전</p>
        </div>
      </article>

      <div class="safe-card-grid">
        <article>
          <p class="eyebrow">동의 상태</p>
          <strong>공유 활성화</strong>
          <span>사용자 동의 기반 GPS 동기화</span>
        </article>
        <article>
          <p class="eyebrow">위험 구역</p>
          <strong>{{ selectedCourse?.risk_factors?.length || 0 }}건</strong>
          <span>주의 알림 기준</span>
        </article>
      </div>

      <article class="alert-item">
        <span class="safety-badge yellow">주의</span>
        <div>
          <strong>보행 주의 구간 접근 중</strong>
          <p>{{ selectedCourse?.risk_factors?.[0] || "전일 강수와 암반 구간으로 미끄럼 주의가 필요합니다." }}</p>
        </div>
      </article>
    </section>

    <section v-else-if="activeTab === 'admin'" class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">B2G Demo</p>
          <h2>위험 Hotspot 대시보드</h2>
        </div>
        <span class="mini-status">Mock + API</span>
      </div>

      <div class="admin-map">
        <span class="hotspot red" style="left: 68%; top: 32%">급경사</span>
        <span class="hotspot yellow" style="left: 42%; top: 56%">암반</span>
        <span class="hotspot green" style="left: 22%; top: 68%">안전</span>
      </div>

      <article v-for="spot in hotspots" :key="spot.name" class="hotspot-row">
        <span :class="['dot', spot.color]"></span>
        <div>
          <strong>{{ spot.name }}</strong>
          <p>{{ spot.reason }}</p>
        </div>
        <button type="button">{{ spot.action }}</button>
      </article>
    </section>

    <section v-else class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Data Sources</p>
          <h2>데이터 연결 상태</h2>
        </div>
        <span class="mini-status">{{ readySourceCount }}개 준비</span>
      </div>
      <article v-for="source in dataSources" :key="source.id" class="source-row">
        <span :class="['dot', isReadySource(source) ? 'green' : 'yellow']"></span>
        <div>
          <strong>{{ source.name }}</strong>
          <p>{{ source.status }} · {{ source.endpoint }}</p>
        </div>
      </article>
    </section>

    <p v-if="error" class="error-toast">{{ error }}</p>
  </main>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { fetchCourses, fetchDataSources, fetchRecommendations } from "./api";

const activeTab = ref("guide");
const loading = ref(false);
const error = ref("");
const publicCourses = ref([]);
const dataSources = ref([]);
const recommendations = ref([]);
const selectedCourse = ref(null);
const resultState = ref("idle");
const agentSummary = ref("실제 탐방로, 기상, 일몰 데이터를 결합해 안전 등급을 계산합니다.");
const alternativeActions = ref([]);
const location = ref({ lat: 37.5665, lng: 126.978 });
const detailMapEl = ref(null);
const safeLinkMapEl = ref(null);
const mapStatus = ref("");
const safeLinkMapStatus = ref("");
let kakaoMapLoadPromise = null;
const minDepartureDate = formatDateForInput(new Date());
const maxDepartureDate = formatDateForInput(addDays(new Date(), 3));

const profile = reactive({
  mountainName: "",
  departureDate: minDepartureDate,
  departureTime: "09:20",
  availableMinutes: 240,
  desiredHikingMinutes: 120,
  companion: "vulnerable",
  experience: "beginner",
  condition: 4,
  intensity: "moderate",
  purpose: "balanced",
  transport: "public",
  maxDistanceKm: 30,
});

const hotspots = [
  { name: "관악산 암반 사면", color: "red", reason: "전일 강수 + 급경사 + 보행 주의 알림 집중", action: "점검" },
  { name: "둘레길 계단 구간", color: "yellow", reason: "노년층 동반 산행 주의 알림 증가", action: "안내" },
  { name: "능선 바람 노출부", color: "yellow", reason: "풍속 5m/s 이상 예보 시 주의 전환", action: "관찰" },
];

onMounted(() => {
  loadEverything();
});

async function loadEverything() {
  await Promise.all([loadSources(), loadCourses()]);
  if (!profile.mountainName && mountainOptions.value.length) {
    profile.mountainName = mountainOptions.value[0].name;
  }
  syncLocationToSelectedMountain();
  await submit();
}

async function loadSources() {
  try {
    const data = await fetchDataSources();
    dataSources.value = data.connected_sources || [];
  } catch {
    dataSources.value = [];
  }
}

async function loadCourses() {
  try {
    const data = await fetchCourses();
    publicCourses.value = data.courses || [];
  } catch {
    publicCourses.value = [];
  }
}

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    const data = await fetchRecommendations({ profile, location: location.value });
    recommendations.value = data.recommendations || [];
    resultState.value = data.result_state || "has_recommendations";
    agentSummary.value = data.agent_summary || recommendations.value[0]?.agent_briefing || "";
    alternativeActions.value = data.alternative_actions || [];
    selectedCourse.value = recommendations.value[0] || null;
    renderMaps();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

function handleMountainChange() {
  syncLocationToSelectedMountain();
  submit();
}

function syncLocationToSelectedMountain() {
  const selected = mountainOptions.value.find((item) => item.name === profile.mountainName);
  if (selected?.lat && selected?.lng) {
    location.value = { lat: selected.lat, lng: selected.lng };
  }
}

function selectCourse(course) {
  selectedCourse.value = course;
}

watch([selectedCourse, activeTab], () => {
  renderMaps();
});

const mountainOptions = computed(() => {
  const buckets = new Map();
  for (const course of publicCourses.value) {
    const name = course.mountain || "산 정보 없음";
    if (!buckets.has(name)) {
      buckets.set(name, {
        name,
        count: 0,
        lat: course.lat,
        lng: course.lng,
        region: course.region,
      });
    }
    const item = buckets.get(name);
    item.count += 1;
    if (!item.lat && course.lat) item.lat = course.lat;
    if (!item.lng && course.lng) item.lng = course.lng;
  }
  return [...buckets.values()]
    .filter((item) => item.name && item.name !== "산 정보 없음")
    .filter((item) => item.name !== "국립공원")
    .sort((a, b) => b.count - a.count)
    .slice(0, 40);
});

const selectedMountainName = computed(() => profile.mountainName || mountainOptions.value[0]?.name || "");

const selectedMountainSummary = computed(() => {
  const selected = mountainOptions.value.find((item) => item.name === profile.mountainName);
  if (!selected) return "실제 탐방로 데이터 연결 중";
  return `실제 코스 ${selected.count}개 후보 분석`;
});

const heroBadgeLabel = computed(() => selectedCourse.value?.safety_label || "진단 중");
const heroBadgeClass = computed(() => (selectedCourse.value ? safetyClass(selectedCourse.value) : "yellow"));
const readySourceCount = computed(() => dataSources.value.filter(isReadySource).length);

function isReadySource(source) {
  return ["ready", "connected"].includes(source.status);
}

function durationLabel(minutes) {
  const value = Number(minutes || 0);
  const hours = Math.floor(value / 60);
  const mins = value % 60;
  if (!hours) return `${mins}분`;
  if (!mins) return `${hours}시간`;
  return `${hours}시간 ${mins}분`;
}

function safetyClass(course) {
  return {
    recommend: "green",
    caution: "yellow",
    not_recommended: "red",
  }[course.safety_decision] || "green";
}

function fallbackSafetyLabel(course) {
  return { safe: "추천", caution: "주의", danger: "비추천" }[course.safety_grade] || "추천";
}

function addDays(date, days) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function formatDateForInput(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function daylightLabel(minutes) {
  if (minutes === null || minutes === undefined) return "확인 중";
  if (minutes < 30) return "부족";
  if (minutes < 60) return "짧음";
  return "충분";
}

async function renderMaps() {
  await nextTick();
  if (activeTab.value === "guide") {
    renderDetailMap();
  }
  if (activeTab.value === "safeLink") {
    renderSafeLinkMap();
  }
}

async function renderDetailMap() {
  if (!detailMapEl.value) return;
  if (!selectedCourse.value?.lat || !selectedCourse.value?.lng) {
    mapStatus.value = "이 코스는 지도 좌표가 없어 다른 추천 코스를 선택해 주세요.";
    return;
  }
  mapStatus.value = "카카오 지도를 불러오는 중입니다.";
  try {
    const kakao = await loadKakaoMapSdk();
    const center = new kakao.maps.LatLng(selectedCourse.value.lat, selectedCourse.value.lng);
    const map = new kakao.maps.Map(detailMapEl.value, { center, level: 5 });
    new kakao.maps.Marker({ map, position: center, title: selectedCourse.value.name });
    const routePath = kakaoRoutePath(kakao, selectedCourse.value);
    if (routePath.length >= 2) {
      new kakao.maps.Polyline({
        map,
        path: routePath,
        strokeWeight: 6,
        strokeColor: selectedCourse.value.safety_decision === "not_recommended" ? "#cf3528" : "#23864b",
        strokeOpacity: 0.9,
        strokeStyle: selectedCourse.value.safety_decision === "recommend" ? "solid" : "shortdash",
      });
      const bounds = new kakao.maps.LatLngBounds();
      routePath.forEach((point) => bounds.extend(point));
      map.setBounds(bounds);
    }
    new kakao.maps.Circle({
      map,
      center,
      radius: 180,
      strokeWeight: 2,
      strokeColor: "#d29a12",
      strokeOpacity: 0.9,
      strokeStyle: "dashed",
      fillColor: "#d29a12",
      fillOpacity: 0.18,
    });
    mapStatus.value = "";
  } catch (err) {
    console.error("Kakao map detail render failed", err);
    mapStatus.value = "카카오 지도를 표시하려면 JavaScript 키와 도메인 등록이 필요합니다.";
  }
}

async function renderSafeLinkMap() {
  if (!safeLinkMapEl.value) return;
  if (!selectedCourse.value?.lat || !selectedCourse.value?.lng) {
    safeLinkMapStatus.value = "이 코스는 지도 좌표가 없어 위치 공유 지도를 표시할 수 없습니다.";
    return;
  }
  safeLinkMapStatus.value = "카카오 지도를 불러오는 중입니다.";
  try {
    const kakao = await loadKakaoMapSdk();
    const courseLat = selectedCourse.value.lat;
    const courseLng = selectedCourse.value.lng;
    const start = new kakao.maps.LatLng(courseLat - 0.004, courseLng - 0.004);
    const current = new kakao.maps.LatLng(courseLat, courseLng);
    const next = new kakao.maps.LatLng(courseLat + 0.003, courseLng + 0.004);
    const map = new kakao.maps.Map(safeLinkMapEl.value, { center: current, level: 5 });
    new kakao.maps.Marker({ map, position: current, title: "공유 대상 현재 위치" });
    const routePath = kakaoRoutePath(kakao, selectedCourse.value);
    new kakao.maps.Polyline({
      map,
      path: routePath.length >= 2 ? routePath : [start, current, next],
      strokeWeight: 5,
      strokeColor: "#23864b",
      strokeOpacity: 0.9,
      strokeStyle: "solid",
    });
    if (routePath.length >= 2) {
      const bounds = new kakao.maps.LatLngBounds();
      routePath.forEach((point) => bounds.extend(point));
      map.setBounds(bounds);
    }
    new kakao.maps.Circle({
      map,
      center: next,
      radius: 160,
      strokeWeight: 2,
      strokeColor: "#cf3528",
      strokeOpacity: 0.9,
      strokeStyle: "dashed",
      fillColor: "#cf3528",
      fillOpacity: 0.16,
    });
    safeLinkMapStatus.value = "";
  } catch (err) {
    console.error("Kakao map Safe Link render failed", err);
    safeLinkMapStatus.value = "카카오 지도를 표시하려면 JavaScript 키와 도메인 등록이 필요합니다.";
  }
}

function loadKakaoMapSdk() {
  if (window.kakao?.maps) {
    return new Promise((resolve) => window.kakao.maps.load(() => resolve(window.kakao)));
  }
  if (kakaoMapLoadPromise) return kakaoMapLoadPromise;

  const appKey = import.meta.env.VITE_KAKAO_MAP_APP_KEY;
  kakaoMapLoadPromise = new Promise((resolve, reject) => {
    if (!appKey) {
      reject(new Error("Missing Kakao map app key"));
      return;
    }
    const script = document.createElement("script");
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&autoload=false`;
    script.async = true;
    script.onload = () => {
      if (!window.kakao?.maps) {
        reject(new Error("Kakao SDK loaded but maps namespace is missing"));
        return;
      }
      window.kakao.maps.load(() => resolve(window.kakao));
    };
    script.onerror = () => reject(new Error("Failed to load Kakao Maps SDK script"));
    document.head.appendChild(script);
  });
  return kakaoMapLoadPromise;
}

function kakaoRoutePath(kakao, course) {
  return (course?.route_geometry || [])
    .filter((point) => Number.isFinite(Number(point.lat)) && Number.isFinite(Number(point.lng)))
    .map((point) => new kakao.maps.LatLng(Number(point.lat), Number(point.lng)));
}
</script>
