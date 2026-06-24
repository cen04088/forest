<template>
  <section class="screen-stack mypage-grid">

    <!-- 로그인 유도 — 전체 너비 -->
    <div v-if="!authUser" class="panel mypage-login-prompt mypage-col-full">
      <p>로그인하면 산행 기록, 즐겨찾기, 긴급 연락처를 저장할 수 있습니다.</p>
      <button class="primary-btn" type="button" @click="showAuthModal = true">로그인 / 회원가입</button>
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

    <!-- ② 산행 기록 (통계 추가) -->
    <section class="panel mypage-col-1">
      <div class="section-title compact">
        <div><p class="eyebrow">History</p><h2>산행 기록</h2></div>
        <span class="mini-status">{{ hikingRecords.length }}회</span>
      </div>
      <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
      <template v-else>
        <div v-if="hikingRecords.length > 0" class="hiking-stats">
          <div class="hstat">
            <span class="hstat-n">{{ hikingRecords.length }}</span>
            <span class="hstat-l">총 산행</span>
          </div>
          <div class="hstat">
            <span class="hstat-n">{{ thisMonthCount }}</span>
            <span class="hstat-l">이번 달</span>
          </div>
          <div v-if="favMountain" class="hstat hstat-wide">
            <span class="hstat-n hstat-mountain">{{ favMountain }}</span>
            <span class="hstat-l">가장 많이</span>
          </div>
        </div>
        <div v-if="hikingRecords.length === 0" class="community-empty"><p>아직 산행 기록이 없습니다.<br>산행 종료 시 자동으로 저장됩니다.</p></div>
        <div v-else class="hiking-record-list">
          <div v-for="rec in hikingRecords" :key="rec.id" class="hiking-record-item">
            <div class="record-info">
              <strong>{{ rec.mountain ? rec.mountain + ' ' : '' }}{{ rec.course_name }}</strong>
              <small>{{ rec.hiked_date }} · {{ rec.duration_min ? durationLabel(rec.duration_min) : '-' }}</small>
              <span v-if="rec.safety_label" :class="['safety-badge', rec.safety_label === '추천' ? 'green' : rec.safety_label === '주의' ? 'yellow' : 'gray']" style="font-size:11px">{{ rec.safety_label }}</span>
            </div>
            <button class="fav-remove-btn" type="button" @click="removeRecord(rec.id)">✕</button>
          </div>
        </div>
      </template>
    </section>

    <!-- ③ 나의 등산 프로필 -->
    <section class="panel mypage-col-1">
      <div class="section-title compact">
        <div><p class="eyebrow">My Profile</p><h2>나의 등산 프로필</h2></div>
        <span v-if="profileSavedMsg" class="mini-status hpf-saved-ok">저장됨 ✓</span>
      </div>
      <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
      <div v-else class="hiking-profile-form">
        <label class="hpf-row">
          <span class="hpf-label">경험</span>
          <select v-model="editProfile.experience" class="hpf-select">
            <option value="beginner">초보</option>
            <option value="intermediate">중급</option>
            <option value="expert">숙련</option>
          </select>
        </label>
        <label class="hpf-row">
          <span class="hpf-label">동반자</span>
          <select v-model="editProfile.companion" class="hpf-select">
            <option value="solo">혼자</option>
            <option value="family">가족</option>
            <option value="vulnerable">어린이·노약자</option>
          </select>
        </label>
        <label class="hpf-row">
          <span class="hpf-label">산행 강도</span>
          <select v-model="editProfile.intensity" class="hpf-select">
            <option value="light">가볍게</option>
            <option value="moderate">보통</option>
            <option value="hard">강하게</option>
          </select>
        </label>
        <label class="hpf-row">
          <span class="hpf-label">가능 시간</span>
          <div class="hpf-input-row">
            <input type="number" v-model.number="editProfile.availableMinutes" min="60" max="720" step="30" class="hpf-number" />
            <span class="hpf-unit">분</span>
          </div>
        </label>
        <label class="hpf-row">
          <span class="hpf-label">최대 거리</span>
          <div class="hpf-input-row">
            <input type="number" v-model.number="editProfile.maxDistanceKm" min="10" max="200" step="10" class="hpf-number" />
            <span class="hpf-unit">km</span>
          </div>
        </label>
        <button class="primary-btn hpf-save-btn" type="button" @click="saveProfile">저장</button>
        <p class="hpf-hint">저장한 정보는 코스 추천과 AI 도우미에 자동 반영됩니다.</p>
      </div>
    </section>

    <!-- ④ 내 활동 (탭) -->
    <section v-if="authUser" class="panel mypage-col-full">
      <div class="section-title compact">
        <div><p class="eyebrow">Activity</p><h2>내 활동</h2></div>
        <div class="activity-tabs">
          <button :class="['act-tab', activityTab === 'posts' ? 'active' : '']" type="button" @click="activityTab = 'posts'">
            내가 쓴 글<span v-if="myPostsTotal" class="act-count">{{ myPostsTotal }}</span>
          </button>
          <button :class="['act-tab', activityTab === 'liked' ? 'active' : '']" type="button" @click="activityTab = 'liked'">
            좋아요한 글<span v-if="likedPosts.length" class="act-count">{{ likedPosts.length }}</span>
          </button>
        </div>
      </div>

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

      <template v-else>
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
    </section>

    <!-- ⑤ 긴급 연락처 -->
    <section class="panel mypage-col-full">
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
import { authUser, showAuthModal } from '../composables/useAuth.js';
import { favorites, hikingRecords, emergencyContacts, loadMyPageData, removeRecord, removeFav, addContact, removeContact } from '../composables/useUserData.js';
import { myPosts, myPostsTotal, myPostsLoading, loadMyPosts, likedPosts, likedPostsLoading, loadLikedPosts, formatRelativeTime, openPost } from '../composables/useCommunity.js';
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
  companion: profile.companion,
  intensity: profile.intensity,
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

// ── 내 활동 탭 ───────────────────────────────────────────────────────────────
const activityTab = ref('posts');

// ── 공통 ─────────────────────────────────────────────────────────────────────
function goToPost(id) {
  openPost(id);
  router.push('/community');
}

onMounted(() => {
  if (authUser.value) {
    loadMyPageData();
    if (myPosts.value.length === 0) loadMyPosts();
    if (likedPosts.value.length === 0) loadLikedPosts();
  }
});
</script>
