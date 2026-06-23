import { ref } from 'vue';
import { fetchChatResponse } from '../api.js';
import { selectedMountain, weatherData, recommendations, profile, disasterZones } from './useGuide.js';

export const chatMessages = ref([]); // { role: 'user'|'assistant', content: string }
export const chatLoading = ref(false);
export const chatError = ref('');

export const SUGGESTED = [
  '지금 이 산 가도 괜찮을까요?',
  '초보자가 가기 좋은 코스는?',
  '등산 중 갑자기 비가 오면 어떻게 해야 하나요?',
  '산행 전 챙겨야 할 필수 장비는?',
];

export async function sendMessage(text) {
  if (!text.trim() || chatLoading.value) return;

  chatMessages.value.push({ role: 'user', content: text.trim() });
  chatLoading.value = true;
  chatError.value = '';

  // API 형식: { role: 'user'|'assistant', content: string }
  const messages = chatMessages.value.map((m) => ({
    role: m.role === 'assistant' ? 'assistant' : 'user',
    content: m.content,
  }));

  const now = new Date();
  const DAYS = ['일', '월', '화', '수', '목', '금', '토'];
  const p = profile;

  const context = {
    mountain: selectedMountain.value || null,
    weather: weatherData.value || null,
    recommendedCourses: recommendations.value?.slice(0, 3) || [],
    now: `${now.getFullYear()}년 ${now.getMonth() + 1}월 ${now.getDate()}일 (${DAYS[now.getDay()]}) ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`,
    userProfile: {
      experience: p.experience,
      companion: p.companion,
      availableMinutes: p.availableMinutes,
      desiredHikingMinutes: p.desiredHikingMinutes,
      departureTime: p.departureTime,
      departureDate: p.departureDate,
      maxDistanceKm: p.maxDistanceKm,
      intensity: p.intensity,
      isDefault: (
        p.experience === 'beginner' &&
        p.companion === 'solo' &&
        p.availableMinutes === 240 &&
        p.intensity === 'moderate'
      ),
    },
    disasterZones: (disasterZones.value || []).slice(0, 5).map((z) => ({
      district: z.district,
      location: z.location,
      risk_factor: z.risk_factor,
    })),
    sunTimes: weatherData.value
      ? { sunrise: weatherData.value.sunrise, sunset: weatherData.value.sunset }
      : null,
  };

  try {
    const data = await fetchChatResponse({ messages, context });
    chatMessages.value.push({ role: 'assistant', content: data.response });
  } catch (e) {
    chatError.value = '응답을 가져오지 못했습니다. 네트워크를 확인해 주세요.';
    chatMessages.value.pop(); // 보낸 메시지 롤백
  } finally {
    chatLoading.value = false;
  }
}

export function clearChat() {
  chatMessages.value = [];
  chatError.value = '';
}
