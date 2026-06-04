import { reactive, ref } from 'vue';
import { apiLogin, apiLogout, apiMe, apiRegister } from '../api.js';

// ── 싱글톤 모듈 수준 상태 ────────────────────────────────────────────────────
export const authToken = ref(localStorage.getItem('auth_token') || '');
export const authUser = ref(null);
export const showAuthModal = ref(false);
export const authMode = ref('login');
export const authForm = reactive({ username: '', password: '', nickname: '', email: '' });
export const authLoading = ref(false);
export const authError = ref('');

export async function loadMe() {
  if (!authToken.value) return;
  try {
    const data = await apiMe(authToken.value);
    authUser.value = data.user;
    if (!data.user) {
      authToken.value = '';
      localStorage.removeItem('auth_token');
    }
  } catch {
    authToken.value = '';
    localStorage.removeItem('auth_token');
  }
}

export async function login(onSuccess) {
  authLoading.value = true;
  authError.value = '';
  try {
    const data = await apiLogin({ username: authForm.username, password: authForm.password });
    authToken.value = data.token;
    authUser.value = data.user;
    localStorage.setItem('auth_token', data.token);
    showAuthModal.value = false;
    authForm.username = '';
    authForm.password = '';
    if (onSuccess) onSuccess();
  } catch (err) {
    authError.value = err.message;
  } finally {
    authLoading.value = false;
  }
}

export async function register(onSuccess) {
  authLoading.value = true;
  authError.value = '';
  try {
    const data = await apiRegister({
      username: authForm.username,
      password: authForm.password,
      nickname: authForm.nickname,
      email: authForm.email,
    });
    authToken.value = data.token;
    authUser.value = data.user;
    localStorage.setItem('auth_token', data.token);
    showAuthModal.value = false;
    authForm.username = '';
    authForm.password = '';
    authForm.nickname = '';
    authForm.email = '';
    if (onSuccess) onSuccess();
  } catch (err) {
    authError.value = err.message;
  } finally {
    authLoading.value = false;
  }
}

export async function logout(onDone) {
  await apiLogout(authToken.value).catch(() => {});
  authToken.value = '';
  authUser.value = null;
  localStorage.removeItem('auth_token');
  showAuthModal.value = false;
  if (onDone) onDone();
}
