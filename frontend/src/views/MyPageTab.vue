<template>
  <section class="screen-stack mypage-layout">

    <!-- 로그인 유도 (full width) -->
    <div v-if="!authUser" class="panel mypage-login-prompt mypage-full">
      <p>로그인하면 산행 기록, 즐겨찾기, 긴급 연락처를 저장할 수 있습니다.</p>
      <button class="primary-btn" type="button" @click="showAuthModal = true">로그인 / 회원가입</button>
    </div>

    <!-- 개인 설정 -->
    <section class="panel profile-settings">
      <div class="section-title compact">
        <div><p class="eyebrow">My Info</p><h2>개인 설정</h2></div>
        <span class="mini-status">{{ myProfileStatus }}</span>
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

    <!-- 즐겨찾기 -->
    <section class="panel">
      <div class="section-title compact">
        <div><p class="eyebrow">Favorites</p><h2>즐겨찾기 코스</h2></div>
        <span class="mini-status">{{ favorites.length }}개</span>
      </div>
      <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
      <div v-else-if="favorites.length === 0" class="community-empty"><p>즐겨찾기한 코스가 없습니다.<br>코스 카드의 ♡ 버튼으로 추가하세요.</p></div>
      <div v-else class="fav-list">
        <div v-for="fav in favorites" :key="fav.course_id" class="fav-item">
          <div class="fav-info">
            <strong>{{ fav.course_name }}</strong>
            <small>{{ fav.mountain }} · {{ fav.distance_km ?? '-' }}km · {{ fav.duration_min ? durationLabel(fav.duration_min) : '-' }}</small>
          </div>
          <button class="fav-remove-btn" type="button" title="즐겨찾기 해제" @click="removeFav(fav.course_id)">✕</button>
        </div>
      </div>
    </section>

    <!-- 산행 기록 -->
    <section class="panel">
      <div class="section-title compact">
        <div><p class="eyebrow">History</p><h2>산행 기록</h2></div>
        <span class="mini-status">{{ hikingRecords.length }}회</span>
      </div>
      <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
      <div v-else-if="hikingRecords.length === 0" class="community-empty"><p>아직 산행 기록이 없습니다.<br>산행 종료 시 자동으로 저장됩니다.</p></div>
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
    </section>

    <!-- 내가 쓴 글 (full width) -->
    <section v-if="authUser" class="panel mypage-full">
      <div class="section-title compact">
        <div><p class="eyebrow">My Posts</p><h2>내가 쓴 글</h2></div>
        <span class="mini-status">{{ myPostsTotal }}개</span>
      </div>
      <div v-if="myPostsLoading" class="community-loading">불러오는 중…</div>
      <div v-else-if="myPosts.length === 0" class="community-empty"><p>아직 작성한 글이 없습니다.</p></div>
      <div v-else>
        <div
          v-for="post in myPosts" :key="post.id"
          class="mypost-item" @click="goToPost(post.id)"
        >
          <span class="category-tag">{{ post.category_label }}</span>
          <strong>{{ post.title }}</strong>
          <small>{{ formatRelativeTime(post.created_at) }} · 👍 {{ post.like_count }} · 💬 {{ post.comment_count }}</small>
        </div>
      </div>
    </section>

    <!-- 긴급 연락처 (full width) -->
    <section class="panel mypage-full">
      <div class="section-title compact">
        <div><p class="eyebrow">Emergency</p><h2>긴급 연락처</h2></div>
        <span class="mini-status">{{ emergencyContacts.length }}명</span>
      </div>
      <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
      <div v-else>
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

    <!-- 출발 전 체크리스트 (full width) -->
    <section class="panel guardian-checklist mypage-full">
      <div class="section-title compact">
        <div><p class="eyebrow">Checklist</p><h2>출발 전 체크리스트</h2></div>
        <span class="mini-status">{{ checkedCount }}/{{ checklistItems.length }}</span>
      </div>
      <label v-for="(item, i) in checklistItems" :key="item.id" class="custom-check-item">
        <input type="checkbox" class="hidden-check" v-model="item.checked" @change="saveChecklist" />
        <span class="check-box"></span>
        <span>{{ item.text }}</span>
        <button class="checklist-del-btn" type="button" @click.prevent="removeChecklistItem(i)">✕</button>
      </label>
      <div class="checklist-add-row">
        <input v-model="newChecklistText" type="text" placeholder="새 항목 추가…" @keydown.enter.prevent="addChecklistItem" />
        <button class="outline-btn" type="button" @click="addChecklistItem">추가</button>
      </div>
    </section>

  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { authUser, showAuthModal } from '../composables/useAuth.js';
import { favorites, hikingRecords, emergencyContacts, loadMyPageData, removeRecord, removeFav, addContact, removeContact } from '../composables/useUserData.js';
import { myPosts, myPostsTotal, myPostsLoading, loadMyPosts, formatRelativeTime, communityView, openPost } from '../composables/useCommunity.js';
import { profile } from '../composables/useGuide.js';
import { durationLabel } from '../utils/courseHelpers.js';

const router = useRouter();

const contactForm = reactive({ name: '', phone: '', relation: '' });
const contactLoading = ref(false);
const contactError = ref('');

const DEFAULT_CHECKLIST = [
  '아이와 보호자 연락처를 서로 확인했어요',
  '물, 간식, 보조배터리를 챙겼어요',
  '입산 통제와 날씨 변화를 한 번 더 확인했어요',
  '해 지기 전에 내려오는 계획을 세웠어요',
];

function loadChecklistFromStorage() {
  try {
    const saved = localStorage.getItem('olla_checklist');
    if (saved) return JSON.parse(saved);
  } catch {}
  return DEFAULT_CHECKLIST.map((text, i) => ({ id: i, text, checked: false }));
}

const checklistItems = ref(loadChecklistFromStorage());
const newChecklistText = ref('');
const checkedCount = computed(() => checklistItems.value.filter((i) => i.checked).length);

const myProfileStatus = computed(() => {
  const companionTypes = [
    { value: 'vulnerable', label: '어린이·노약자 동반' },
    { value: 'family', label: '가족 동반' },
    { value: 'solo', label: '혼자 산행' },
  ];
  return (companionTypes.find((t) => t.value === profile.companion)?.label || '동반자').replace(' 동반', '');
});

function saveChecklist() {
  try { localStorage.setItem('olla_checklist', JSON.stringify(checklistItems.value)); } catch {}
}

function addChecklistItem() {
  const text = newChecklistText.value.trim();
  if (!text) return;
  checklistItems.value.push({ id: Date.now(), text, checked: false });
  newChecklistText.value = '';
  saveChecklist();
}

function removeChecklistItem(index) {
  checklistItems.value.splice(index, 1);
  saveChecklist();
}

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

function goToPost(id) {
  openPost(id);
  router.push('/community');
}

onMounted(() => {
  if (authUser.value) {
    loadMyPageData();
    if (myPosts.value.length === 0) loadMyPosts();
  }
});
</script>
