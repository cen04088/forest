const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    // 인증/커뮤니티 오류는 서버 메시지를 그대로 던짐
    let msg = "데이터를 불러오지 못했습니다.";
    try { msg = (await response.json()).error || msg; } catch {}
    throw new Error(msg);
  }

  return response.json();
}

function authHeaders(token) {
  return token ? { "Content-Type": "application/json", "X-Auth-Token": token } : { "Content-Type": "application/json" };
}

// ── 인증 ─────────────────────────────────────────────────────────────────────

export async function apiRegister({ username, password, nickname, email }) {
  return request("/auth/register/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, nickname, email }),
  });
}

export async function apiLogin({ username, password }) {
  return request("/auth/login/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
}

export async function apiLogout(token) {
  return request("/auth/logout/", { method: "POST", headers: authHeaders(token) });
}

export async function apiMe(token) {
  return request("/auth/me/", { headers: authHeaders(token) });
}

// ── 커뮤니티 ──────────────────────────────────────────────────────────────────

export async function fetchPosts({ category = "", mountain = "", page = 1 } = {}, token) {
  const params = new URLSearchParams({ category, mountain, page });
  return request(`/posts/?${params}`, { headers: authHeaders(token) });
}

export async function fetchPost(id, token) {
  return request(`/posts/${id}/`, { headers: authHeaders(token) });
}

export async function createPost(data, token) {
  return request("/posts/", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
}

export async function updatePost(id, data, token) {
  return request(`/posts/${id}/`, {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
}

export async function deletePost(id, token) {
  return request(`/posts/${id}/`, { method: "DELETE", headers: authHeaders(token) });
}

export async function likePost(id, token) {
  return request(`/posts/${id}/like/`, { method: "POST", headers: authHeaders(token) });
}

export async function createComment(postId, content, token) {
  return request(`/posts/${postId}/comments/`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ content }),
  });
}

export async function deleteComment(id, token) {
  return request(`/comments/${id}/`, { method: "DELETE", headers: authHeaders(token) });
}

export async function fetchCourses() {
  return request("/courses/");
}

export async function fetchDataSources() {
  return request("/data-sources/");
}

export async function fetchWeather(location) {
  const lat = location?.lat ?? 37.5665;
  const lng = location?.lng ?? 126.978;
  const params = new URLSearchParams({ lat, lng });
  return request(`/weather/?${params.toString()}`);
}

export async function fetchMountainWeather({ mountainName = "", mountainNum = "" } = {}) {
  const params = new URLSearchParams({ mountain: mountainName || "" });
  if (mountainNum) {
    params.set("mountainNum", mountainNum);
  }
  return request(`/mountain-weather/?${params.toString()}`);
}

export async function fetchForestSpatial(mountainName) {
  const params = new URLSearchParams({ mountain: mountainName || "" });
  return request(`/forest-spatial/?${params.toString()}`);
}

export async function fetchVWorldTrails({ mountainName = "", lat, lng, radius = 5 } = {}) {
  const params = new URLSearchParams({ mountain: mountainName || "", radius });
  if (lat !== undefined && lng !== undefined) {
    params.set("lat", lat);
    params.set("lng", lng);
  }
  return request(`/vworld-trails/?${params.toString()}`);
}

export async function fetchMountainStory(mountainName) {
  const params = new URLSearchParams({ mountain: mountainName || "" });
  return request(`/mountain-story/?${params.toString()}`);
}

export async function fetchLandslide(sgg) {
  const params = new URLSearchParams({ sgg: sgg || "" });
  return request(`/landslide/?${params.toString()}`);
}

export async function fetchRecommendations(payload) {
  return request("/recommendations/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchDisasterZones(mountainName) {
  const params = new URLSearchParams({ mountain: mountainName || "" });
  return request(`/disaster-zones/?${params.toString()}`);
}

export async function createSafeLink(course) {
  return request("/safe-links/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ course }),
  });
}

export async function getSafeLink(id) {
  return request(`/safe-links/${id}/`);
}

export async function updateSafeLinkLocation(id, lat, lng) {
  return request(`/safe-links/${id}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat, lng }),
  });
}

export async function endSafeLink(id) {
  return request(`/safe-links/${id}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "end" }),
  });
}
