/**
 * GPS 위치 감지 Composable
 * 브라우저 Geolocation API를 통해 현재 위치를 받아온다.
 */
import { ref } from 'vue';

export function useLocation(initialLocation = { lat: 37.5665, lng: 126.978 }) {
  const location = ref({ ...initialLocation });
  const gpsStatus = ref('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const gpsError = ref('');

  /**
   * 브라우저 Geolocation API로 현재 위치를 가져온다.
   * @returns {Promise<boolean>} 성공 여부
   */
  async function detectGPS() {
    if (!navigator.geolocation) {
      gpsStatus.value = 'error';
      gpsError.value = '이 브라우저는 위치 서비스를 지원하지 않습니다.';
      return false;
    }

    gpsStatus.value = 'loading';
    gpsError.value = '';

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          location.value = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };
          gpsStatus.value = 'success';
          resolve(true);
        },
        (error) => {
          gpsStatus.value = 'error';
          if (error.code === error.PERMISSION_DENIED) {
            gpsError.value = '위치 권한이 거부되었습니다. 브라우저 주소창 왼쪽 🔒 아이콘에서 허용해주세요.';
          } else if (error.code === error.POSITION_UNAVAILABLE) {
            gpsError.value = '현재 위치를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.';
          } else if (error.code === error.TIMEOUT) {
            gpsError.value = '위치 요청이 시간 초과되었습니다.';
          } else {
            gpsError.value = '위치를 가져오는 중 오류가 발생했습니다.';
          }
          resolve(false);
        },
        { timeout: 8000, maximumAge: 60000, enableHighAccuracy: false },
      );
    });
  }

  function resetGPS() {
    gpsStatus.value = 'idle';
    gpsError.value = '';
  }

  return { location, gpsStatus, gpsError, detectGPS, resetGPS };
}
