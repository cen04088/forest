<template>
  <nav class="tabbar shared-sidebar" aria-label="주요 화면">
    <button class="sidebar-brand" type="button" aria-label="Ola 홈으로 이동" @click="goHome">
      <span class="sidebar-logo-text">Ola</span>
      <span class="sidebar-logo-leaf" aria-hidden="true">
        <svg viewBox="0 0 24 24" focusable="false">
          <path d="M20.8 3.2C13.7 3.7 7.6 7.6 5.2 14.4c-.4 1.2.7 2.4 1.9 2.1 6.7-1.8 11-6.6 13.7-13.3Z" />
          <path d="M5.8 15.5c3.8-2.9 7.7-5.2 12-7.1" />
        </svg>
      </span>
    </button>

    <router-link to="/guide" class="tabbar-item" active-class="active">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>
      <span>안전코스</span>
    </router-link>

    <router-link to="/chat" class="tabbar-item" active-class="active">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
      <span>AI 도우미</span>
    </router-link>

    <router-link to="/safe-link" class="tabbar-item" active-class="active">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
      <span>안전공유</span>
    </router-link>

    <router-link to="/community" class="tabbar-item" active-class="active">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
      <span>커뮤니티</span>
    </router-link>

    <router-link
      v-if="authUser"
      to="/my-page"
      class="tabbar-item"
      active-class="active"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      <span>마이페이지</span>
    </router-link>

    <router-link
      v-else
      to="/login"
      class="tabbar-item"
      active-class="active"
      @click="openLogin"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      <span>로그인</span>
    </router-link>

    <section class="sidebar-search-panel" aria-label="산 검색하기">
      <div class="sidebar-search-head">
        <h2>산 검색하기</h2>
      </div>

      <label class="bfp-search-row sidebar-search-row">
        <svg class="bfp-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input
          v-model="mountainSearch"
          class="bfp-search-input"
          type="text"
          placeholder="산 이름 또는 지역 검색"
          autocomplete="off"
        />
      </label>

      <div class="sidebar-filter-row" aria-label="난이도 필터">
        <button
          v-for="filter in difficultyFilters"
          :key="filter.value"
          type="button"
          class="sidebar-filter-chip"
          :class="{ active: sidebarDifficultyFilter === filter.value }"
          @click="sidebarDifficultyFilter = filter.value"
        >
          <i :style="{ background: filter.color }"></i>
          <span>{{ filter.label }}</span>
        </button>
      </div>

      <div v-if="loading && !sidebarMountains.length" class="community-loading sidebar-search-loading">불러오는 중</div>
      <p v-else-if="!sidebarMountains.length && mountainSearch" class="tag-filter-empty sidebar-search-empty">
        조건에 맞는 산이 없어요.
      </p>

      <div class="mountain-browse-list sidebar-mountain-list">
        <button
          v-for="mountain in sidebarMountains"
          :key="mountain.mountain_key || mountain.id"
          class="mountain-browse-row sidebar-mountain-row"
          type="button"
          @click="selectMountain(mountain)"
        >
          <i class="mbr-diff-dot" :style="{ background: diffDotColor(mountain.difficulty) }"></i>
          <span class="mbr-body">
            <strong class="mbr-name">{{ mountain.name }}</strong>
            <span class="mbr-meta">{{ mountain.region }} · {{ elevationLabel(mountain) }}</span>
          </span>
          <svg class="mbr-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
        </button>
      </div>

    </section>

    <div class="sidebar-fire-stats">
      <div class="sfs-head">
        <span class="sfs-title">산행 안전 예측</span>
        <span class="sfs-badge">{{ browseRiskLoading ? '분석 중' : riskBadgeText }}</span>
      </div>
      <p class="sfs-sub">{{ riskWarning }}</p>
      <div class="sfs-grid">
        <span v-for="pill in riskPills" :key="pill.label" class="sfs-pill" :class="pill.cls">{{ pill.label }}</span>
      </div>
      <p class="sfs-note">{{ riskNote }}</p>
    </div>
  </nav>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { authMode, authUser, showAuthModal } from '../composables/useAuth.js';
import {
  diffDotColor,
  filteredMountains,
  guideStep,
  loading,
  mountainSearch,
  selectedMountain,
  browseRisk,
  browseRiskLoading,
  loadBrowseRisk,
} from '../composables/useGuide.js';

const router = useRouter();
const sidebarDifficultyFilter = ref('all');

const riskBadgeText = computed(() => {
  if (!browseRisk.value) return '분석 중';
  const r = browseRisk.value.risk_index;
  if (r >= 0.70) return '고위험 구간';
  if (r >= 0.45) return '사고 주의';
  if (r >= 0.20) return '낮은 위험';
  return '안전 구간';
});

const riskWarning = computed(() => {
  if (!browseRisk.value) return '현재 시간·요일·계절 사고 통계 분석 중';
  return browseRisk.value.warning || '이 시간대 상대적 안전 구간입니다';
});

const riskPills = computed(() => {
  if (!browseRisk.value?.type_proba || !Object.keys(browseRisk.value.type_proba).length) return [];
  const map = { '조난수색': '길잃음·조난', '부상사고': '실족·추락', '질환': '탈진·질환', '기타': '기타' };
  const cls = ['sfs-pill-1', 'sfs-pill-2', 'sfs-pill-3', 'sfs-pill-4'];
  return Object.entries(browseRisk.value.type_proba)
    .sort((a, b) => b[1] - a[1])
    .map(([key, val], i) => ({ label: `${map[key] || key} ${Math.round(val * 100)}%`, cls: cls[i] || 'sfs-pill-4' }));
});

const riskNote = computed(() => {
  const t = browseRisk.value?.training;
  if (t?.rows && Array.isArray(t?.year_range) && t.year_range.length === 2) {
    return `* ${t.year_range[0]}-${t.year_range[1]}년 소방청 산악사고 ${Number(t.rows).toLocaleString()}건 기준`;
  }
  return '* 2010-2024년 산악사고 112,902건 기준';
});

onMounted(() => {
  if (!browseRisk.value) loadBrowseRisk();
});

const difficultyFilters = [
  { value: 'all', label: '전체', color: '#7fb069' },
  { value: 'easy', label: '초급', color: '#63b65f' },
  { value: 'medium', label: '중급', color: '#4f82d8' },
  { value: 'hard', label: '고급', color: '#6d56b8' },
];

const sidebarMountains = computed(() => {
  const list = filteredMountains.value || [];
  if (sidebarDifficultyFilter.value === 'all') return list;
  return list.filter((mountain) => mountain.difficulty === sidebarDifficultyFilter.value);
});

function elevationLabel(mountain) {
  const elevation = mountain?.elevation_m;
  if (elevation === null || elevation === undefined || elevation === '') return '고도미상';
  return `${elevation}m`;
}

function goHome() {
  guideStep.value = 'browse';
  selectedMountain.value = null;
  router.push('/guide');
}

function openLogin() {
  authMode.value = 'login';
  showAuthModal.value = true;
}

function selectMountain(mountain) {
  guideStep.value = 'courses';
  selectedMountain.value = mountain;
  router.push('/guide');
}
</script>
