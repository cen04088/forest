import { reactive, ref } from 'vue';

// ── 전역 공유 상태 (탭 간 공유) ────────────────────────────────────────────

export const authToken = ref(localStorage.getItem('auth_token') || '');
export const authUser = ref(null);
export const showAuthModal = ref(false);

export const selectedCourse = ref(null);
export const weatherData = ref(null);
export const favorites = ref([]);
export const hikingRecords = ref([]);
export const emergencyContacts = ref([]);

export const profile = reactive({
  mountainName: '',
  departureDate: '',
  departureTime: '',
  availableMinutes: 240,
  desiredHikingMinutes: 120,
  experience: 'beginner',
  purpose: 'balanced',
  transport: 'public',
  maxDistanceKm: 30,
});

export const globalError = ref('');
