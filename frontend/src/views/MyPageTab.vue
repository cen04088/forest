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
        :class="{ active: activeSection === feature.key }"
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

    <!-- 즐겨찾기 패널 -->
    <section v-if="activeSection === 'favorites'" class="mypage-inline-panel">
      <h3 class="inline-panel-title">즐겨찾기 <span class="panel-count">{{ favorites.length }}</span></h3>
      <div v-if="favorites.length === 0" class="inline-panel-empty">저장된 즐겨찾기가 없습니다.</div>
      <div v-else class="fav-card-grid">
        <div v-for="fav in favorites" :key="fav.course_id" class="fav-card">
          <button class="fav-card-remove" type="button" @click="removeFav(fav.course_id)" aria-label="삭제">✕</button>
          <div class="fav-card-icon">⛰️</div>
          <strong class="fav-card-name">{{ fav.mountain }}</strong>
          <span v-if="fav.course_name && fav.course_name !== fav.mountain" class="fav-card-course">{{ fav.course_name }}</span>
          <div v-if="fav.distance_km" class="fav-card-meta">{{ fav.distance_km }}km · {{ fav.duration_min }}분</div>
          <button class="fav-card-goto" type="button" @click="goToMountain(fav)">산 정보 보기 →</button>
        </div>
      </div>
    </section>

    <!-- 챌린지 배지 패널 -->
    <section v-if="activeSection === 'challenges'" class="mypage-inline-panel">
      <h3 class="inline-panel-title">챌린지 배지 <span class="panel-count">{{ earnedBadgeCount }}/8</span></h3>
      <div class="badge-card-grid">
        <div
          v-for="badge in allBadges"
          :key="badge.key"
          class="badge-card"
          :class="{ earned: badge.earned }"
        >
          <span class="badge-card-icon">{{ badge.icon }}</span>
          <span class="badge-card-name">{{ badge.name }}</span>
          <span class="badge-card-cond">{{ badge.condition }}</span>
          <span v-if="badge.earned" class="badge-earned-mark">획득</span>
        </div>
      </div>
    </section>

    <!-- 내 활동 패널 -->
    <section v-if="activeSection === 'activity'" class="mypage-inline-panel">
      <h3 class="inline-panel-title">내 활동</h3>
      <div class="activity-tab-row">
        <button :class="['activity-tab', activityTab === 'posts' ? 'active' : '']" type="button" @click="switchActivityTab('posts')">
          작성글 <span class="tab-count">{{ myPosts.length }}</span>
        </button>
        <button :class="['activity-tab', activityTab === 'liked' ? 'active' : '']" type="button" @click="switchActivityTab('liked')">
          좋아요 <span class="tab-count">{{ likedPosts.length }}</span>
        </button>
        <button :class="['activity-tab', activityTab === 'comments' ? 'active' : '']" type="button" @click="switchActivityTab('comments')">
          댓글 <span class="tab-count">{{ myComments.length }}</span>
        </button>
      </div>

      <!-- 작성글 -->
      <template v-if="activityTab === 'posts'">
        <p v-if="myPostsLoading" class="inline-panel-empty">불러오는 중…</p>
        <div v-else-if="myPosts.length === 0" class="inline-panel-empty">작성한 게시글이 없습니다.</div>
        <div v-else class="activity-post-list">
          <div v-for="post in myPosts" :key="post.id" class="activity-post-item">
            <span class="post-cat-badge">{{ post.category_label || post.category }}</span>
            <strong class="activity-post-title">{{ post.title }}</strong>
            <span class="activity-post-meta">{{ post.created_at?.slice(0, 10) }} · 💬 {{ post.comment_count ?? 0 }} · ♥ {{ post.like_count ?? 0 }}</span>
          </div>
        </div>
      </template>

      <!-- 좋아요한 글 -->
      <template v-else-if="activityTab === 'liked'">
        <p v-if="likedPostsLoading" class="inline-panel-empty">불러오는 중…</p>
        <div v-else-if="likedPosts.length === 0" class="inline-panel-empty">좋아요한 게시글이 없습니다.</div>
        <div v-else class="activity-post-list">
          <div v-for="post in likedPosts" :key="post.id" class="activity-post-item">
            <span class="post-cat-badge">{{ post.category_label || post.category }}</span>
            <strong class="activity-post-title">{{ post.title }}</strong>
            <span class="activity-post-meta">{{ post.author }} · {{ post.created_at?.slice(0, 10) }}</span>
          </div>
        </div>
      </template>

      <!-- 댓글 -->
      <template v-else-if="activityTab === 'comments'">
        <p v-if="myCommentsLoading" class="inline-panel-empty">불러오는 중…</p>
        <div v-else-if="myComments.length === 0" class="inline-panel-empty">작성한 댓글이 없습니다.</div>
        <div v-else class="activity-post-list">
          <div v-for="comment in myComments" :key="comment.id" class="activity-post-item">
            <span class="post-cat-badge comment-badge">댓글</span>
            <strong class="activity-post-title">{{ comment.post_title }}</strong>
            <span class="activity-comment-body">{{ comment.content }}</span>
            <span class="activity-post-meta">{{ comment.created_at?.slice(0, 10) }}</span>
          </div>
        </div>
      </template>
    </section>

    <!-- 긴급 연락처 패널 -->
    <section v-if="activeSection === 'emergency'" class="mypage-inline-panel">
      <h3 class="inline-panel-title">긴급 연락처 <span class="panel-count">{{ emergencyContacts.length }}</span></h3>
      <div v-if="emergencyContacts.length > 0" class="contact-card-grid">
        <div v-for="contact in emergencyContacts" :key="contact.id" class="contact-card">
          <button class="fav-card-remove" type="button" @click="removeContact(contact.id)" aria-label="삭제">✕</button>
          <span class="contact-card-icon">📞</span>
          <strong class="contact-card-name">{{ contact.name }}</strong>
          <span v-if="contact.relation" class="contact-card-rel">{{ contact.relation }}</span>
          <a :href="`tel:${contact.phone}`" class="contact-card-phone">{{ contact.phone }}</a>
        </div>
      </div>
      <div v-else class="inline-panel-empty">등록된 긴급 연락처가 없습니다.</div>

      <form class="inline-contact-form" @submit.prevent="submitContact">
        <h4 class="contact-form-title">연락처 추가</h4>
        <div class="contact-form-row">
          <input v-model="contactForm.name" class="contact-input" type="text" placeholder="이름" required />
          <input v-model="contactForm.relation" class="contact-input" type="text" placeholder="관계 (선택)" />
        </div>
        <div class="contact-form-row">
          <input v-model="contactForm.phone" class="contact-input" type="tel" placeholder="전화번호" required />
          <button class="contact-add-btn" type="submit" :disabled="contactAdding">
            {{ contactAdding ? '추가 중…' : '추가' }}
          </button>
        </div>
        <p v-if="contactError" class="contact-form-error">{{ contactError }}</p>
      </form>
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
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { authUser, logout, showAuthModal } from '../composables/useAuth.js';
import { favorites, hikingRecords, emergencyContacts, loadMyPageData, removeFav, addContact, removeContact } from '../composables/useUserData.js';
import { myPostsTotal, myPosts, myPostsLoading, loadMyPosts, likedPosts, likedPostsLoading, loadLikedPosts, myComments, myCommentsLoading, loadMyComments } from '../composables/useCommunity.js';
import { publicMountains, selectedMountain, guideStep } from '../composables/useGuide.js';
import { useRouter } from 'vue-router';

const router = useRouter();
const activeSection = ref(null);
const activityTab = ref('posts');

function switchActivityTab(tab) {
  activityTab.value = tab;
  if (tab === 'liked' && likedPosts.value.length === 0) loadLikedPosts();
  if (tab === 'comments' && myComments.value.length === 0) loadMyComments();
}

function goToMountain(fav) {
  const isMountainKey = typeof fav.course_id === 'string' && fav.course_id.startsWith('mountain_');
  if (isMountainKey) {
    const mountainId = parseInt(fav.course_id.replace('mountain_', ''));
    const mountain = publicMountains.value.find((m) => m.id === mountainId);
    if (mountain) {
      selectedMountain.value = mountain;
      guideStep.value = 'course';
      router.push('/guide');
      return;
    }
  }
  router.push('/guide');
}

const displayName = computed(() => authUser.value?.nickname || authUser.value?.username || '회원');

const contactForm = reactive({ name: '', relation: '', phone: '' });
const contactAdding = ref(false);
const contactError = ref('');

async function submitContact() {
  contactError.value = '';
  contactAdding.value = true;
  try {
    await addContact({ name: contactForm.name, relation: contactForm.relation, phone: contactForm.phone });
    contactForm.name = '';
    contactForm.relation = '';
    contactForm.phone = '';
  } catch (e) {
    contactError.value = '추가에 실패했습니다. 다시 시도해 주세요.';
  } finally {
    contactAdding.value = false;
  }
}

const earnedBadgeCount = computed(() => allBadges.value.filter((b) => b.earned).length);

const allBadges = computed(() => {
  const recs = hikingRecords.value;
  const uniqueMountains = new Set(recs.map((r) => r.mountain).filter(Boolean));
  const recommendedCount = recs.filter((r) => r.safety_label === '추천').length;
  const longHike = recs.some((r) => Number(r.duration_min || 0) >= 240);
  const winterHike = recs.some((r) => { const m = new Date(r.hiked_date).getMonth() + 1; return m === 12 || m === 1 || m === 2; });
  const weekendHikes = recs.filter((r) => { const d = new Date(r.hiked_date).getDay(); return d === 0 || d === 6; }).length;

  return [
    { key: 'first',     icon: '🥾', name: '첫 발걸음',   condition: '첫 산행 기록',         earned: recs.length >= 1 },
    { key: 'five',      icon: '⛰️',  name: '산악인',      condition: '산행 5회',             earned: recs.length >= 5 },
    { key: 'ten',       icon: '🏔️', name: '등산 고수',   condition: '산행 10회',            earned: recs.length >= 10 },
    { key: 'explorer',  icon: '🗺️', name: '탐험가',      condition: '3개 산 방문',          earned: uniqueMountains.size >= 3 },
    { key: 'safe',      icon: '🛡️', name: '안전 산행왕', condition: '추천 코스 3회 이상',   earned: recommendedCount >= 3 },
    { key: 'endurance', icon: '💪', name: '지구력 왕',   condition: '4시간 이상 산행',      earned: longHike },
    { key: 'winter',    icon: '❄️', name: '겨울 산악인', condition: '겨울 산행(12·1·2월)', earned: winterHike },
    { key: 'weekend',   icon: '🌄', name: '주말 등산러', condition: '주말 산행 3회',        earned: weekendHikes >= 3 },
  ];
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
    onClick: () => {
      if (!requireLogin()) return;
      activeSection.value = activeSection.value === 'favorites' ? null : 'favorites';
    },
  },
  {
    key: 'challenges',
    eyebrow: 'CHALLENGES',
    title: '챌린지 배지',
    desc: '완료한 챌린지와 배지를 확인하고 새로운 도전에 참여해보세요.',
    badge: `${authUser.value ? earnedBadgeCount.value : 0}/8`,
    icon: icons.trophy,
    onClick: () => {
      if (!requireLogin()) return;
      activeSection.value = activeSection.value === 'challenges' ? null : 'challenges';
    },
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
      if (activeSection.value !== 'activity') {
        activityTab.value = 'posts';
        if (myPosts.value.length === 0) loadMyPosts();
      }
      activeSection.value = activeSection.value === 'activity' ? null : 'activity';
    },
  },
  {
    key: 'emergency',
    eyebrow: 'EMERGENCY',
    title: '긴급 연락처',
    desc: '산행 중 긴급 상황에 대비해 연락처를 저장하고 관리하세요.',
    badge: `${authUser.value ? emergencyContacts.value.length : 0}명`,
    icon: icons.phone,
    onClick: () => {
      if (!requireLogin()) return;
      activeSection.value = activeSection.value === 'emergency' ? null : 'emergency';
    },
  },
]);

function requireLogin() {
  if (authUser.value) return true;
  showAuthModal.value = true;
  return false;
}

async function handleLogout() {
  activeSection.value = null;
  await logout(() => {
    router.push('/guide');
  });
}

async function loadAccountData() {
  if (!authUser.value) return;
  await loadMyPageData();
  if (myPostsTotal.value === 0) loadMyPosts();
}

watch(authUser, () => {
  activeSection.value = null;
  loadAccountData();
});

onMounted(loadAccountData);
</script>
