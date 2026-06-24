import { reactive, ref } from 'vue';
import {
  createComment, createPost, deleteComment, deletePost,
  fetchPost, fetchPosts, likePost, updatePost, fetchMyPosts, fetchLikedPosts,
  followUser, fetchFollowingPosts,
} from '../api.js';
import { authToken, authUser, showAuthModal } from './useAuth.js';

// ── 싱글톤 상태 ─────────────────────────────────────────────────────────────
export const activeInfoPost = ref(null);
export const communityView = ref('list');
export const communityPosts = ref([]);
export const communityPost = ref(null);
export const communityCategory = ref('');
export const communitySearch = ref('');
export const communityPage = ref(1);
export const communityTotal = ref(0);
export const communityLoading = ref(false);
export const communityError = ref('');
export const communityCommentInput = ref('');
export const writeForm = reactive({ title: '', content: '', category: 'general', mountain: '', course_name: '' });
export const writeError = ref('');
export const writeLoading = ref(false);
export const myPosts = ref([]);
export const myPostsTotal = ref(0);
export const myPostsLoading = ref(false);
export const likedPosts = ref([]);
export const likedPostsLoading = ref(false);
export const followingPosts = ref([]);
export const followingPostsLoading = ref(false);
export const followingPostsTotal = ref(0);

export async function loadPosts(page = 1) {
  communityLoading.value = true;
  communityError.value = '';
  communityPage.value = page;
  try {
    const data = await fetchPosts(
      { category: communityCategory.value, search: communitySearch.value, page },
      authToken.value,
    );
    communityPosts.value = data.posts;
    communityTotal.value = data.total;
  } catch (err) {
    communityError.value = err.message;
  } finally {
    communityLoading.value = false;
  }
}

export async function openPost(id) {
  communityLoading.value = true;
  try {
    communityPost.value = await fetchPost(id, authToken.value);
    communityView.value = 'detail';
  } catch (err) {
    communityError.value = err.message;
  } finally {
    communityLoading.value = false;
  }
}

export function openWrite() {
  Object.assign(writeForm, { title: '', content: '', category: 'general', mountain: '', course_name: '' });
  writeError.value = '';
  communityPost.value = null;
  communityView.value = 'write';
}

export function openEdit() {
  Object.assign(writeForm, {
    title: communityPost.value.title,
    content: communityPost.value.content,
    category: communityPost.value.category,
    mountain: communityPost.value.mountain,
    course_name: communityPost.value.course_name,
  });
  writeError.value = '';
  communityView.value = 'edit';
}

export async function submitWrite() {
  writeLoading.value = true;
  writeError.value = '';
  try {
    if (communityView.value === 'edit') {
      communityPost.value = await updatePost(communityPost.value.id, writeForm, authToken.value);
      communityView.value = 'detail';
    } else {
      const post = await createPost(writeForm, authToken.value);
      await loadPosts();
      communityPost.value = await fetchPost(post.id, authToken.value);
      communityView.value = 'detail';
    }
  } catch (err) {
    writeError.value = err.message;
  } finally {
    writeLoading.value = false;
  }
}

export async function toggleLike() {
  if (!authUser.value) { showAuthModal.value = true; return; }
  try {
    const data = await likePost(communityPost.value.id, authToken.value);
    communityPost.value.is_liked = data.is_liked;
    communityPost.value.like_count = data.like_count;
  } catch (err) {
    communityError.value = err.message || '좋아요 처리에 실패했습니다.';
  }
}

export async function submitComment() {
  if (!communityCommentInput.value.trim()) return;
  try {
    const comment = await createComment(communityPost.value.id, communityCommentInput.value, authToken.value);
    communityPost.value.comments.push(comment);
    communityPost.value.comment_count = (communityPost.value.comment_count || 0) + 1;
    communityCommentInput.value = '';
  } catch (err) {
    communityError.value = err.message || '댓글 작성에 실패했습니다.';
  }
}

export async function removeComment(id) {
  try {
    await deleteComment(id, authToken.value);
    communityPost.value.comments = communityPost.value.comments.filter((c) => c.id !== id);
    communityPost.value.comment_count = Math.max(0, (communityPost.value.comment_count || 1) - 1);
  } catch (err) {
    communityError.value = err.message || '댓글 삭제에 실패했습니다.';
  }
}

export async function removePost() {
  if (!confirm('게시글을 삭제하시겠습니까?')) return;
  try {
    await deletePost(communityPost.value.id, authToken.value);
    communityPost.value = null;
    communityView.value = 'list';
    loadPosts();
  } catch (err) {
    communityError.value = err.message;
  }
}

export function filterCategory(cat) {
  communityCategory.value = cat;
  if (cat === 'following') {
    loadFollowingPosts(1);
  } else {
    loadPosts(1);
  }
}

export async function loadMyPosts() {
  if (!authToken.value) return;
  myPostsLoading.value = true;
  try {
    const data = await fetchMyPosts(authToken.value);
    myPosts.value = data.posts || [];
    myPostsTotal.value = data.total || 0;
  } catch {}
  finally { myPostsLoading.value = false; }
}

export async function loadLikedPosts() {
  if (!authToken.value) return;
  likedPostsLoading.value = true;
  try {
    const data = await fetchLikedPosts(authToken.value);
    likedPosts.value = data.posts || [];
  } catch {}
  finally { likedPostsLoading.value = false; }
}

export async function loadFollowingPosts(page = 1) {
  if (!authToken.value) return;
  followingPostsLoading.value = true;
  try {
    const data = await fetchFollowingPosts(authToken.value, page);
    followingPosts.value = data.posts || [];
    followingPostsTotal.value = data.total || 0;
  } catch {}
  finally { followingPostsLoading.value = false; }
}

export async function toggleFollow(authorId) {
  if (!authUser.value) { showAuthModal.value = true; return; }
  try {
    const data = await followUser(authorId, authToken.value);
    if (communityPost.value && communityPost.value.author_id === authorId) {
      communityPost.value.is_following_author = data.is_following;
    }
    // 목록에서도 반영
    communityPosts.value.forEach(p => {
      if (p.author_id === authorId) p.is_following_author = data.is_following;
    });
    followingPosts.value = followingPosts.value.filter(p => p.author_id !== authorId || data.is_following);
    return data;
  } catch (err) {
    communityError.value = err.message || '팔로우 처리에 실패했습니다.';
  }
}

export function formatRelativeTime(isoString) {
  const diff = Math.floor((Date.now() - new Date(isoString)) / 1000);
  if (diff < 60) return '방금 전';
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  return `${Math.floor(diff / 86400)}일 전`;
}
