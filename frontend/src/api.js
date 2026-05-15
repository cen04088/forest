const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    throw new Error("데이터를 불러오지 못했습니다.");
  }

  return response.json();
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
