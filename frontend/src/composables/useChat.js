import { ref } from 'vue';
import { fetchChatResponse } from '../api.js';
import { selectedMountain, weatherData, recommendations } from './useGuide.js';

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

  const context = {
    mountain: selectedMountain.value || null,
    weather: weatherData.value || null,
    recommendedCourses: recommendations.value?.slice(0, 3) || [],
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
