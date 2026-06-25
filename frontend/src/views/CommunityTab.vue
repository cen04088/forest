<template>
  <section class="screen-stack community-page">
    <template v-if="communityView === 'list'">
      <template v-if="!activeInfoPost">
        <section class="info-mag-section">
          <div class="info-mag-header">
            <span class="info-mag-eyebrow">EDITOR'S PICK</span>
            <h2 class="info-mag-heading">이번 주 정보글</h2>
            <p class="info-mag-sub">올라 에디터가 직접 큐레이션한 산행 정보</p>
          </div>

          <div class="info-mag-list">
            <article
              v-for="(slide, idx) in heroThemeSlides"
              :key="slide.id"
              class="info-mag-card"
              :style="{ '--mag-image': `url('${slide.image}')` }"
              @click="activeInfoPost = slide.id"
            >
              <div class="info-mag-image"></div>
              <div class="info-mag-card-inner">
                <div class="info-mag-card-top">
                  <div class="info-mag-meta-left">
                    <span class="info-mag-num">{{ String(idx + 1).padStart(2, '0') }}</span>
                    <span class="info-mag-badge">{{ slide.infoPost.label }}</span>
                  </div>
                </div>

                <div class="info-mag-card-bottom">
                  <p class="info-mag-mountain">{{ formatMountainTags(slide.infoPost.mountain) }}</p>
                  <strong class="info-mag-title">{{ slide.infoPost.title }}</strong>
                  <div class="info-mag-tags">
                    <span v-for="tag in slide.infoPost.tags.slice(0, 3)" :key="tag" class="info-mag-tag">
                      {{ cleanTag(tag) }}
                    </span>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </section>
      </template>

      <template v-else>
        <section class="info-detail-section">
          <button class="info-detail-back" type="button" @click="activeInfoPost = null">← 목록으로</button>
          <template v-for="slide in heroThemeSlides" :key="slide.id">
            <template v-if="slide.id === activeInfoPost">
              <div class="info-detail-hero" :style="{ '--detail-image': `url('${slide.image}')` }">
                <span class="info-detail-badge">{{ slide.infoPost.label }}</span>
                <h1 class="info-detail-title">{{ slide.infoPost.title }}</h1>
                <p class="info-detail-mountain">{{ slide.infoPost.mountain }}</p>
              </div>
              <div class="info-detail-body">
                <p
                  v-for="(para, i) in slide.infoPost.content.split('\n\n')"
                  :key="i"
                  class="info-detail-para"
                >
                  {{ para }}
                </p>
                <div class="info-detail-tags">
                  <span v-for="tag in slide.infoPost.tags" :key="tag" class="info-mag-tag">{{ cleanTag(tag) }}</span>
                </div>
              </div>
            </template>
          </template>
        </section>
      </template>

      <template v-if="!activeInfoPost">
        <section class="community-feed">
          <div class="section-title compact community-feed-head">
            <div>
              <p class="eyebrow">COMMUNITY</p>
              <h2>동반 산행 커뮤니티</h2>
            </div>
            <div class="community-header-actions">
              <div v-if="authUser" class="following-menu-wrap" v-click-outside="() => followingMenuOpen = false">
                <button type="button" class="following-menu-btn" @click="toggleFollowingMenu">
                  팔로잉
                  <span class="following-count-badge">{{ followingList.length }}</span>
                </button>
                <div v-if="followingMenuOpen" class="following-dropdown">
                  <p class="following-dropdown-title">팔로잉 목록</p>
                  <div v-if="followingList.length === 0" class="following-empty">팔로우한 사람이 없습니다.</div>
                  <ul v-else class="following-list">
                    <li v-for="user in followingList" :key="user.id" class="following-item">
                      <div class="following-avatar">{{ user.nickname[0] }}</div>
                      <span class="following-name">{{ user.nickname }}</span>
                      <button class="unfollow-btn" type="button" @click="handleUnfollow(user.id)">언팔로우</button>
                    </li>
                  </ul>
                </div>
              </div>

              <button v-if="authUser" class="write-btn" type="button" @click="openWrite">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>
                글쓰기
              </button>
              <button v-else class="write-btn write-btn-ghost" type="button" @click="showAuthModal = true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>
                글쓰기
              </button>
            </div>
          </div>

          <div class="community-search-row">
            <input
              v-model="communitySearch"
              type="search"
              placeholder="제목·내용 검색..."
              class="community-search-input"
              @keydown.enter="loadPosts(1)"
            />
            <button class="outline-btn community-search-btn" type="button" @click="loadPosts(1)">검색</button>
          </div>

          <div class="filter-row">
            <button :class="{ active: communityCategory === '' }" type="button" @click="filterCategory('')">전체</button>
            <button :class="{ active: communityCategory === 'review' }" type="button" @click="filterCategory('review')">등산 후기</button>
            <button :class="{ active: communityCategory === 'question' }" type="button" @click="filterCategory('question')">질문</button>
            <button :class="{ active: communityCategory === 'safety' }" type="button" @click="filterCategory('safety')">안전 제보</button>
            <button :class="{ active: communityCategory === 'general' }" type="button" @click="filterCategory('general')">자유</button>
            <button
              v-if="authUser"
              :class="['follow-feed-btn', { active: communityCategory === 'following' }]"
              type="button"
              @click="filterCategory('following')"
            >
              팔로잉
            </button>
          </div>

          <template v-if="communityCategory === 'following'">
            <div v-if="followingPostsLoading" class="community-loading">게시글을 불러오는 중입니다.</div>
            <div v-else-if="followingPosts.length === 0" class="community-empty">
              <p>팔로우한 사람의 게시글이 없습니다.</p>
              <p>게시글 상세에서 작성자를 팔로우해 보세요.</p>
            </div>
            <div v-else class="community-post-grid">
              <CommunityPostCard
                v-for="post in followingPosts"
                :key="post.id"
                :post="post"
                :auth-user="authUser"
                :format-relative-time="formatRelativeTime"
                @open="openPost"
                @toggle-follow="handleToggleFollow"
              />
            </div>
            <div v-if="followingPostsTotal > 15" class="pagination-row">
              <button class="outline-btn" type="button" :disabled="followingPage === 1" @click="loadFollowingPosts(followingPage - 1)">이전</button>
              <span>{{ followingPage }} / {{ Math.ceil(followingPostsTotal / 15) }}</span>
              <button class="outline-btn" type="button" :disabled="followingPage * 15 >= followingPostsTotal" @click="loadFollowingPosts(followingPage + 1)">다음</button>
            </div>
          </template>

          <template v-else>
            <div v-if="communityLoading" class="community-loading">게시글을 불러오는 중입니다.</div>
            <div v-else-if="communityError" class="error-banner">{{ communityError }}</div>
            <div v-else-if="communityPosts.length === 0" class="community-empty">
              <p>아직 게시글이 없습니다.</p>
              <button v-if="authUser" class="primary-btn" type="button" @click="openWrite">첫 글 작성하기</button>
            </div>

            <div class="community-post-grid">
              <CommunityPostCard
                v-for="post in communityPosts"
                :key="post.id"
                :post="post"
                :auth-user="authUser"
                :format-relative-time="formatRelativeTime"
                @open="openPost"
                @toggle-follow="handleToggleFollow"
              />
            </div>

            <div v-if="communityTotal > 15" class="pagination-row">
              <button class="outline-btn" type="button" :disabled="communityPage === 1" @click="loadPosts(communityPage - 1)">이전</button>
              <span>{{ communityPage }} / {{ Math.ceil(communityTotal / 15) }}</span>
              <button class="outline-btn" type="button" :disabled="communityPage * 15 >= communityTotal" @click="loadPosts(communityPage + 1)">다음</button>
            </div>
          </template>
        </section>
      </template>
    </template>

    <template v-else-if="communityView === 'detail' && communityPost">
      <section class="panel community-detail-wide">
        <div class="post-detail-nav">
          <button class="back-btn" type="button" @click="communityView = 'list'">← 목록</button>
          <span class="category-tag">{{ communityPost.category_label }}</span>
        </div>
        <h2 class="post-detail-title">{{ communityPost.title }}</h2>
        <div class="post-detail-meta">
          <div class="post-detail-author-row">
            <div class="post-avatar">{{ communityPost.author[0] }}</div>
            <span class="post-detail-author-name">{{ communityPost.author }}</span>
            <button
              v-if="authUser && !communityPost.is_owner"
              :class="['follow-btn-sm', communityPost.is_following_author ? 'following' : '']"
              type="button"
              @click="handleToggleFollow(communityPost.author_id)"
            >
              {{ communityPost.is_following_author ? '팔로잉' : '+ 팔로우' }}
            </button>
          </div>
          <span>{{ formatRelativeTime(communityPost.created_at) }}</span>
          <span v-if="communityPost.mountain">⛰ {{ communityPost.mountain }}</span>
          <span>조회 {{ communityPost.view_count }}</span>
        </div>
        <div class="post-detail-content">{{ communityPost.content }}</div>
        <div class="post-detail-actions">
          <button :class="['like-btn', { liked: communityPost.is_liked }]" type="button" @click="toggleLike">
            👍 좋아요 {{ communityPost.like_count }}
          </button>
          <template v-if="communityPost.is_owner">
            <button class="outline-btn" type="button" @click="openEdit">수정</button>
            <button class="outline-btn danger" type="button" @click="removePost">삭제</button>
          </template>
        </div>

        <div class="comments-section">
          <h3>댓글 {{ communityPost.comments?.length ?? 0 }}개</h3>
          <div v-for="c in communityPost.comments" :key="c.id" class="comment-item">
            <div class="comment-header">
              <span class="comment-author">{{ c.author }}</span>
              <span class="comment-time">{{ formatRelativeTime(c.created_at) }}</span>
              <button v-if="c.is_owner" class="comment-delete" type="button" @click="removeComment(c.id)">삭제</button>
            </div>
            <p class="comment-content">{{ c.content }}</p>
          </div>
          <div v-if="authUser" class="comment-form">
            <textarea v-model="communityCommentInput" placeholder="댓글을 입력하세요..." rows="2"></textarea>
            <button class="primary-btn" type="button" :disabled="!communityCommentInput.trim()" @click="submitComment">댓글 쓰기</button>
          </div>
          <div v-else class="comment-login-prompt">
            <button class="outline-btn" type="button" @click="showAuthModal = true">로그인 후 댓글 작성</button>
          </div>
        </div>
      </section>
    </template>

    <template v-else-if="communityView === 'write' || communityView === 'edit'">
      <section class="panel community-detail-wide">
        <div class="section-title">
          <div>
            <p class="eyebrow">{{ communityView === 'edit' ? 'EDIT' : 'WRITE' }}</p>
            <h2>{{ communityView === 'edit' ? '게시글 수정' : '게시글 작성' }}</h2>
          </div>
          <button class="outline-btn" type="button" @click="communityView = communityPost ? 'detail' : 'list'">취소</button>
        </div>
        <div v-if="writeError" class="error-banner" role="alert">{{ writeError }}</div>
        <form class="write-form" @submit.prevent="submitWrite">
          <label class="field">
            <span>카테고리</span>
            <select v-model="writeForm.category">
              <option value="review">등산 후기</option>
              <option value="question">질문</option>
              <option value="safety">안전 제보</option>
              <option value="general">자유게시판</option>
            </select>
          </label>
          <label class="field">
            <span>관련 산 (선택)</span>
            <input v-model="writeForm.mountain" type="text" placeholder="예: 북한산" />
          </label>
          <label class="field wide-field">
            <span>제목</span>
            <input v-model="writeForm.title" type="text" placeholder="제목을 입력하세요" required />
          </label>
          <label class="field wide-field">
            <span>내용</span>
            <textarea v-model="writeForm.content" placeholder="내용을 입력하세요" rows="8" required></textarea>
          </label>
          <button class="primary-btn wide-field" type="submit" :disabled="writeLoading">
            {{ writeLoading ? '저장 중' : (communityView === 'edit' ? '수정 완료' : '게시하기') }}
          </button>
        </form>
      </section>
    </template>
  </section>
</template>

<script setup>
import { defineComponent, h, onMounted, ref } from 'vue';
import { authUser, showAuthModal } from '../composables/useAuth.js';
import {
  activeInfoPost,
  communityCategory, communityCommentInput, communityError, communityLoading,
  communityPage, communityPost, communityPosts, communitySearch, communityTotal,
  communityView, filterCategory, formatRelativeTime, loadPosts, openEdit,
  openPost, openWrite, removeComment, removePost, submitComment, submitWrite,
  toggleLike, writeError, writeForm, writeLoading,
  followingPosts, followingPostsLoading, followingPostsTotal, loadFollowingPosts, toggleFollow,
  followingList, loadFollowingList,
} from '../composables/useCommunity.js';
import { heroThemeSlides } from '../data/heroCuration.js';

const followingPage = ref(1);
const followingMenuOpen = ref(false);

const vClickOutside = {
  mounted(el, binding) {
    el._clickOutside = (e) => { if (!el.contains(e.target)) binding.value(e); };
    document.addEventListener('click', el._clickOutside);
  },
  unmounted(el) {
    document.removeEventListener('click', el._clickOutside);
  },
};

const CommunityPostCard = defineComponent({
  name: 'CommunityPostCard',
  props: {
    post: { type: Object, required: true },
    authUser: { type: Object, default: null },
    formatRelativeTime: { type: Function, required: true },
  },
  emits: ['open', 'toggle-follow'],
  setup(props, { emit }) {
    return () => h('article', {
      class: 'community-post-modern',
      onClick: () => emit('open', props.post.id),
    }, [
      h('div', { class: 'post-header' }, [
        h('div', { class: 'post-avatar' }, props.post.author?.[0] || '?'),
        h('div', { class: 'post-meta' }, [
          h('div', { class: 'post-meta-author-row' }, [
            h('strong', props.post.author),
            props.authUser && !props.post.is_owner
              ? h('button', {
                class: ['follow-tag', props.post.is_following_author ? 'following' : ''],
                type: 'button',
                onClick: (event) => {
                  event.stopPropagation();
                  emit('toggle-follow', props.post.author_id);
                },
              }, props.post.is_following_author ? '팔로잉' : '팔로우')
              : null,
          ]),
          h('span', [
            props.formatRelativeTime(props.post.created_at),
            ' · ',
            h('span', { class: 'category-tag' }, props.post.category_label),
          ]),
        ]),
        props.post.mountain ? h('span', { class: 'post-mountain' }, `⛰ ${props.post.mountain}`) : null,
      ]),
      h('div', { class: 'post-content' }, [
        h('strong', props.post.title),
        h('p', props.post.content?.length > 120 ? `${props.post.content.slice(0, 120)}...` : props.post.content),
      ]),
      h('div', { class: 'post-actions' }, [
        h('span', `👍 ${props.post.like_count}`),
        h('span', `💬 ${props.post.comment_count}`),
        h('span', `👀 ${props.post.view_count}`),
      ]),
    ]);
  },
});

function cleanTag(tag) {
  return String(tag || '').replace(/^#/, '');
}

function formatMountainTags(value) {
  return String(value || '')
    .split(/\s*[·ㆍ•,]\s*/)
    .map((item) => item.trim().replace(/^#/, ''))
    .filter(Boolean)
    .map((item) => `#${item}`)
    .join(' ');
}

async function toggleFollowingMenu() {
  followingMenuOpen.value = !followingMenuOpen.value;
  if (followingMenuOpen.value) await loadFollowingList();
}

async function handleToggleFollow(authorId) {
  const data = await toggleFollow(authorId);
  if (data && !data.is_following && communityCategory.value === 'following') {
    await loadFollowingPosts(followingPage.value);
  }
}

async function handleUnfollow(userId) {
  await toggleFollow(userId);
  await loadFollowingList();
}

onMounted(() => {
  if (communityPosts.value.length === 0) loadPosts();
  if (authUser.value) loadFollowingList();
});
</script>
