<template>
  <section class="mypage-final">
    <section class="mypage-hero-card">
      <div class="mypage-hero-copy">
        <h1>
          <template v-if="authUser">
            안녕하세요, <span>{{ displayName }}님!</span>
          </template>
          <template v-else>안녕하세요!</template>
        </h1>
        <p>로그인하면 산행 기록, 즐겨찾기, 긴급 연락처를 저장할 수 있습니다.</p>
        <button v-if="authUser" class="mypage-hero-btn" type="button" @click="handleLogout">로그아웃</button>
        <button v-else class="mypage-hero-btn" type="button" @click="showAuthModal = true">로그인 / 회원가입</button>
      </div>
    </section>

    <section class="mypage-feature-grid" aria-label="마이페이지 주요 기능">
      <button
        v-for="feature in featureCards"
        :key="feature.key"
        class="mypage-feature-card"
        type="button"
        @click="feature.onClick"
      >
        <span class="feature-icon" v-html="feature.icon"></span>
        <span class="feature-copy">
          <span class="feature-eyebrow">{{ feature.eyebrow }}</span>
          <strong>{{ feature.title }}</strong>
          <span>{{ feature.desc }}</span>
        </span>
        <span class="feature-badge">{{ feature.badge }}</span>
        <span class="feature-arrow" aria-hidden="true">›</span>
      </button>
    </section>

    <section class="mypage-bottom-banner">
      <span class="bottom-shield" aria-hidden="true">
        <svg viewBox="0 0 24 24"><path d="M12 3 5 6v5c0 4.7 2.9 8.4 7 10 4.1-1.6 7-5.3 7-10V6l-7-3Z" /><path d="m9 12 2 2 4-5" /></svg>
      </span>
      <div class="bottom-copy">
        <h2>Ola 계정으로 더 안전하고 편리한 산행을 경험하세요.</h2>
        <p>로그인 후 모든 기능을 이용할 수 있습니다.</p>
      </div>
      <div class="backpack-illustration" aria-hidden="true">
        <span class="rock rock-left"></span>
        <span class="rock rock-right"></span>
        <span class="leaf leaf-left"></span>
        <span class="leaf leaf-right"></span>
        <span class="bag">
          <span class="bag-pocket"></span>
          <span class="bag-flap"></span>
        </span>
      </div>
    </section>
  </section>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { authUser, logout, showAuthModal } from '../composables/useAuth.js';
import { favorites, hikingRecords, emergencyContacts, loadMyPageData } from '../composables/useUserData.js';
import { myPostsTotal, myPosts, loadMyPosts, openPost } from '../composables/useCommunity.js';

const router = useRouter();

const displayName = computed(() => authUser.value?.nickname || authUser.value?.username || '회원');

const earnedBadgeCount = computed(() => {
  const recs = hikingRecords.value;
  const uniqueMountains = new Set(recs.map((record) => record.mountain).filter(Boolean));
  const recommendedCount = recs.filter((record) => record.safety_label === '추천').length;
  const longHike = recs.some((record) => Number(record.duration_min || 0) >= 240);
  const winterHike = recs.some((record) => {
    const month = new Date(record.hiked_date).getMonth() + 1;
    return month === 12 || month === 1 || month === 2;
  });
  const weekendHikes = recs.filter((record) => {
    const day = new Date(record.hiked_date).getDay();
    return day === 0 || day === 6;
  }).length;

  return [
    recs.length >= 1,
    recs.length >= 5,
    recs.length >= 10,
    uniqueMountains.size >= 3,
    recommendedCount >= 3,
    longHike,
    winterHike,
    weekendHikes >= 3,
  ].filter(Boolean).length;
});

const icons = {
  bookmark: '<svg viewBox="0 0 24 24"><path d="M6 4h12v17l-6-4-6 4V4Z" /></svg>',
  trophy: '<svg viewBox="0 0 24 24"><path d="M8 21h8" /><path d="M12 17v4" /><path d="M7 4h10v6a5 5 0 0 1-10 0V4Z" /><path d="M5 6H3v2a4 4 0 0 0 4 4" /><path d="M19 6h2v2a4 4 0 0 1-4 4" /></svg>',
  activity: '<svg viewBox="0 0 24 24"><path d="M4 18 9 13l3 3 7-9" /><path d="M15 7h4v4" /></svg>',
  phone: '<svg viewBox="0 0 24 24"><path d="M22 16.9v3a2 2 0 0 1-2.2 2A19.8 19.8 0 0 1 3.1 5.2 2 2 0 0 1 5.1 3h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.6a2 2 0 0 1-.4 2.1L9 10.7a16 16 0 0 0 4.3 4.3l1.3-1.3a2 2 0 0 1 2.1-.4c.8.3 1.7.5 2.6.6a2 2 0 0 1 1.7 2Z" /></svg>',
};

const featureCards = computed(() => [
  {
    key: 'favorites',
    eyebrow: 'FAVORITES',
    title: '즐겨찾기 코스',
    desc: '자주 찾는 산행 코스를 저장하고 한눈에 확인하세요.',
    badge: `${authUser.value ? favorites.value.length : 0}개`,
    icon: icons.bookmark,
    onClick: () => requireLogin(),
  },
  {
    key: 'challenges',
    eyebrow: 'CHALLENGES',
    title: '챌린지 배지',
    desc: '완료한 챌린지와 배지를 확인하고 새로운 도전에 참여해보세요.',
    badge: `${authUser.value ? earnedBadgeCount.value : 0}/8`,
    icon: icons.trophy,
    onClick: () => requireLogin(),
  },
  {
    key: 'activity',
    eyebrow: 'ACTIVITY',
    title: '내 활동',
    desc: '작성한 게시글, 댓글, 좋아요 등 나의 활동 내역을 확인하세요.',
    badge: `${authUser.value ? myPostsTotal.value : 0}개`,
    icon: icons.activity,
    onClick: () => {
      if (!requireLogin()) return;
      if (myPosts.value[0]?.id) openPost(myPosts.value[0].id);
      router.push('/community');
    },
  },
  {
    key: 'emergency',
    eyebrow: 'EMERGENCY',
    title: '긴급 연락처',
    desc: '산행 중 긴급 상황에 대비해 연락처를 저장하고 관리하세요.',
    badge: `${authUser.value ? emergencyContacts.value.length : 0}명`,
    icon: icons.phone,
    onClick: () => requireLogin(),
  },
]);

function requireLogin() {
  if (authUser.value) return true;
  showAuthModal.value = true;
  return false;
}

async function handleLogout() {
  await logout(() => {
    router.push('/guide');
  });
}

async function loadAccountData() {
  if (!authUser.value) return;
  await loadMyPageData();
  if (myPosts.value.length === 0) loadMyPosts();
}

watch(authUser, () => {
  loadAccountData();
});

onMounted(loadAccountData);
</script>
