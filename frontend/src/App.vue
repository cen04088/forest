<template>
  <main class="app-shell">
    <!-- ─── 헤더 ──────────────────────────────────────────────────────── -->
    <header class="app-header">
      <div>
        <p class="eyebrow">스마트 안전 진단</p>
        <h1>ForestRx</h1>
        <p>어린이와 노약자도 함께 갈 수 있는 안전한 산행 코스를 추천합니다.</p>
      </div>
      <button class="icon-btn" type="button" title="새로고침" @click="loadEverything">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M21 12a9 9 0 0 1-15.5 6.2M3 12A9 9 0 0 1 18.5 5.8M18 3v4h-4M6 21v-4h4" />
        </svg>
      </button>
    </header>

    <!-- ─── 에러 배너 ──────────────────────────────────────────────────── -->
    <div v-if="error" class="error-banner" role="alert">
      <span>⚠️ {{ error }}</span>
      <button class="error-close" type="button" aria-label="닫기" @click="error = ''">✕</button>
    </div>

    <!-- ─── 탭바 ──────────────────────────────────────────────────────── -->
    <nav class="tabbar" aria-label="주요 화면">
      <button :class="{ active: activeTab === 'guide' }" type="button" @click="activeTab = 'guide'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>
        <span>안전코스</span>
      </button>
      <button :class="{ active: activeTab === 'safeLink' }" type="button" @click="activeTab = 'safeLink'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        <span>안전공유</span>
      </button>
      <button :class="{ active: activeTab === 'community' }" type="button" @click="activeTab = 'community'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
        <span>커뮤니티</span>
        <span class="tab-badge">준비중</span>
      </button>
      <button :class="{ active: activeTab === 'myPage' }" type="button" @click="activeTab = 'myPage'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        <span>내정보</span>
      </button>
    </nav>

    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- 안전코스 탭                                                         -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <section v-if="activeTab === 'guide'" class="screen-stack">

      <!-- 플래너 입력 폼 -->
      <section class="panel planner-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Safe Course</p>
            <h2>약자 동반 안전코스추천</h2>
          </div>
          <span class="mini-status">{{ loading ? '분석 중' : '준비됨' }}</span>
        </div>

        <form class="planner" @submit.prevent="submit">
          <!-- 산 선택 + GPS 버튼 -->
          <div class="field wide-field gps-field">
            <span>산 선택</span>
            <div class="gps-row">
              <select v-model="profile.mountainName" @change="handleMountainChange">
                <option v-for="mountain in mountainOptions" :key="mountain.name" :value="mountain.name">
                  {{ mountain.name }} · {{ mountain.count }}개 코스
                </option>
              </select>
              <button
                class="gps-btn"
                type="button"
                :class="gpsStatus"
                :disabled="gpsStatus === 'loading'"
                :title="gpsBtnTitle"
                @click="handleGPS"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
                  <path v-if="gpsStatus === 'loading'" d="M12 6a6 6 0 0 1 6 6" class="gps-spin" />
                </svg>
              </button>
            </div>
            <!-- GPS 결과 메시지 -->
            <p v-if="gpsStatus === 'success'" class="gps-message success">
              📍 현재 위치 감지 완료 — 가장 가까운 코스를 우선합니다
            </p>
            <p v-if="gpsStatus === 'error'" class="gps-message error">⚠️ {{ gpsError }}</p>
          </div>

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
          <button class="primary-btn wide-field" :class="{ loading }" type="submit" :disabled="loading">
            {{ loading ? '안전 등급 계산 중…' : '동반자 기준 안전코스 찾기' }}
          </button>
        </form>
      </section>

      <!-- 로딩 스켈레톤 -->
      <section v-if="loading" class="panel">
        <div class="skeleton-card">
          <div class="skeleton-line short"></div>
          <div class="skeleton-line full"></div>
          <div class="skeleton-line medium"></div>
        </div>
        <div class="skeleton-card">
          <div class="skeleton-line short"></div>
          <div class="skeleton-line full"></div>
          <div class="skeleton-line medium"></div>
        </div>
      </section>

      <!-- 비추천 공지 -->
      <article v-if="resultState === 'no_safe_course'" class="empty-state">
        <span class="safety-badge red">비추천</span>
        <h3>현재 조건에서 권장할 코스가 없습니다</h3>
        <p>{{ agentSummary }}</p>
        <div class="chip-row">
          <button v-for="action in alternativeActions" :key="action" type="button">{{ action }}</button>
        </div>
      </article>

      <!-- 추천 코스 목록 -->
      <section v-if="!loading && recommendations.length" class="panel">
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
          <CourseCard
            v-for="course in displayPrimaryCourses"
            :key="course.id"
            :course="course"
            :is-selected="selectedCourse?.id === course.id"
            @select="selectCourse"
          />
        </div>
      </section>

      <!-- 대체 코스 -->
      <section v-if="!loading && nearbyAlternativeCourses.length" class="panel subtle-panel">
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
          <span :class="['safety-badge', safetyClass(course)]">
            {{ course.safety_label || fallbackSafetyLabel(course) }}
          </span>
        </button>
      </section>

      <!-- 코스 상세 (지도 + 타임라인) -->
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
          <div class="legend">
            <span><i class="line green-line"></i>{{ selectedCourseRoutePoints.length >= 2 ? '등산로' : '위치' }}</span>
            <span><i class="line yellow-line"></i>주의</span>
          </div>
        </div>
        <div class="route-summary">
          <div>
            <strong>{{ selectedCourseRoutePoints.length >= 2 ? '지도 경로 표시' : '코스 단계 표시' }}</strong>
            <p>{{ routeDisplayMessage }}</p>
          </div>
          <span class="mini-status">
            {{ selectedCourseRoutePoints.length >= 2 ? `${selectedCourseRoutePoints.length}점` : `${courseTimelineItems.length}단계` }}
          </span>
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

    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- 안전공유 탭 (구 세이프링크)                                          -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <section v-else-if="activeTab === 'safeLink'" class="screen-stack">
      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Safe Link</p>
            <h2>보호자 공유카드</h2>
          </div>
        </div>

        <article class="safe-link-card">
          <div class="safe-link-map">
            <div ref="safeLinkMapEl" class="kakao-map" aria-label="보호자 공유 카카오 지도"></div>
          </div>
          <div class="safe-link-status">
            <span :class="['safety-badge', selectedCourse ? safetyClass(selectedCourse) : 'yellow']">
              {{ selectedCourse?.safety_label || '진단 대기' }}
            </span>
            <h3>{{ selectedCourse?.name || '안전 진단 후 공유 가능' }}</h3>
            <p>{{ safeLinkSummary }}</p>
          </div>
        </article>

        <!-- 현재 공유 상태 표시 (Mock UI) -->
        <div v-if="selectedCourse" class="safe-link-status-bar">
          <div class="status-dot" :class="selectedCourse.safety_decision === 'recommend' ? 'dot-green' : 'dot-yellow'"></div>
          <span>{{ selectedCourse.safe_link_preview?.status || '정상 이동' }}</span>
          <span class="status-time">마지막 확인: 방금 전</span>
        </div>
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
        <!-- 119 신고 CTA -->
        <a class="map-action emergency" href="tel:119">
          <strong>🚨 119 신고</strong>
          <span>산악 사고 발생 시 즉시 119에 신고하세요.</span>
        </a>
      </section>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- 커뮤니티 탭 (준비중)                                                -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <section v-else-if="activeTab === 'community'" class="screen-stack">
      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Community</p>
            <h2>동반 산행 커뮤니티</h2>
          </div>
          <span class="mini-status">후기 기반</span>
        </div>

        <!-- 준비중 배너 -->
        <div class="coming-soon-banner">
          <p class="coming-soon-icon">🏗️</p>
          <strong>커뮤니티 기능 준비 중</strong>
          <p>약자 동반 산행 후기, 현장 정보 공유 기능을 개발하고 있습니다.<br>아래는 서비스 오픈 시 제공될 샘플입니다.</p>
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
          <button class="outline-btn" type="button" disabled>후기 쓰기 (준비중)</button>
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

    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- 내정보 탭                                                           -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
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
            <label class="segment-btn"><input type="radio" v-model="profile.experience" value="beginner" name="exp" /><span>🌱 초보</span></label>
            <label class="segment-btn"><input type="radio" v-model="profile.experience" value="intermediate" name="exp" /><span>👟 보통</span></label>
            <label class="segment-btn"><input type="radio" v-model="profile.experience" value="advanced" name="exp" /><span>⛰️ 숙련</span></label>
          </div>
        </div>
        <div class="field">
          <span>컨디션</span>
          <div class="segment-group">
            <label class="segment-btn"><input type="radio" v-model.number="profile.condition" :value="2" name="cond" /><span>📉 낮음</span></label>
            <label class="segment-btn"><input type="radio" v-model.number="profile.condition" :value="3" name="cond" /><span>➖ 보통</span></label>
            <label class="segment-btn"><input type="radio" v-model.number="profile.condition" :value="4" name="cond" /><span>💪 좋음</span></label>
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
  </main>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue';
import { fetchCourses, fetchDataSources, fetchRecommendations } from './api';
import { useLocation } from './composables/useLocation.js';
import { useKakaoMap } from './composables/useKakaoMap.js';
import { safetyClass, fallbackSafetyLabel, durationLabel, daylightLabel, daylightColor } from './utils/courseHelpers.js';
import CourseCard from './components/CourseCard.vue';

// ─── 상태 ─────────────────────────────────────────────────────────────────
const activeTab = ref('guide');
const loading = ref(false);
const error = ref('');
const publicCourses = ref([]);
const dataSources = ref([]);
const recommendations = ref([]);
const alternatives = ref([]);
const selectedCourse = ref(null);
const resultState = ref('idle');
const agentSummary = ref('산과 출발 조건을 선택하면 실제 탐방로, 날씨, 일몰, 위험 데이터를 종합해 안전 등급을 계산합니다.');
const alternativeActions = ref([]);
const detailMapEl = ref(null);
const safeLinkMapEl = ref(null);
const shareStatus = ref('');

// ─── Composables ──────────────────────────────────────────────────────────
const { location, gpsStatus, gpsError, detectGPS } = useLocation();
const { mapStatus, safeLinkMapStatus, renderDetailMap, renderSafeLinkMap } = useKakaoMap();

// ─── 날짜/시간 초기값 ────────────────────────────────────────────────────
const initialDepartureAt = addMinutes(new Date(), 5);
const minDepartureDate = formatDateForInput(initialDepartureAt);
const maxDepartureDate = formatDateForInput(addDays(initialDepartureAt, 3));
const minDepartureTime = computed(() =>
  profile.departureDate === minDepartureDate ? formatTimeForInput(addMinutes(new Date(), 5)) : undefined,
);

// ─── 프로필 ───────────────────────────────────────────────────────────────
const profile = reactive({
  mountainName: '',
  departureDate: minDepartureDate,
  departureTime: formatTimeForInput(initialDepartureAt),
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

// ─── 정적 데이터 ──────────────────────────────────────────────────────────
const guardianChecklist = [
  '아이와 보호자 연락처를 서로 확인했어요',
  '물, 간식, 보조배터리를 챙겼어요',
  '입산 통제와 날씨 변화를 한 번 더 확인했어요',
  '해 지기 전에 내려오는 계획을 세웠어요',
];

const companionTypes = [
  { value: 'vulnerable', label: '어린이 또는 노약자 동반' },
  { value: 'child', label: '어린이 동반' },
  { value: 'senior', label: '노약자 동반' },
  { value: 'family', label: '가족 동반' },
  { value: 'solo', label: '혼자 산행' },
];

const activeCommunityFilter = ref('전체');

const rawCommunityPosts = [
  { author: '초코아빠', time: '2시간 전', likes: 12, title: '초등학생과 90분 코스로 다녀왔어요', body: '초입 화장실 이후에는 쉼터 간격이 길어 물을 미리 챙기는 편이 좋았습니다.', tag: '어린이', color: 'green' },
  { author: '산좋아', time: '5시간 전', likes: 8, title: '부모님과 갈 때 계단 구간은 우회가 좋아요', body: '초반 경사는 완만하지만 중간 데크 계단이 길어 쉬는 시간을 넉넉히 잡았습니다.', tag: '노약자', color: 'yellow' },
  { author: '비오는날', time: '하루 전', likes: 24, title: '비 온 다음날은 흙길보다 포장 접근로 추천', body: '미끄러운 구간이 있어 유모차나 보행 보조가 필요한 동반자는 대체 코스가 안전했습니다.', tag: '주의', color: 'yellow' },
];

const filteredCommunityPosts = computed(() => {
  if (activeCommunityFilter.value === '전체') return rawCommunityPosts;
  return rawCommunityPosts.filter((post) => post.tag === activeCommunityFilter.value);
});

// ─── GPS 버튼 ─────────────────────────────────────────────────────────────
const gpsBtnTitle = computed(() => {
  if (gpsStatus.value === 'loading') return '위치 감지 중...';
  if (gpsStatus.value === 'success') return '위치 감지 완료';
  if (gpsStatus.value === 'error') return '위치 감지 실패 — 다시 시도';
  return '내 위치 자동 감지';
});

async function handleGPS() {
  const success = await detectGPS();
  if (success) {
    syncLocationToSelectedMountain();
    await submit();
  }
}

// ─── 라이프사이클 ─────────────────────────────────────────────────────────
onMounted(() => { loadEverything(); });

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
  } catch { dataSources.value = []; }
}

async function loadCourses() {
  try {
    const data = await fetchCourses();
    publicCourses.value = data.courses || [];
  } catch { publicCourses.value = []; }
}

async function submit() {
  loading.value = true;
  error.value = '';
  try {
    const data = await fetchRecommendations({ profile, location: location.value });
    recommendations.value = data.recommendations || [];
    alternatives.value = data.alternatives || [];
    resultState.value = data.result_state || 'has_recommendations';
    agentSummary.value = data.agent_summary || recommendations.value[0]?.agent_briefing || '';
    alternativeActions.value = data.alternative_actions || [];
    selectedCourse.value = displayPrimaryCourses.value[0] || recommendations.value[0] || null;
    renderMaps();
  } catch (err) {
    error.value = err.message || '추천 데이터를 불러오지 못했습니다.';
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
  shareStatus.value = '';
  renderMaps();
}

// ─── 감시자 ───────────────────────────────────────────────────────────────
watch([selectedCourse, activeTab], () => { renderMaps(); });
watch(() => [profile.departureDate, profile.departureTime], () => { ensureFutureDepartureTime(); });

// ─── 계산 속성 ────────────────────────────────────────────────────────────
const mountainOptions = computed(() => {
  const buckets = new Map();
  for (const course of publicCourses.value) {
    const name = course.mountain || '산 정보 없음';
    if (!buckets.has(name)) {
      buckets.set(name, { name, count: 0, lat: course.lat, lng: course.lng, region: course.region });
    }
    const item = buckets.get(name);
    item.count += 1;
    if (!item.lat && course.lat) item.lat = course.lat;
    if (!item.lng && course.lng) item.lng = course.lng;
  }
  return [...buckets.values()]
    .filter((item) => item.name && item.name !== '산 정보 없음')
    .filter((item) => item.name !== '국립공원')
    .sort((a, b) => b.count - a.count)
    .slice(0, 40);
});

const selectedMountainName = computed(() => profile.mountainName || mountainOptions.value[0]?.name || '');
const normalizedSelectedMountain = computed(() => normalizeText(selectedMountainName.value));
const matchedRecommendations = computed(() =>
  recommendations.value.filter((course) => isSelectedMountainCourse(course)),
);
const strictMountainMatch = computed(() => matchedRecommendations.value.length > 0);
const displayPrimaryCourses = computed(() =>
  (strictMountainMatch.value ? matchedRecommendations.value : recommendations.value).slice(0, 3),
);
const nearbyAlternativeCourses = computed(() => {
  const seen = new Set(displayPrimaryCourses.value.map((c) => c.id));
  return [...recommendations.value, ...alternatives.value]
    .filter((c) => !seen.has(c.id))
    .filter((c) => !isSelectedMountainCourse(c))
    .slice(0, 3);
});

const selectedCourseLat = computed(() => Number(selectedCourse.value?.lat));
const selectedCourseLng = computed(() => Number(selectedCourse.value?.lng));
const hasSelectedCourseLocation = computed(
  () => Number.isFinite(selectedCourseLat.value) && Number.isFinite(selectedCourseLng.value),
);
const selectedCourseRoutePoints = computed(() =>
  (selectedCourse.value?.route_geometry || []).filter(
    (p) => Number.isFinite(Number(p.lat)) && Number.isFinite(Number(p.lng)),
  ),
);
const routeDisplayMessage = computed(() => {
  if (!selectedCourse.value) return '코스를 선택하면 표시 방식이 정해집니다.';
  if (selectedCourseRoutePoints.value.length >= 2) return '이 코스는 실제 선형 좌표가 있어 지도에 등산로 라인을 표시합니다.';
  return '이 코스는 공공 데이터에 정확한 선형 좌표가 없어 출발·경유·도착 단계로 표시합니다.';
});
const courseTimelineItems = computed(() => {
  const highlights = selectedCourse.value?.highlights || [];
  const parsed = highlights.map(parseTimelineHighlight).filter(Boolean);
  if (parsed.length) return parsed;
  if (!selectedCourse.value) return [];
  return [{ label: '코스', value: selectedCourse.value.name }];
});
const kakaoMapUrl = computed(() => {
  if (!hasSelectedCourseLocation.value) return '';
  return `https://map.kakao.com/link/map/${encodeURIComponent(selectedCourse.value.name)},${selectedCourseLat.value},${selectedCourseLng.value}`;
});
const kakaoNavigateUrl = computed(() => {
  if (!hasSelectedCourseLocation.value) return '';
  return `https://map.kakao.com/link/to/${encodeURIComponent(selectedCourse.value.name)},${selectedCourseLat.value},${selectedCourseLng.value}`;
});
const safeLinkSummary = computed(() => {
  if (!selectedCourse.value) return '안전 진단 후 보호자에게 보낼 공유 카드가 생성됩니다.';
  return `${selectedCourse.value.mountain} ${selectedCourse.value.name} 코스의 안전 등급과 카카오 지도 위치를 보호자에게 공유합니다.`;
});
const myProfileStatus = computed(() => {
  const companion = companionTypes.find((t) => t.value === profile.companion)?.label || '동반자';
  return companion.replace(' 동반', '');
});
const safeLinkMessage = computed(() => {
  if (!selectedCourse.value) return '안전 진단 후 공유 메시지가 생성됩니다.';
  const course = selectedCourse.value;
  const riskFactors = (course.risk_factors || []).slice(0, 2).join(', ') || '특이 위험 요인 없음';
  const locationLine = hasSelectedCourseLocation.value
    ? `카카오맵 위치: ${kakaoMapUrl.value}`
    : '카카오맵 위치: 좌표 정보 없음';
  return [
    '[ForestRx 안전공유]',
    `산/코스: ${course.mountain} · ${course.name}`,
    `안전 등급: ${course.safety_label || fallbackSafetyLabel(course)}`,
    `예상 산행: 약 ${durationLabel(course.duration_min)} / 거리 ${course.distance_km}km`,
    `하산 여유: ${daylightLabel(course.daylight_margin_min)}`,
    `주의 요인: ${riskFactors}`,
    locationLine,
    '현장 통제, 기상 변화, 입산 제한 여부를 함께 확인해 주세요.',
  ].join('\n');
});

// ─── 지도 렌더링 ──────────────────────────────────────────────────────────
async function renderMaps() {
  await nextTick();
  if (activeTab.value === 'guide') {
    renderDetailMap(detailMapEl.value, selectedCourse.value, selectedCourseRoutePoints.value);
  }
  if (activeTab.value === 'safeLink') {
    renderSafeLinkMap(safeLinkMapEl.value, selectedCourse.value, selectedCourseRoutePoints.value);
  }
}

// ─── 공유 기능 ────────────────────────────────────────────────────────────
async function copySafeLinkMessage() {
  if (!selectedCourse.value) return;
  try {
    await navigator.clipboard.writeText(safeLinkMessage.value);
    shareStatus.value = '보호자 공유 문구를 복사했습니다.';
  } catch {
    shareStatus.value = '브라우저에서 복사를 허용하지 않았습니다. 문구를 직접 선택해 복사해 주세요.';
  }
}

async function shareSafeLink() {
  if (!selectedCourse.value) return;
  const sharePayload = {
    title: 'ForestRx 안전공유',
    text: safeLinkMessage.value,
    url: hasSelectedCourseLocation.value ? kakaoMapUrl.value : window.location.href,
  };
  if (navigator.share) {
    try {
      await navigator.share(sharePayload);
      shareStatus.value = '보호자 공유 창을 열었습니다.';
      return;
    } catch (err) {
      if (err?.name === 'AbortError') { shareStatus.value = '공유를 취소했습니다.'; return; }
    }
  }
  await copySafeLinkMessage();
  if (hasSelectedCourseLocation.value) window.open(kakaoMapUrl.value, '_blank', 'noreferrer');
}

// ─── 유틸 함수 ────────────────────────────────────────────────────────────
function isSelectedMountainCourse(course) {
  const target = normalizedSelectedMountain.value;
  if (!target) return false;
  return normalizeText(course.mountain).includes(target) || normalizeText(course.name).includes(target);
}

function normalizeText(value) { return String(value || '').replace(/\s/g, '').toLowerCase(); }

function parseTimelineHighlight(item) {
  const text = String(item || '').trim();
  if (!text) return null;
  const [label, ...rest] = text.split(':');
  if (rest.length) return { label: label.trim(), value: rest.join(':').trim() };
  return { label: '정보', value: text };
}

function addDays(date, days) { const d = new Date(date); d.setDate(d.getDate() + days); return d; }
function addMinutes(date, minutes) { const d = new Date(date); d.setMinutes(d.getMinutes() + minutes); return d; }
function formatDateForInput(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}
function formatTimeForInput(date) {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}
</script>
