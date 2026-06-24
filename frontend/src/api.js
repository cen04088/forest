const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch (networkErr) {
    throw new Error(`네트워크 연결 오류: ${networkErr.message}`);
  }

  if (!response.ok) {
    let msg = `오류 ${response.status} (${path.split('?')[0]})`;
    try {
      const data = await response.json();
      msg = data.error || data.detail || msg;
    } catch {}
    console.error('[API]', response.status, path, msg);
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

export async function fetchPosts({ category = "", mountain = "", search = "", page = 1 } = {}, token) {
  const params = new URLSearchParams({ category, mountain, search, page });
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

export async function fetchMountains() {
  return request("/mountains/");
}

export async function fetchMountainRecommendations(payload) {
  return request("/recommend-mountains/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchWeather(location) {
  const lat = location?.lat ?? 37.5665;
  const lng = location?.lng ?? 126.978;
  const params = new URLSearchParams({ lat, lng });
  if (location?.mountain) params.set('mountain', location.mountain);
  return request(`/weather/?${params.toString()}`);
}

export async function fetchForestFlux({ mountain = "", lat, lng } = {}) {
  const params = new URLSearchParams();
  if (mountain) params.set("mountain", mountain);
  if (lat != null) params.set("lat", lat);
  if (lng != null) params.set("lng", lng);
  return request(`/forest-flux/?${params.toString()}`);
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

export async function fetchOSMTrails({ lat, lng, mountainName = "", radius = 3000 } = {}) {
  const params = new URLSearchParams({ lat, lng, mountain: mountainName, radius });
  return request(`/osm-trails/?${params.toString()}`);
}

export async function fetchVWorldTrails({ mountainName = "", lat, lng, radius = 5 } = {}) {
  const params = new URLSearchParams({ mountain: mountainName || "", radius });
  if (lat !== undefined && lng !== undefined) {
    params.set("lat", lat);
    params.set("lng", lng);
  }
  return request(`/vworld-trails/?${params.toString()}`);
}

export async function fetchLocalRoadTrails({ mountainName = "", lat, lng, radius = 8, size = 80 } = {}) {
  const params = new URLSearchParams({ mountain: mountainName || "", radius, size });
  if (lat !== undefined && lng !== undefined) {
    params.set("lat", lat);
    params.set("lng", lng);
  }
  return request(`/local-road-trails/?${params.toString()}`);
}

export async function fetchSafetyReports(mountainName) {
  const params = new URLSearchParams({ mountain: mountainName || "" });
  return request(`/safety-reports/?${params.toString()}`);
}

export async function fetchMountainStory(mountainName) {
  const params = new URLSearchParams({ mountain: mountainName || "" });
  return request(`/mountain-story/?${params.toString()}`);
}

export async function fetchLikedPosts(token) {
  return request("/liked-posts/", { headers: authHeaders(token) });
}

export async function fetchDisasterZones(mountainName) {
  const params = new URLSearchParams({ mountain: mountainName || "" });
  return request(`/disaster-zones/?${params.toString()}`);
}

export async function fetchLandslide(region) {
  const params = new URLSearchParams({ sgg: region || "" });
  return request(`/landslide-prediction/?${params.toString()}`);
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

export async function getSafeLinkByCode(code) {
  const params = new URLSearchParams({ code: code.toUpperCase().trim() });
  return request(`/safe-links/by-code/?${params}`);
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

// ── 내 활동 ───────────────────────────────────────────────────────────────────

export async function fetchMyPosts(token, page = 1) {
  return request(`/my-posts/?page=${page}`, { headers: authHeaders(token) });
}

// ── 산행 기록 ─────────────────────────────────────────────────────────────────

export async function fetchHikingRecords(token) {
  return request("/hiking-records/", { headers: authHeaders(token) });
}

export async function createHikingRecord(data, token) {
  return request("/hiking-records/", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
}

export async function deleteHikingRecord(id, token) {
  return request(`/hiking-records/${id}/`, { method: "DELETE", headers: authHeaders(token) });
}

// ── 즐겨찾기 ──────────────────────────────────────────────────────────────────

export async function fetchFavorites(token) {
  return request("/favorites/", { headers: authHeaders(token) });
}

export async function addFavorite(data, token) {
  return request("/favorites/", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
}

export async function removeFavorite(courseId, token) {
  return request(`/favorites/${encodeURIComponent(courseId)}/`, { method: "DELETE", headers: authHeaders(token) });
}

// ── 긴급 연락처 ───────────────────────────────────────────────────────────────

export async function fetchEmergencyContacts(token) {
  return request("/emergency-contacts/", { headers: authHeaders(token) });
}

export async function addEmergencyContact(data, token) {
  return request("/emergency-contacts/", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(data),
  });
}

export async function removeEmergencyContact(id, token) {
  return request(`/emergency-contacts/${id}/`, { method: "DELETE", headers: authHeaders(token) });
}

// ── AI ────────────────────────────────────────────────────────────────────────

export async function fetchChatResponse({ messages, context }) {
  return request("/chat/", {
    method: "POST",
    body: JSON.stringify({ messages, context }),
  });
}

export async function fetchSafetyAdvice({ mountain, weather, profile, sunTimes }) {
  return request("/safety-advice/", {
    method: "POST",
    body: JSON.stringify({ mountain, weather, profile, sun_times: sunTimes }),
  });
}

export async function fetchMountainIntro({ name, summary, selectionReason }) {
  return request("/mountain-intro/", {
    method: "POST",
    body: JSON.stringify({ name, summary, selection_reason: selectionReason }),
  });
}
