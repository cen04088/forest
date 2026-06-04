import { ref } from 'vue';
import {
  addFavorite, addEmergencyContact, createHikingRecord,
  deleteHikingRecord, fetchEmergencyContacts, fetchFavorites,
  fetchHikingRecords, removeFavorite, removeEmergencyContact,
} from '../api.js';
import { authToken, authUser, showAuthModal } from './useAuth.js';

// ── 싱글톤 상태 ─────────────────────────────────────────────────────────────
export const favorites = ref([]);
export const hikingRecords = ref([]);
export const emergencyContacts = ref([]);

export async function loadMyPageData() {
  if (!authToken.value) return;
  const [favsData, recordsData, contactsData] = await Promise.allSettled([
    fetchFavorites(authToken.value),
    fetchHikingRecords(authToken.value),
    fetchEmergencyContacts(authToken.value),
  ]);
  if (favsData.status === 'fulfilled') favorites.value = favsData.value.favorites || [];
  if (recordsData.status === 'fulfilled') hikingRecords.value = recordsData.value.records || [];
  if (contactsData.status === 'fulfilled') emergencyContacts.value = contactsData.value.contacts || [];
}

export async function toggleFavorite(course, onAuthRequired) {
  if (!authUser.value) { showAuthModal.value = true; if (onAuthRequired) onAuthRequired(); return; }
  const isFav = favorites.value.some((f) => f.course_id === course.id);
  if (isFav) {
    await removeFavorite(course.id, authToken.value).catch(() => {});
    favorites.value = favorites.value.filter((f) => f.course_id !== course.id);
  } else {
    await addFavorite({
      course_id: course.id, course_name: course.name, mountain: course.mountain,
      distance_km: course.distance_km, duration_min: course.duration_min, difficulty: course.difficulty,
    }, authToken.value);
    favorites.value.unshift({
      course_id: course.id, course_name: course.name, mountain: course.mountain,
      distance_km: course.distance_km, duration_min: course.duration_min, difficulty: course.difficulty,
    });
  }
}

export async function saveHikingRecord(course, weatherData) {
  if (!authToken.value || !course) return;
  const rec = await createHikingRecord({
    mountain: course.mountain || '',
    course_name: course.name || '',
    hiked_date: new Date().toISOString().slice(0, 10),
    duration_min: course.duration_min || 0,
    weather_summary: weatherData
      ? `${weatherData.temperature_c}°C, 강수 ${weatherData.rainfall_mm}mm` : '',
    safety_label: course.safety_label || '',
  }, authToken.value);
  hikingRecords.value.unshift(rec);
}

export async function removeRecord(id) {
  await deleteHikingRecord(id, authToken.value).catch(() => {});
  hikingRecords.value = hikingRecords.value.filter((r) => r.id !== id);
}

export async function addContact(form) {
  const contact = await addEmergencyContact(form, authToken.value);
  emergencyContacts.value.push(contact);
}

export async function removeContact(id) {
  await removeEmergencyContact(id, authToken.value).catch(() => {});
  emergencyContacts.value = emergencyContacts.value.filter((c) => c.id !== id);
}

export async function removeFav(courseId) {
  await removeFavorite(courseId, authToken.value).catch(() => {});
  favorites.value = favorites.value.filter((f) => f.course_id !== courseId);
}
