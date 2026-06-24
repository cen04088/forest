<template>
  <section class="screen-stack mypage-grid">

    <!-- 로그인 유도 — 전체 너비 -->
    <div v-if="!authUser" class="panel mypage-login-prompt mypage-col-full">
      <p>로그인하면 산행 기록, 즐겨찾기, 긴급 연락처를 저장할 수 있습니다.</p>
      <button class="primary-btn" type="button" @click="showAuthModal = true">로그인 / 회원가입</button>
    </div>

    <div v-else class="panel mypage-account-bar mypage-col-full">
      <div class="mypage-account-main">
        <span class="mypage-account-avatar">{{ authUser.nickname?.[0] || authUser.username?.[0] || 'U' }}</span>
        <div>
          <p class="eyebrow">My Account</p>
          <h2>{{ authUser.nickname || authUser.username }}님</h2>
          <p class="mypage-account-id">{{ authUser.username }}</p>
        </div>
      </div>
      <button class="outline-btn mypage-logout-btn" type="button" @click="handleLogout">로그아웃</button>
    </div>

    <!-- ① 즐겨찾기 -->
    <section class="panel mypage-col-1">
      <div class="section-title compact">
        <div><p class="eyebrow">Favorites</p><h2>즐겨찾기 코스</h2></div>
        <span class="mini-status">{{ favorites.length }}개</span>
      </div>
      <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
      <div v-else-if="favorites.length === 0" class="community-empty"><p>즐겨찾기한 코스가 없습니다.<br>코스 카드의 ♡ 버튼으로 추가하세요.</p></div>
      <div v-else class="fav-list">
        <div v-for="fav in favorites" :key="fav.course_id" class="fav-item">
          <div class="fav-info">
            <strong>
              <span v-if="fav.course_id.startsWith('mountain_')" class="fav-type-badge">산</span>
              {{ fav.course_name }}
            </strong>
            <small v-if="!fav.course_id.startsWith('mountain_')">
              {{ fav.mountain }} · {{ fav.distance_km ?? '-' }}km · {{ fav.duration_min ? durationLabel(fav.duration_min) : '-' }}
            </small>
            <small v-else>{{ fav.mountain }}</small>
          </div>
          <button class="fav-remove-btn" type="button" title="즐겨찾기 해제" @click="removeFav(fav.course_id)">✕</button>
        </div>
      </div>
    </section>

    <!-- ② 챌린지 배지 -->
    <section class="panel mypage-col-1">
      <div class="section-title compact">
        <div><p class="eyebrow">Challenges</p><h2>챌린지 배지</h2></div>
        <span class="mini-status">{{ authUser ? earnedCount + '/8' : '0/8' }}</span>
      </div>
      <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
      <div v-else class="badge-grid">
        <div
          v-for="badge in badges"
          :key="badge.id"
          :class="['badge-card', badge.achieved ? 'badge-achieved' : 'badge-locked']"
          :title="badge.desc"
        >
          <span class="badge-icon">{{ badge.icon }}</span>
          <span class="badge-name">{{ badge.name }}</span>
          <span class="badge-desc">{{ badge.desc }}</span>
        </div>
      </div>
    </section>

    <!-- ④ 내 활동 (탭) -->
    <section class="panel mypage-col-1">
      <div class="section-title compact">
        <div><p class="eyebrow">Activity</p><h2>내 활동</h2></div>
        <div v-if="authUser" class="activity-tabs">
          <button :class="['act-tab', activityTab === 'posts' ? 'active' : '']" type="button" @click="activityTab = 'posts'">
            내가 쓴 글<span v-if="myPostsTotal" class="act-count">{{ myPostsTotal }}</span>
          </button>
          <button :class="['act-tab', activityTab === 'liked' ? 'active' : '']" type="button" @click="activityTab = 'liked'">
            좋아요한 글<span v-if="likedPosts.length" class="act-count">{{ likedPosts.length }}</span>
          </button>
          <button :class="['act-tab', activityTab === 'following' ? 'active' : '']" type="button" @click="activityTab = 'following'">
            팔로잉<span v-if="followingList.length" class="act-count">{{ followingList.length }}</span>
          </button>
        </div>
      </div>
      <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
      <template v-else>
        <template v-if="activityTab === 'posts'">
          <div v-if="myPostsLoading" class="community-loading">불러오는 중…</div>
          <div v-else-if="myPosts.length === 0" class="community-empty"><p>아직 작성한 글이 없습니다.</p></div>
          <div v-else class="mypost-grid">
            <div v-for="post in myPosts" :key="post.id" class="mypost-item" @click="goToPost(post.id)">
              <span class="category-tag">{{ post.category_label }}</span>
              <strong>{{ post.title }}</strong>
              <small>{{ formatRelativeTime(post.created_at) }} · 👍 {{ post.like_count }} · 💬 {{ post.comment_count }}</small>
            </div>
          </div>
        </template>
        <template v-else-if="activityTab === 'liked'">
          <div v-if="likedPostsLoading" class="community-loading">불러오는 중…</div>
          <div v-else-if="likedPosts.length === 0" class="community-empty"><p>아직 좋아요한 글이 없습니다.</p></div>
          <div v-else class="mypost-grid">
            <div v-for="post in likedPosts" :key="post.id" class="mypost-item" @click="goToPost(post.id)">
              <span class="category-tag">{{ post.category_label }}</span>
              <strong>{{ post.title }}</strong>
              <small>{{ formatRelativeTime(post.created_at) }} · 👍 {{ post.like_count }} · 💬 {{ post.comment_count }}</small>
            </div>
          </div>
        </template>

        <template v-else-if="activityTab === 'following'">
          <div v-if="followingList.length === 0" class="community-empty"><p>팔로잉 중인 사용자가 없습니다.</p></div>
          <div v-else class="following-user-list">
            <div v-for="user in followingList" :key="user.id" class="following-user-item">
              <div class="following-user-avatar">{{ (user.nickname || user.username)?.[0]?.toUpperCase() || 'U' }}</div>
              <div class="following-user-info">
                <strong>{{ user.nickname || user.username }}</strong>
                <small>@{{ user.username }}</small>
              </div>
              <button class="unfollow-btn-sm" type="button" @click="handleUnfollow(user.id)">언팔로우</button>
            </div>
          </div>
        </template>
      </template>
    </section>

    <!-- ⑤ 긴급 연락처 -->
    <section class="panel mypage-col-1">
      <div class="section-title compact">
        <div><p class="eyebrow">Emergency</p><h2>긴급 연락처</h2></div>
        <span class="mini-status">{{ emergencyContacts.length }}명</span>
      </div>
      <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
      <div v-else class="emergency-inner">
        <div v-for="contact in emergencyContacts" :key="contact.id" class="contact-item">
          <div class="contact-info">
            <strong>{{ contact.name }}</strong>
            <span v-if="contact.relation" class="contact-relation">{{ contact.relation }}</span>
            <a :href="`tel:${contact.phone}`" class="contact-phone">{{ contact.phone }}</a>
          </div>
          <button class="fav-remove-btn" type="button" @click="removeContact(contact.id)">✕</button>
        </div>
        <form class="contact-add-form" @submit.prevent="handleAddContact">
          <input v-model="contactForm.name" type="text" placeholder="이름" required />
          <input v-model="contactForm.phone" type="tel" placeholder="전화번호" required />
          <input v-model="contactForm.relation" type="text" placeholder="관계 (선택)" />
          <button class="outline-btn" type="submit" :disabled="contactLoading">추가</button>
        </form>
        <p v-if="contactError" class="auth-error">{{ contactError }}</p>
      </div>
    </section>

  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { authUser, logout, showAuthModal } from '../composables/useAuth.js';
import { favorites, hikingRecords, emergencyContacts, loadMyPageData, removeRecord, removeFav, addContact, removeContact } from '../composables/useUserData.js';
import { myPosts, myPostsTotal, myPostsLoading, loadMyPosts, likedPosts, likedPostsLoading, loadLikedPosts, followingList, loadFollowingList, toggleFollow, formatRelativeTime, openPost } from '../composables/useCommunity.js';
import { profile, applyAndSaveProfile } from '../composables/useGuide.js';
import { durationLabel } from '../utils/courseHelpers.js';

const router = useRouter();

// ── 긴급 연락처 ─────────────────────────────────────────────────────────────
const contactForm = reactive({ name: '', phone: '', relation: '' });
const contactLoading = ref(false);
const contactError = ref('');

async function handleAddContact() {
  contactLoading.value = true;
  contactError.value = '';
  try {
    await addContact(contactForm);
    contactForm.name = '';
    contactForm.phone = '';
    contactForm.relation = '';
  } catch (err) {
    contactError.value = err.message;
  } finally {
    contactLoading.value = false;
  }
}

// ── 산행 기록 통계 ───────────────────────────────────────────────────────────
const thisMonthCount = computed(() => {
  const now = new Date();
  return hikingRecords.value.filter((r) => {
    const d = new Date(r.hiked_date);
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth();
  }).length;
});

const favMountain = computed(() => {
  const counts = {};
  for (const r of hikingRecords.value) {
    if (r.mountain) counts[r.mountain] = (counts[r.mountain] || 0) + 1;
  }
  const entries = Object.entries(counts);
  return entries.length ? entries.sort((a, b) => b[1] - a[1])[0][0] : null;
});

// ── 나의 등산 프로필 ─────────────────────────────────────────────────────────
const editProfile = reactive({
  experience: profile.experience,
  availableMinutes: profile.availableMinutes,
  maxDistanceKm: profile.maxDistanceKm,
});

const profileSavedMsg = ref(false);
let _profileSaveTimer = null;

function saveProfile() {
  applyAndSaveProfile({ ...editProfile });
  profileSavedMsg.value = true;
  clearTimeout(_profileSaveTimer);
  _profileSaveTimer = setTimeout(() => { profileSavedMsg.value = false; }, 2500);
}

// ── 챌린지 배지 ──────────────────────────────────────────────────────────────
const badges = computed(() => {
  const recs = hikingRecords.value;
  const uniqueMountains = new Set(recs.map(r => r.mountain).filter(Boolean));
  const recommendedCount = recs.filter(r => r.safety_label === '추천').length;
  const longHike = recs.some(r => (r.duration_min || 0) >= 240);
  const winterHike = recs.some(r => {
    const m = new Date(r.hiked_date).getMonth() + 1;
    return m === 12 || m === 1 || m === 2;
  });
  const weekendHikes = recs.filter(r => {
    const d = new Date(r.hiked_date).getDay();
    return d === 0 || d === 6;
  }).length;
  const hardCourse = recs.some(r => r.difficulty === 'hard');

  return [
    { id: 1, icon: '🥾', name: '첫 걸음',      desc: '첫 번째 산행 기록',          achieved: recs.length >= 1 },
    { id: 2, icon: '📅', name: '꾸준한 등산러', desc: '총 5회 이상 산행',            achieved: recs.length >= 5 },
    { id: 3, icon: '🏔️', name: '산악 마니아',  desc: '총 10회 이상 산행',           achieved: recs.length >= 10 },
    { id: 4, icon: '🗺️', name: '탐험가',       desc: '3개 이상 다른 산 방문',       achieved: uniqueMountains.size >= 3 },
    { id: 5, icon: '🛡️', name: '안전 우선',    desc: '추천 코스로 3회 산행',        achieved: recommendedCount >= 3 },
    { id: 6, icon: '⏱️', name: '장거리 등반',  desc: '4시간 이상 코스 완주',        achieved: longHike },
    { id: 7, icon: '❄️', name: '겨울 전사',    desc: '겨울(12~2월) 산행 완료',     achieved: winterHike },
    { id: 8, icon: '🌿', name: '주말 등산러',  desc: '주말에 3회 이상 산행',        achieved: weekendHikes >= 3 },
  ];
});

const earnedCount = computed(() => badges.value.filter(b => b.achieved).length);

// ── 내 활동 탭 ───────────────────────────────────────────────────────────────
const activityTab = ref('posts');

async function handleUnfollow(userId) {
  await toggleFollow(userId);
}

// ── 공통 ─────────────────────────────────────────────────────────────────────
function goToPost(id) {
  openPost(id);
  router.push('/community');
}

async function handleLogout() {
  await logout(() => {
    router.push('/guide');
  });
}

onMounted(() => {
  if (authUser.value) {
    loadMyPageData();
    if (myPosts.value.length === 0) loadMyPosts();
    if (likedPosts.value.length === 0) loadLikedPosts();
    if (followingList.value.length === 0) loadFollowingList();
  }
});
</script>
