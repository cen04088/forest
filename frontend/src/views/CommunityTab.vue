<template>
  <section class="screen-stack">

    <!-- ── 목록 뷰 ── -->
    <template v-if="communityView === 'list'">

      <!-- ── 에디터 정보글 섹션 ── -->
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
              :style="{ backgroundImage: `linear-gradient(to top, rgba(0,0,0,0.82) 0%, rgba(0,0,0,0.28) 55%, rgba(0,0,0,0.06) 100%), url('${slide.image}')` }"
              @click="activeInfoPost = slide.id"
            >
              <div class="info-mag-card-inner">
                <div class="info-mag-card-top">
                  <span class="info-mag-num">{{ String(idx + 1).padStart(2, '0') }}</span>
                  <span class="info-mag-badge">{{ slide.infoPost.label }}</span>
                  <span class="info-mag-readtime">{{ slide.infoPost.readTime }}</span>
                </div>
                <div class="info-mag-card-bottom">
                  <p class="info-mag-mountain">{{ slide.infoPost.mountain }}</p>
                  <strong class="info-mag-title">{{ slide.infoPost.title }}</strong>
                  <div class="info-mag-tags">
                    <span v-for="tag in slide.infoPost.tags.slice(0, 3)" :key="tag" class="info-mag-tag">{{ tag }}</span>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </section>
      </template>

      <!-- ── 정보글 상세 뷰 ── -->
      <template v-else>
        <section class="info-detail-section">
          <button class="info-detail-back" type="button" @click="activeInfoPost = null">← 목록으로</button>
          <template v-for="slide in heroThemeSlides" :key="slide.id">
            <template v-if="slide.id === activeInfoPost">
              <div
                class="info-detail-hero"
                :style="{ backgroundImage: `linear-gradient(to top, rgba(0,0,0,0.88) 0%, rgba(0,0,0,0.3) 60%, transparent 100%), url('${slide.image}')` }"
              >
                <span class="info-detail-badge">{{ slide.infoPost.label }}</span>
                <h1 class="info-detail-title">{{ slide.infoPost.title }}</h1>
                <p class="info-detail-mountain">{{ slide.infoPost.mountain }}</p>
              </div>
              <div class="info-detail-body">
                <p
                  v-for="(para, i) in slide.infoPost.content.split('\n\n')"
                  :key="i"
                  class="info-detail-para"
                >{{ para }}</p>
                <div class="info-detail-tags">
                  <span v-for="tag in slide.infoPost.tags" :key="tag" class="info-mag-tag">{{ tag }}</span>
                </div>
              </div>
            </template>
          </template>
        </section>
      </template>

      <section class="panel community-feed">
        <div class="section-title compact">
          <div>
            <p class="eyebrow">Community</p>
            <h2>동반 산행 커뮤니티</h2>
          </div>
          <div class="community-header-actions">
            <!-- 팔로잉 목록 -->
            <div v-if="authUser" class="following-menu-wrap" v-click-outside="() => followingMenuOpen = false">
              <button
                type="button"
                class="following-menu-btn"
                @click="toggleFollowingMenu"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="15" height="15"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
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
            <!-- 글쓰기 버튼 -->
            <button v-if="authUser" class="write-btn" type="button" @click="openWrite">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              글쓰기
            </button>
            <button v-else class="write-btn write-btn-ghost" type="button" @click="showAuthModal = true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              글쓰기
            </button>
          </div>
        </div>

        <div class="community-search-row">
          <input
            v-model="communitySearch"
            type="search"
            placeholder="제목·내용 검색…"
            class="community-search-input"
            @keydown.enter="loadPosts(1)"
          />
          <button class="outline-btn" type="button" @click="loadPosts(1)">검색</button>
        </div>
        <div class="filter-row">
          <button :class="{ active: communityCategory === '' }" type="button" @click="filterCategory('')">전체</button>
          <button :class="{ active: communityCategory === 'review' }" type="button" @click="filterCategory('review')">등산 후기</button>
          <button :class="{ active: communityCategory === 'question' }" type="button" @click="filterCategory('question')">질문</button>
          <button :class="{ active: communityCategory === 'safety' }" type="button" @click="filterCategory('safety')">안전 제보</button>
          <button :class="{ active: communityCategory === 'general' }" type="button" @click="filterCategory('general')">자유</button>
          <button v-if="authUser" :class="['follow-feed-btn', { active: communityCategory === 'following' }]" type="button" @click="filterCategory('following')">👥 팔로우</button>
        </div>

        <!-- 팔로우 피드 -->
        <template v-if="communityCategory === 'following'">
          <div v-if="followingPostsLoading" class="community-loading">게시글을 불러오는 중입니다…</div>
          <div v-else-if="followingPosts.length === 0" class="community-empty">
            <p>팔로우한 사람의 게시글이 없습니다.</p>
            <p style="font-size:13px;color:var(--muted);margin-top:6px">게시글 상세에서 작성자를 팔로우해 보세요.</p>
          </div>
          <div v-else class="community-post-grid">
            <article
              v-for="post in followingPosts"
              :key="post.id"
              class="community-post-modern"
              style="cursor:pointer"
              @click="openPost(post.id)"
            >
              <div class="post-header">
                <div class="post-avatar">{{ post.author[0] }}</div>
                <div class="post-meta">
                  <div class="post-meta-author-row">
                    <strong>{{ post.author }}</strong>
                    <button class="follow-tag following" type="button" @click.stop="handleToggleFollow(post.author_id)">팔로잉</button>
                  </div>
                  <span>{{ formatRelativeTime(post.created_at) }} · <span class="category-tag">{{ post.category_label }}</span></span>
                </div>
                <span v-if="post.mountain" class="post-mountain">⛰️ {{ post.mountain }}</span>
              </div>
              <div class="post-content">
                <strong>{{ post.title }}</strong>
                <p>{{ post.content.length > 120 ? post.content.slice(0, 120) + '…' : post.content }}</p>
              </div>
              <div class="post-actions">
                <span>👍 {{ post.like_count }}</span>
                <span>💬 {{ post.comment_count }}</span>
                <span>👀 {{ post.view_count }}</span>
              </div>
            </article>
          </div>
          <div v-if="followingPostsTotal > 15" class="pagination-row">
            <button class="outline-btn" type="button" :disabled="followingPage === 1" @click="loadFollowingPosts(followingPage - 1)">이전</button>
            <span>{{ followingPage }} / {{ Math.ceil(followingPostsTotal / 15) }}</span>
            <button class="outline-btn" type="button" :disabled="followingPage * 15 >= followingPostsTotal" @click="loadFollowingPosts(followingPage + 1)">다음</button>
          </div>
        </template>

        <!-- 일반 피드 -->
        <template v-else>
          <div v-if="communityLoading" class="community-loading">게시글을 불러오는 중입니다…</div>
          <div v-else-if="communityError" class="error-banner">{{ communityError }}</div>
          <div v-else-if="communityPosts.length === 0" class="community-empty">
            <p>아직 게시글이 없습니다.</p>
            <button v-if="authUser" class="primary-btn" type="button" @click="openWrite">첫 글 작성하기</button>
          </div>

          <div class="community-post-grid">
            <article
              v-for="post in communityPosts"
              :key="post.id"
              class="community-post-modern"
              style="cursor:pointer"
              @click="openPost(post.id)"
            >
              <div class="post-header">
                <div class="post-avatar">{{ post.author[0] }}</div>
                <div class="post-meta">
                  <div class="post-meta-author-row">
                    <strong>{{ post.author }}</strong>
                    <button
                      v-if="authUser && !post.is_owner"
                      :class="['follow-tag', post.is_following_author ? 'following' : '']"
                      type="button"
                      @click.stop="handleToggleFollow(post.author_id)"
                    >{{ post.is_following_author ? '팔로잉' : '팔로우' }}</button>
                  </div>
                  <span>{{ formatRelativeTime(post.created_at) }} · <span class="category-tag">{{ post.category_label }}</span></span>
                </div>
                <span v-if="post.mountain" class="post-mountain">⛰️ {{ post.mountain }}</span>
              </div>
              <div class="post-content">
                <strong>{{ post.title }}</strong>
                <p>{{ post.content.length > 120 ? post.content.slice(0, 120) + '…' : post.content }}</p>
              </div>
              <div class="post-actions">
                <span>👍 {{ post.like_count }}</span>
                <span>💬 {{ post.comment_count }}</span>
                <span>👀 {{ post.view_count }}</span>
              </div>
            </article>
          </div>

          <div v-if="communityTotal > 15" class="pagination-row">
            <button class="outline-btn" type="button" :disabled="communityPage === 1" @click="loadPosts(communityPage - 1)">이전</button>
            <span>{{ communityPage }} / {{ Math.ceil(communityTotal / 15) }}</span>
            <button class="outline-btn" type="button" :disabled="communityPage * 15 >= communityTotal" @click="loadPosts(communityPage + 1)">다음</button>
          </div>
        </template>
      </section>
    </template>

    <!-- ── 상세 뷰 ── -->
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
            >{{ communityPost.is_following_author ? '팔로잉 ✓' : '+ 팔로우' }}</button>
          </div>
          <span>{{ formatRelativeTime(communityPost.created_at) }}</span>
          <span v-if="communityPost.mountain">⛰️ {{ communityPost.mountain }}</span>
          <span>👀 {{ communityPost.view_count }}</span>
        </div>
        <div class="post-detail-content">{{ communityPost.content }}</div>
        <div class="post-detail-actions">
          <button :class="['like-btn', { liked: communityPost.is_liked }]" type="button" @click="toggleLike">
            👍 {{ communityPost.is_liked ? '좋아요 취소' : '좋아요' }} {{ communityPost.like_count }}
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
            <textarea v-model="communityCommentInput" placeholder="댓글을 입력하세요…" rows="2"></textarea>
            <button class="primary-btn" type="button" :disabled="!communityCommentInput.trim()" @click="submitComment">댓글 달기</button>
          </div>
          <div v-else class="comment-login-prompt">
            <button class="outline-btn" type="button" @click="showAuthModal = true">로그인 후 댓글 작성</button>
          </div>
        </div>
      </section>
    </template>

    <!-- ── 작성/수정 뷰 ── -->
    <template v-else-if="communityView === 'write' || communityView === 'edit'">
      <section class="panel community-detail-wide">
        <div class="section-title">
          <div>
            <p class="eyebrow">{{ communityView === 'edit' ? 'Edit' : 'Write' }}</p>
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
            {{ writeLoading ? '저장 중…' : (communityView === 'edit' ? '수정 완료' : '게시하기') }}
          </button>
        </form>
      </section>
    </template>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue';
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

// v-click-outside 디렉티브
const vClickOutside = {
  mounted(el, binding) {
    el._clickOutside = (e) => { if (!el.contains(e.target)) binding.value(e); };
    document.addEventListener('click', el._clickOutside);
  },
  unmounted(el) { document.removeEventListener('click', el._clickOutside); },
};

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
}

onMounted(() => {
  if (communityPosts.value.length === 0) loadPosts();
  if (authUser.value) loadFollowingList();
});
</script>
