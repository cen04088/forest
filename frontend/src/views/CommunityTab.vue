<template>
  <section class="screen-stack">

    <!-- ── 목록 뷰 ── -->
    <template v-if="communityView === 'list'">
      <section class="panel community-feed">
        <div class="section-title compact">
          <div>
            <p class="eyebrow">Community</p>
            <h2>동반 산행 커뮤니티</h2>
          </div>
          <button v-if="authUser" class="primary-btn" type="button" @click="openWrite">글쓰기</button>
          <button v-else class="outline-btn" type="button" @click="showAuthModal = true">로그인 후 글쓰기</button>
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
        </div>

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
              <strong>{{ post.author }}</strong>
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
        </div><!-- /community-post-grid -->

        <div v-if="communityTotal > 15" class="pagination-row">
          <button class="outline-btn" type="button" :disabled="communityPage === 1" @click="loadPosts(communityPage - 1)">이전</button>
          <span>{{ communityPage }} / {{ Math.ceil(communityTotal / 15) }}</span>
          <button class="outline-btn" type="button" :disabled="communityPage * 15 >= communityTotal" @click="loadPosts(communityPage + 1)">다음</button>
        </div>
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
          <span>{{ communityPost.author }}</span>
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
import { onMounted } from 'vue';
import { authUser, showAuthModal } from '../composables/useAuth.js';
import {
  communityCategory, communityCommentInput, communityError, communityLoading,
  communityPage, communityPost, communityPosts, communitySearch, communityTotal,
  communityView, filterCategory, formatRelativeTime, loadPosts, openEdit,
  openPost, openWrite, removeComment, removePost, submitComment, submitWrite,
  toggleLike, writeError, writeForm, writeLoading,
} from '../composables/useCommunity.js';

onMounted(() => {
  if (communityPosts.value.length === 0) loadPosts();
});
</script>
