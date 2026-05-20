<template>
  <main class="app-shell">
    <header class="app-header">
      <div>
        <p class="eyebrow">AI Forest Safety</p>
        <h1>ForestRx</h1>
        <p>어린이와 노약자도 함께 갈 수 있는 안전한 산행 코스를 추천합니다.</p>
      </div>
      <button class="icon-btn" type="button" title="새로고침" @click="loadEverything">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M21 12a9 9 0 0 1-15.5 6.2M3 12A9 9 0 0 1 18.5 5.8M18 3v4h-4M6 21v-4h4" />
        </svg>
      </button>
    </header>



    <nav class="tabbar" aria-label="주요 화면">
      <button :class="{ active: activeTab === 'guide' }" type="button" @click="activeTab = 'guide'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>
        <span>안전코스</span>
      </button>
      <button :class="{ active: activeTab === 'safeLink' }" type="button" @click="activeTab = 'safeLink'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        <span>세이프링크</span>
      </button>
      <button :class="{ active: activeTab === 'community' }" type="button" @click="activeTab = 'community'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
        <span>커뮤니티</span>
      </button>
      <button :class="{ active: activeTab === 'myPage' }" type="button" @click="activeTab = 'myPage'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        <span>내정보</span>
      </button>
    </nav>

    <section v-if="activeTab === 'guide'" class="screen-stack">
      <section class="panel planner-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Safe Course</p>
            <h2>약자 동반 안전코스추천</h2>
          </div>
          <span class="mini-status">{{ loading ? "분석 중" : "준비됨" }}</span>
        </div>

        <form class="planner" @submit.prevent="submit">
          <label class="field wide-field">
            <span>산 선택</span>
            <select v-model="profile.mountainName" @change="handleMountainChange">
              <option v-for="mountain in mountainOptions" :key="mountain.name" :value="mountain.name">
                {{ mountain.name }} · {{ mountain.count }}개 코스
              </option>
            </select>
          </label>
          <label class="field">
            <span>출발 일자</span>
            <input v-model="profile.departureDate" type="date" :min="minDepartureDate" :max="maxDepartureDate" />
          </label>
        <label class="field">
          <span>출발 시간</span>
          <input v-model="profile.departureTime" type="time" :min="minDepartureTime" @change="ensureFutureDepartureTime" />
        </label>
          <label class="field">
            <span>희망 산행 시간</span>
            <select v-model.number="profile.desiredHikingMinutes">
              <option :value="60">1시간</option>
              <option :value="120">2시간</option>
              <option :value="180">3시간</option>
              <option :value="240">4시간</option>
            </select>
          </label>
          <button class="primary-btn wide-field" type="submit" :disabled="loading">
            {{ loading ? "안전 등급 계산 중" : "동반자 기준 안전코스 찾기" }}
          </button>
        </form>
      </section>

      <article v-if="resultState === 'no_safe_course'" class="empty-state">
        <span class="safety-badge red">비추천</span>
        <h3>현재 조건에서 권장할 코스가 없습니다</h3>
        <p>{{ agentSummary }}</p>
        <div class="chip-row">
          <button v-for="action in alternativeActions" :key="action" type="button">{{ action }}</button>
        </div>
      </article>

      <section v-if="recommendations.length" class="panel">
        <div class="section-title compact">
          <div>
            <p class="eyebrow">Recommended</p>
            <h2>추천 코스</h2>
          </div>
          <span class="mini-status">{{ displayPrimaryCourses.length }}개</span>
        </div>
        <p v-if="!strictMountainMatch" class="notice">
          선택한 산과 정확히 일치하는 후보가 부족해 주변 안전 후보를 함께 보여줍니다.
        </p>
        <div class="course-list">
          <article
            v-for="course in displayPrimaryCourses"
            :key="course.id"
            :class="['course-card', selectedCourse?.id === course.id ? 'selected' : '']"
            @click="selectCourse(course)"
            role="button"
            tabindex="0"
            @keydown.enter="selectCourse(course)"
            @keydown.space.prevent="selectCourse(course)"
          >
            <div class="course-meta">
              <span :class="['safety-badge', safetyClass(course)]">{{ course.safety_label || fallbackSafetyLabel(course) }}</span>
              <span>{{ course.safe_for_vulnerable ? "취약자 동반 가능" : "취약자 주의" }}</span>
            </div>
            <h3>{{ course.name }}</h3>
            <p>{{ course.mountain }} · {{ course.distance_km }}km · 약 {{ durationLabel(course.duration_min) }}</p>
            <div class="metric-row-compact">
              <span title="하산 여유">⏱️ {{ daylightLabel(course.daylight_margin_min) }}</span>
              <span title="접근 거리">📍 {{ course.distance_from_user_km ?? "-" }}km</span>
              <span title="데이터 출처">ℹ️ {{ course.sourceLabel || sourceLabel(course) }}</span>
            </div>
            <div class="risk-tags">
              <span v-for="factor in (course.risk_factors || []).slice(0, 3)" :key="factor">{{ factor }}</span>
              <span v-if="!(course.risk_factors || []).length">위험 요인 확인 중</span>
            </div>
          </article>
        </div>
      </section>

      <section v-if="nearbyAlternativeCourses.length" class="panel subtle-panel">
        <div class="section-title compact">
          <div>
            <p class="eyebrow">Alternative</p>
            <h2>주변 대체 코스</h2>
          </div>
          <span class="mini-status">{{ nearbyAlternativeCourses.length }}개</span>
        </div>
        <button
          v-for="course in nearbyAlternativeCourses"
          :key="course.id"
          class="alternative-row"
          type="button"
          @click="selectCourse(course)"
        >
          <span>
            <strong>{{ course.name }}</strong>
            <small>{{ course.mountain }} · {{ course.distance_km }}km · {{ durationLabel(course.duration_min) }}</small>
          </span>
          <span :class="['safety-badge', safetyClass(course)]">{{ course.safety_label || fallbackSafetyLabel(course) }}</span>
        </button>
      </section>

      <section v-if="selectedCourse" class="panel detail-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Course Detail</p>
            <h2>{{ selectedCourse.name }}</h2>
          </div>
          <button class="outline-btn" type="button" @click="activeTab = 'safeLink'">공유 카드</button>
        </div>
        <div class="detail-map">
          <div ref="detailMapEl" class="kakao-map" aria-label="선택 코스 카카오 지도"></div>
          <p v-if="mapStatus" class="map-status">{{ mapStatus }}</p>
          <div class="legend">
            <span><i class="line green-line"></i>{{ selectedCourseRoutePoints.length >= 2 ? "등산로" : "위치" }}</span>
            <span><i class="line yellow-line"></i>주의</span>
          </div>
        </div>
        <div class="route-summary">
          <div>
            <strong>{{ selectedCourseRoutePoints.length >= 2 ? "지도 경로 표시" : "코스 단계 표시" }}</strong>
            <p>{{ routeDisplayMessage }}</p>
          </div>
          <span class="mini-status">{{ selectedCourseRoutePoints.length >= 2 ? `${selectedCourseRoutePoints.length}점` : `${courseTimelineItems.length}단계` }}</span>
        </div>
        <ol class="route-timeline" aria-label="코스 진행 단계">
          <li v-for="item in courseTimelineItems" :key="item.label + item.value">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </li>
        </ol>
        <p class="detail-copy">{{ selectedCourse.agent_briefing }}</p>
      </section>
    </section>

    <section v-else-if="activeTab === 'safeLink'" class="screen-stack">
      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Safe Link</p>
            <h2>보호자 안전 공유</h2>
          </div>
        </div>

        <article class="safe-link-card">
          <div class="safe-link-map">
            <div ref="safeLinkMapEl" class="kakao-map" aria-label="세이프링크 카카오 지도"></div>
            <p v-if="safeLinkMapStatus" class="map-status">{{ safeLinkMapStatus }}</p>
          </div>
          <div class="safe-link-status">
            <span :class="['safety-badge', selectedCourse ? safetyClass(selectedCourse) : 'yellow']">
              {{ selectedCourse?.safety_label || "진단 대기" }}
            </span>
            <h3>{{ selectedCourse?.name || "안전 진단 후 공유 가능" }}</h3>
            <p>{{ safeLinkSummary }}</p>
          </div>
        </article>
      </section>

      <section class="panel share-panel">
        <textarea class="share-message" :value="safeLinkMessage" readonly aria-label="보호자 공유 메시지"></textarea>
        <div class="share-actions">
          <button class="primary-btn" type="button" :disabled="!selectedCourse" @click="shareSafeLink">
            보호자에게 공유
          </button>
          <button class="outline-btn" type="button" :disabled="!selectedCourse" @click="copySafeLinkMessage">
            문구 복사
          </button>
        </div>
        <p v-if="shareStatus" class="share-status">{{ shareStatus }}</p>
      </section>

      <section class="panel kakao-actions">
        <a :class="['map-action', !selectedCourse ? 'disabled' : '']" :href="selectedCourse ? kakaoMapUrl : undefined" target="_blank" rel="noreferrer">
          <strong>카카오맵에서 위치 보기</strong>
          <span>보호자가 코스 위치를 바로 확인합니다.</span>
        </a>
        <a :class="['map-action', !selectedCourse ? 'disabled' : '']" :href="selectedCourse ? kakaoNavigateUrl : undefined" target="_blank" rel="noreferrer">
          <strong>카카오맵 길찾기 열기</strong>
          <span>현재 위치 기준 경로 확인은 카카오맵에서 처리합니다.</span>
        </a>
      </section>
    </section>

    <section v-else-if="activeTab === 'community'" class="screen-stack">
      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Community</p>
            <h2>동반 산행 커뮤니티</h2>
          </div>
          <span class="mini-status">후기 기반</span>
        </div>

        <div class="community-hero">
          <p>약자 동반 산행 후기</p>
          <h3>아이, 부모님과 다녀온 안전 정보를 함께 모아요</h3>
          <span>화장실, 쉼터, 계단, 급경사처럼 실제 동반자가 체감한 정보를 코스 추천에 보태는 공간입니다.</span>
        </div>
      </section>

      <section class="panel community-feed">
        <div class="section-title compact">
          <div>
            <p class="eyebrow">Reviews</p>
            <h2>최근 동반 산행 후기</h2>
          </div>
          <button class="outline-btn" type="button">후기 쓰기</button>
        </div>

        <div class="filter-row">
          <button :class="{ active: activeCommunityFilter === '전체' }" @click="activeCommunityFilter = '전체'">전체</button>
          <button :class="{ active: activeCommunityFilter === '어린이' }" @click="activeCommunityFilter = '어린이'">🧒 어린이</button>
          <button :class="{ active: activeCommunityFilter === '노약자' }" @click="activeCommunityFilter = '노약자'">🧓 노약자</button>
          <button :class="{ active: activeCommunityFilter === '주의' }" @click="activeCommunityFilter = '주의'">⚠️ 주의</button>
        </div>

        <article v-for="post in filteredCommunityPosts" :key="post.title" class="community-post-modern">
          <div class="post-header">
            <div class="post-avatar">{{ post.author[0] }}</div>
            <div class="post-meta">
              <strong>{{ post.author }}</strong>
              <span>{{ post.time }} · <span :class="['safety-text', post.color]">{{ post.tag }}</span></span>
            </div>
          </div>
          <div class="post-content">
            <strong>{{ post.title }}</strong>
            <p>{{ post.body }}</p>
          </div>
          <div class="post-actions">
            <button class="like-btn" type="button">👍 유용해요 {{ post.likes }}</button>
          </div>
        </article>
      </section>
    </section>

    <section v-else class="screen-stack">
      <section class="panel profile-settings">
        <div class="section-title">
          <div>
            <p class="eyebrow">My Info</p>
            <h2>내정보</h2>
          </div>
          <span class="mini-status">{{ myProfileStatus }}</span>
        </div>
        <div class="field">
          <span>동반 유형</span>
          <div class="segment-group wrap">
            <label v-for="type in companionTypes" :key="type.value" class="segment-btn">
              <input type="radio" v-model="profile.companion" :value="type.value" name="companion" />
              <span>{{ type.label }}</span>
            </label>
          </div>
        </div>
        <div class="field">
          <span>산행 경험</span>
          <div class="segment-group">
            <label class="segment-btn">
              <input type="radio" v-model="profile.experience" value="beginner" name="exp" />
              <span>🌱 초보</span>
            </label>
            <label class="segment-btn">
              <input type="radio" v-model="profile.experience" value="intermediate" name="exp" />
              <span>👟 보통</span>
            </label>
            <label class="segment-btn">
              <input type="radio" v-model="profile.experience" value="advanced" name="exp" />
              <span>⛰️ 숙련</span>
            </label>
          </div>
        </div>
        <div class="field">
          <span>컨디션</span>
          <div class="segment-group">
            <label class="segment-btn">
              <input type="radio" v-model.number="profile.condition" :value="2" name="cond" />
              <span>📉 낮음</span>
            </label>
            <label class="segment-btn">
              <input type="radio" v-model.number="profile.condition" :value="3" name="cond" />
              <span>➖ 보통</span>
            </label>
            <label class="segment-btn">
              <input type="radio" v-model.number="profile.condition" :value="4" name="cond" />
              <span>💪 좋음</span>
            </label>
          </div>
        </div>
      </section>

      <section class="panel guardian-checklist">
        <div class="section-title compact">
          <div>
            <p class="eyebrow">Checklist</p>
            <h2>출발 전 체크리스트</h2>
          </div>
          <span class="mini-status">내 저장</span>
        </div>
        <label v-for="item in guardianChecklist" :key="item" class="custom-check-item">
          <input type="checkbox" class="hidden-check" />
          <span class="check-box"></span>
          <span>{{ item }}</span>
        </label>
      </section>

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
const alternatives = ref([]);
const selectedCourse = ref(null);
const resultState = ref("idle");
const agentSummary = ref("산과 출발 조건을 선택하면 실제 탐방로, 날씨, 일몰, 위험 데이터를 종합해 안전 등급을 계산합니다.");
const alternativeActions = ref([]);
const location = ref({ lat: 37.5665, lng: 126.978 });
const detailMapEl = ref(null);
const safeLinkMapEl = ref(null);
const mapStatus = ref("");
const safeLinkMapStatus = ref("");
const shareStatus = ref("");
let kakaoMapLoadPromise = null;
const initialDepartureAt = addMinutes(new Date(), 5);
const minDepartureDate = formatDateForInput(initialDepartureAt);
const maxDepartureDate = formatDateForInput(addDays(initialDepartureAt, 3));
const minDepartureTime = computed(() => (profile.departureDate === minDepartureDate ? formatTimeForInput(addMinutes(new Date(), 5)) : undefined));

const profile = reactive({
  mountainName: "",
  departureDate: minDepartureDate,
  departureTime: formatTimeForInput(initialDepartureAt),
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

const guardianChecklist = [
  "아이와 보호자 연락처를 서로 확인했어요",
  "물, 간식, 보조배터리를 챙겼어요",
  "입산 통제와 날씨 변화를 한 번 더 확인했어요",
  "해 지기 전에 내려오는 계획을 세웠어요",
];

const companionTypes = [
  { value: "vulnerable", label: "어린이 또는 노약자 동반" },
  { value: "child", label: "어린이 동반" },
  { value: "senior", label: "노약자 동반" },
  { value: "family", label: "가족 동반" },
  { value: "solo", label: "혼자 산행" },
];

const activeCommunityFilter = ref('전체');

const rawCommunityPosts = [
  {
    author: "초코아빠",
    time: "2시간 전",
    likes: 12,
    title: "초등학생과 90분 코스로 다녀왔어요",
    body: "초입 화장실 이후에는 쉼터 간격이 길어 물을 미리 챙기는 편이 좋았습니다.",
    tag: "어린이",
    color: "green",
  },
  {
    author: "산좋아",
    time: "5시간 전",
    likes: 8,
    title: "부모님과 갈 때 계단 구간은 우회가 좋아요",
    body: "초반 경사는 완만하지만 중간 데크 계단이 길어 쉬는 시간을 넉넉히 잡았습니다.",
    tag: "노약자",
    color: "yellow",
  },
  {
    author: "비오는날",
    time: "하루 전",
    likes: 24,
    title: "비 온 다음날은 흙길보다 포장 접근로 추천",
    body: "미끄러운 구간이 있어 유모차나 보행 보조가 필요한 동반자는 대체 코스가 안전했습니다.",
    tag: "주의",
    color: "yellow",
  },
];

const filteredCommunityPosts = computed(() => {
  if (activeCommunityFilter.value === '전체') return rawCommunityPosts;
  return rawCommunityPosts.filter(post => post.tag === activeCommunityFilter.value);
});

const communitySignals = [
  { color: "green", title: "편의시설", body: "화장실, 쉼터, 음수대, 주차장 접근성을 후기에서 모읍니다." },
  { color: "yellow", title: "약자 체감 난이도", body: "공식 난이도와 별개로 아이와 노약자가 힘들어한 구간을 기록합니다." },
  { color: "yellow", title: "현장 변수", body: "공사, 통제, 미끄럼, 벌레, 그늘 부족처럼 당일 체감 정보를 공유합니다." },
];

const defaultMountainPhoto = {
  label: "한국 산행",
  url: "https://commons.wikimedia.org/wiki/Special:FilePath/Korea-Seoraksan-01.jpg",
};

const mountainPhotos = {
  관악산: { label: "관악산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Gwanaksan%20Seoul%20KR.jpg" },
  북한산: { label: "북한산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Bukhansan%20Mountain.jpg" },
  도봉산: { label: "도봉산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/DoBongSan%20%28Mt.%20DoBongSan%29%20in%20Spring.jpg" },
  인왕산: { label: "인왕산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Korea-Seoul-Inwangsan-28.jpg" },
  아차산: { label: "아차산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Forts%20in%20Achasan%20mountain.jpg" },
  청계산: { label: "청계산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Cheonggyesan.jpg" },
  수락산: { label: "수락산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Suraksan.JPG" },
  남산: { label: "남산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Seoul%20from%20Namsan.jpg" },
  설악산: { label: "설악산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Korea-Seoraksan-01.jpg" },
  지리산: { label: "지리산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Korea-Mountain-Jirisan-15.jpg" },
  한라산: { label: "한라산", url: "https://commons.wikimedia.org/wiki/Special:FilePath/Hallasan%20Above.jpg" },
};

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
    alternatives.value = data.alternatives || [];
    resultState.value = data.result_state || "has_recommendations";
    agentSummary.value = data.agent_summary || recommendations.value[0]?.agent_briefing || "";
    alternativeActions.value = data.alternative_actions || [];
    selectedCourse.value = displayPrimaryCourses.value[0] || recommendations.value[0] || null;
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

function ensureFutureDepartureTime() {
  if (profile.departureDate !== minDepartureDate) return;
  const minimum = minDepartureTime.value;
  if (minimum && (!profile.departureTime || profile.departureTime < minimum)) {
    profile.departureTime = minimum;
  }
}

function syncLocationToSelectedMountain() {
  const selected = mountainOptions.value.find((item) => item.name === profile.mountainName);
  if (selected?.lat && selected?.lng) {
    location.value = { lat: selected.lat, lng: selected.lng };
  }
}

function selectCourse(course) {
  selectedCourse.value = course;
  shareStatus.value = "";
  renderMaps();
}

watch([selectedCourse, activeTab], () => {
  renderMaps();
});

watch(
  () => [profile.departureDate, profile.departureTime],
  () => {
    ensureFutureDepartureTime();
  },
);

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
  return `실제 코스 ${selected.count}개를 기준으로 위험 요인을 분석합니다.`;
});

const normalizedSelectedMountain = computed(() => normalizeText(selectedMountainName.value));
const matchedRecommendations = computed(() =>
  recommendations.value.filter((course) => isSelectedMountainCourse(course)),
);
const strictMountainMatch = computed(() => matchedRecommendations.value.length > 0);
const displayPrimaryCourses = computed(() =>
  (strictMountainMatch.value ? matchedRecommendations.value : recommendations.value).slice(0, 3),
);
const nearbyAlternativeCourses = computed(() => {
  const seen = new Set(displayPrimaryCourses.value.map((course) => course.id));
  return [...recommendations.value, ...alternatives.value]
    .filter((course) => !seen.has(course.id))
    .filter((course) => !isSelectedMountainCourse(course))
    .slice(0, 3);
});

const routeScopeLabel = computed(() => (strictMountainMatch.value ? "선택 산" : "주변"));
const heroBadgeLabel = computed(() => selectedCourse.value?.safety_label || "진단 중");
const heroBadgeClass = computed(() => (selectedCourse.value ? safetyClass(selectedCourse.value) : "yellow"));
const heroPhotoStyle = computed(() => backgroundImageStyle(mountainPhotoFor(selectedMountainName.value).url));
const readySourceCount = computed(() => dataSources.value.filter(isReadySource).length);
const selectedCourseLat = computed(() => Number(selectedCourse.value?.lat));
const selectedCourseLng = computed(() => Number(selectedCourse.value?.lng));
const hasSelectedCourseLocation = computed(() => Number.isFinite(selectedCourseLat.value) && Number.isFinite(selectedCourseLng.value));
const selectedCourseRoutePoints = computed(() =>
  (selectedCourse.value?.route_geometry || []).filter((point) => Number.isFinite(Number(point.lat)) && Number.isFinite(Number(point.lng))),
);
const routeDisplayMessage = computed(() => {
  if (!selectedCourse.value) return "코스를 선택하면 표시 방식이 정해집니다.";
  if (selectedCourseRoutePoints.value.length >= 2) return "이 코스는 실제 선형 좌표가 있어 지도에 등산로 라인을 표시합니다.";
  return "이 코스는 공공 데이터에 정확한 선형 좌표가 없어 출발·경유·도착 단계로 표시합니다.";
});
const courseTimelineItems = computed(() => {
  const highlights = selectedCourse.value?.highlights || [];
  const parsed = highlights.map(parseTimelineHighlight).filter(Boolean);
  if (parsed.length) return parsed;
  if (!selectedCourse.value) return [];
  return [{ label: "코스", value: selectedCourse.value.name }];
});
const kakaoMapUrl = computed(() => {
  if (!hasSelectedCourseLocation.value) return "";
  return `https://map.kakao.com/link/map/${encodeURIComponent(selectedCourse.value.name)},${selectedCourseLat.value},${selectedCourseLng.value}`;
});
const kakaoNavigateUrl = computed(() => {
  if (!hasSelectedCourseLocation.value) return "";
  return `https://map.kakao.com/link/to/${encodeURIComponent(selectedCourse.value.name)},${selectedCourseLat.value},${selectedCourseLng.value}`;
});
const safeLinkSummary = computed(() => {
  if (!selectedCourse.value) return "안전 진단 후 보호자에게 보낼 공유 카드가 생성됩니다.";
  return `${selectedCourse.value.mountain} ${selectedCourse.value.name} 코스의 안전 등급과 카카오 지도 위치를 보호자에게 공유합니다.`;
});
const myProfileSummary = computed(() => {
  const companion = companionTypes.find((type) => type.value === profile.companion)?.label || "동반자 기준";
  const experience = { beginner: "초보", intermediate: "보통", advanced: "숙련" }[profile.experience] || "초보";
  return `${companion} · ${experience} · 최대 ${durationLabel(profile.availableMinutes)} 산행을 기준으로 추천합니다.`;
});
const myProfileStatus = computed(() => {
  const companion = companionTypes.find((type) => type.value === profile.companion)?.label || "동반자";
  return companion.replace(" 동반", "");
});
const safeLinkMessage = computed(() => {
  if (!selectedCourse.value) return "안전 진단 후 공유 메시지가 생성됩니다.";
  const course = selectedCourse.value;
  const riskFactors = (course.risk_factors || []).slice(0, 2).join(", ") || "특이 위험 요인 없음";
  const locationLine = hasSelectedCourseLocation.value ? `카카오맵 위치: ${kakaoMapUrl.value}` : "카카오맵 위치: 좌표 정보 없음";
  return [
    "[ForestRx 세이프링크]",
    `산/코스: ${course.mountain} · ${course.name}`,
    `안전 등급: ${course.safety_label || fallbackSafetyLabel(course)}`,
    `예상 산행: 약 ${durationLabel(course.duration_min)} / 거리 ${course.distance_km}km`,
    `하산 여유: ${daylightLabel(course.daylight_margin_min)}`,
    `주의 요인: ${riskFactors}`,
    locationLine,
    "현장 통제, 기상 변화, 입산 제한 여부를 함께 확인해 주세요.",
  ].join("\n");
});
const guardianSummary = computed(() => {
  if (!selectedCourse.value) return "안전진단을 실행하면 보호자가 확인할 상태가 표시됩니다.";
  return `${selectedCourse.value.safety_label || fallbackSafetyLabel(selectedCourse.value)} 등급입니다. 하산 여유는 ${daylightLabel(selectedCourse.value.daylight_margin_min)}이며, 보호자는 카카오맵 위치와 주의 요인을 확인할 수 있습니다.`;
});
const guardianAlerts = computed(() => {
  const course = selectedCourse.value;
  if (!course) {
    return [
      { color: "yellow", title: "안전진단 대기", body: "산과 출발 시간을 선택하고 안전진단을 먼저 실행해 주세요." },
    ];
  }

  const alerts = [
    {
      color: course.safety_decision === "recommend" ? "green" : "yellow",
      title: "현재 코스 상태",
      body: course.agent_briefing || "현재 조건을 기준으로 안전 상태를 계산했습니다.",
    },
    {
      color: daylightColor(course.daylight_margin_min),
      title: "하산 시간",
      body: `일몰 전 하산 여유는 ${daylightLabel(course.daylight_margin_min)}입니다.`,
    },
  ];

  for (const factor of (course.risk_factors || []).slice(0, 2)) {
    alerts.push({ color: "yellow", title: "주의 요인", body: factor });
  }

  if (!hasSelectedCourseLocation.value) {
    alerts.push({ color: "yellow", title: "위치 공유 제한", body: "이 코스는 지도 좌표가 없어 카카오맵 위치 공유가 제한됩니다." });
  }

  return alerts;
});
const safetyEvidenceItems = computed(() => {
  const course = selectedCourse.value;
  if (!course) {
    return [
      { color: "yellow", title: "안전진단 전", body: "코스를 선택하면 날씨, 일몰, 접근 거리, 위험 데이터를 종합해 판단합니다." },
    ];
  }

  return [
    { color: safetyDotColor(course), title: "코스 안전 등급", body: `${course.safety_label || fallbackSafetyLabel(course)} 등급으로 판단했습니다.` },
    { color: daylightColor(course.daylight_margin_min), title: "하산 여유", body: `현재 출발 시간 기준 하산 여유는 ${daylightLabel(course.daylight_margin_min)}입니다.` },
    { color: "green", title: "코스 거리", body: `${course.distance_km}km, 약 ${durationLabel(course.duration_min)} 산행으로 계산했습니다.` },
    { color: course.distance_from_user_km === null || course.distance_from_user_km === undefined ? "yellow" : "green", title: "접근 거리", body: `기준 위치에서 약 ${course.distance_from_user_km ?? "-"}km 떨어져 있습니다.` },
    { color: (course.risk_factors || []).length ? "yellow" : "green", title: "주의 요인", body: (course.risk_factors || []).slice(0, 2).join(", ") || "특이 위험 요인이 크게 표시되지 않았습니다." },
    { color: "green", title: "데이터 출처", body: sourceLabel(course) },
  ];
});

function isReadySource(source) {
  return ["ready", "connected"].includes(source.status);
}

function isSelectedMountainCourse(course) {
  const target = normalizedSelectedMountain.value;
  if (!target) return false;
  return normalizeText(course.mountain).includes(target) || normalizeText(course.name).includes(target);
}

function normalizeText(value) {
  return String(value || "").replace(/\s/g, "").toLowerCase();
}

function parseTimelineHighlight(item) {
  const text = String(item || "").trim();
  if (!text) return null;
  const [label, ...rest] = text.split(":");
  if (rest.length) return { label: label.trim(), value: rest.join(":").trim() };
  return { label: "정보", value: text };
}

function mountainPhotoFor(mountainName) {
  const normalized = normalizeText(mountainName);
  const entry = Object.entries(mountainPhotos).find(([name]) => normalized.includes(normalizeText(name)));
  return entry?.[1] || defaultMountainPhoto;
}

function backgroundImageStyle(url) {
  return { "--mountain-photo": `url("${url}")` };
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

function safetyDotColor(course) {
  return {
    recommend: "green",
    caution: "yellow",
    not_recommended: "red",
  }[course?.safety_decision] || "green";
}

function daylightColor(minutes) {
  if (minutes === null || minutes === undefined) return "yellow";
  if (minutes < 30) return "red";
  if (minutes < 60) return "yellow";
  return "green";
}

function sourceLabel(course) {
  const source = String(course.source || "");
  if (source.includes("SHP")) return "로컬 SHP";
  if (source.includes("국립공원")) return "국립공원";
  if (source.includes("VWorld")) return "VWorld";
  return "공공 데이터";
}

async function copySafeLinkMessage() {
  if (!selectedCourse.value) return;
  try {
    await navigator.clipboard.writeText(safeLinkMessage.value);
    shareStatus.value = "보호자 공유 문구를 복사했습니다.";
  } catch {
    shareStatus.value = "브라우저에서 복사를 허용하지 않았습니다. 문구를 직접 선택해 복사해 주세요.";
  }
}

async function shareSafeLink() {
  if (!selectedCourse.value) return;
  const sharePayload = {
    title: "ForestRx 세이프링크",
    text: safeLinkMessage.value,
    url: hasSelectedCourseLocation.value ? kakaoMapUrl.value : window.location.href,
  };

  if (navigator.share) {
    try {
      await navigator.share(sharePayload);
      shareStatus.value = "보호자 공유 창을 열었습니다.";
      return;
    } catch (err) {
      if (err?.name === "AbortError") {
        shareStatus.value = "공유를 취소했습니다.";
        return;
      }
    }
  }

  await copySafeLinkMessage();
  if (hasSelectedCourseLocation.value) {
    window.open(kakaoMapUrl.value, "_blank", "noreferrer");
  }
}

function addDays(date, days) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function addMinutes(date, minutes) {
  const next = new Date(date);
  next.setMinutes(next.getMinutes() + minutes);
  return next;
}

function formatDateForInput(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatTimeForInput(date) {
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${hours}:${minutes}`;
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
    renderCourseFallbackMap(detailMapEl.value, selectedCourse.value, { safeLink: false });
    mapStatus.value = "지도 좌표가 부족해 코스 단계로 표시합니다.";
    return;
  }
  if (selectedCourseRoutePoints.value.length < 2) {
    renderCourseFallbackMap(detailMapEl.value, selectedCourse.value, { safeLink: false });
    mapStatus.value = "정확한 등산로 선형이 없어 JavaScript 코스 프리뷰로 표시합니다.";
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
      mapStatus.value = "";
    } else {
      mapStatus.value = "정확한 등산로 선형이 없어 중심 위치만 표시합니다.";
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
  } catch (err) {
    console.error("Kakao map detail render failed", err);
    renderCourseFallbackMap(detailMapEl.value, selectedCourse.value, { safeLink: false });
    mapStatus.value = "카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.";
  }
}

async function renderSafeLinkMap() {
  if (!safeLinkMapEl.value) return;
  if (!selectedCourse.value?.lat || !selectedCourse.value?.lng) {
    renderCourseFallbackMap(safeLinkMapEl.value, selectedCourse.value, { safeLink: true });
    safeLinkMapStatus.value = "선택된 코스의 지도 좌표가 부족합니다.";
    return;
  }
  if (selectedCourseRoutePoints.value.length < 2) {
    renderCourseFallbackMap(safeLinkMapEl.value, selectedCourse.value, { safeLink: true });
    safeLinkMapStatus.value = "정확한 등산로 선형이 없어 JavaScript 코스 프리뷰로 표시합니다.";
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
    renderCourseFallbackMap(safeLinkMapEl.value, selectedCourse.value, { safeLink: true });
    safeLinkMapStatus.value = "카카오 JavaScript SDK 연결 전까지 대체 지도로 표시합니다.";
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
    const timeout = window.setTimeout(() => reject(new Error("Kakao Maps SDK load timeout")), 7000);
    const script = document.createElement("script");
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${appKey}&autoload=false`;
    script.async = true;
    script.onload = () => {
      if (!window.kakao?.maps) {
        window.clearTimeout(timeout);
        reject(new Error("Kakao SDK loaded but maps namespace is missing"));
        return;
      }
      window.kakao.maps.load(() => {
        window.clearTimeout(timeout);
        resolve(window.kakao);
      });
    };
    script.onerror = () => {
      window.clearTimeout(timeout);
      reject(new Error("Failed to load Kakao Maps SDK script"));
    };
    document.head.appendChild(script);
  });
  return kakaoMapLoadPromise;
}

function kakaoRoutePath(kakao, course) {
  return (course?.route_geometry || [])
    .filter((point) => Number.isFinite(Number(point.lat)) && Number.isFinite(Number(point.lng)))
    .map((point) => new kakao.maps.LatLng(Number(point.lat), Number(point.lng)));
}

function renderCourseFallbackMap(container, course, { safeLink = false } = {}) {
  if (!container) return;
  const timeline = (course?.highlights || []).map(parseTimelineHighlight).filter(Boolean).slice(0, 3);
  const routePoints = normalizeSvgRoutePoints(course?.route_geometry || []);
  const routePath = routePoints.length >= 2 ? routePoints.map((point, index) => `${index ? "L" : "M"} ${point.x} ${point.y}`).join(" ") : "M 36 118 C 92 58, 166 166, 254 74";
  const startLabel = timeline[0]?.value || course?.name || "출발";
  const endLabel = timeline.find((item) => item.label.includes("도착"))?.value || timeline.at(-1)?.value || "도착";
  const start = routePoints[0] || { x: 36, y: 118 };
  const end = routePoints.at(-1) || { x: 254, y: 74 };
  const mid = routePoints[Math.floor(routePoints.length / 2)] || { x: 150, y: 100 };
  const hasGeometry = routePoints.length >= 2;

  container.innerHTML = `
    <div class="fallback-map ${hasGeometry ? "has-geometry" : "estimated"}">
      <svg viewBox="0 0 290 180" aria-hidden="true">
        <defs>
          <linearGradient id="routeGradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#11a361" />
            <stop offset="100%" stop-color="#2563eb" />
          </linearGradient>
        </defs>
        <path class="fallback-terrain ridge-a" d="M-10 138 C 36 88, 66 112, 104 74 C 142 36, 178 80, 214 52 C 244 30, 270 46, 304 18" />
        <path class="fallback-terrain ridge-b" d="M-8 162 C 44 126, 82 146, 126 110 C 170 74, 206 118, 296 70" />
        <path class="fallback-contour" d="M28 42 C 82 58, 120 24, 168 48 C 214 70, 242 52, 270 38 M24 86 C 70 104, 104 76, 152 94 C 196 110, 234 92, 268 104 M28 136 C 82 126, 124 154, 178 130 C 214 114, 242 132, 270 122" />
        <path class="fallback-grid" d="M20 40 H270 M20 90 H270 M20 140 H270 M70 20 V160 M145 20 V160 M220 20 V160" />
        <path class="fallback-route-shadow" d="${routePath}" />
        <path class="fallback-route" d="${routePath}" />
        <circle class="fallback-pulse" cx="${mid.x}" cy="${mid.y}" r="18" />
        <circle class="fallback-node" cx="${start.x}" cy="${start.y}" r="7" />
        <circle class="fallback-node end" cx="${end.x}" cy="${end.y}" r="7" />
      </svg>
      <div class="fallback-pin start" style="left:${start.x / 2.9}%; top:${start.y / 1.8}%">출발</div>
      <div class="fallback-pin end" style="left:${end.x / 2.9}%; top:${end.y / 1.8}%">도착</div>
      <div class="fallback-map-copy">
        <span>${hasGeometry ? "Coordinate Image" : "Estimated Route Image"}</span>
        <strong>${escapeHtml(course?.name || "코스 정보")}</strong>
        <p>${escapeHtml(startLabel)} → ${escapeHtml(endLabel)}</p>
        <em>${escapeHtml(course?.distance_km ?? "-")}km · ${safeLink ? "보호자 공유용" : "입력 좌표 기반"}</em>
      </div>
    </div>
  `;
}

function normalizeSvgRoutePoints(points) {
  const valid = points
    .filter((point) => Number.isFinite(Number(point.lat)) && Number.isFinite(Number(point.lng)))
    .slice(0, 24);
  if (valid.length < 2) return [];
  const lats = valid.map((point) => Number(point.lat));
  const lngs = valid.map((point) => Number(point.lng));
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const latSpan = maxLat - minLat || 1;
  const lngSpan = maxLng - minLng || 1;
  return valid.map((point) => ({
    x: 28 + ((Number(point.lng) - minLng) / lngSpan) * 234,
    y: 152 - ((Number(point.lat) - minLat) / latSpan) * 124,
  }));
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
</script>
