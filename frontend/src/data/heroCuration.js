// TODO: Replace these mock values with live safety feeds when the backend exposes them.
export const liveSafetyItems = [
  { id: 'wildfire', label: '산불경보', value: '전국 2곳' },
  { id: 'closure', label: '입산통제', value: '14개 구간' },
  { id: 'weather-alert', label: '기상특보', value: '강원 산지 강풍' },
  { id: 'sunset', label: '오늘 일몰', value: '19:57' },
  { id: 'local-weather', label: '현재 위치', value: '24도 맑음' },
];

export const heroThemeSlides = [
  {
    id: 'june-editorial',
    tone: 'green',
    label: 'JUNE EDITORIAL',
    title: '한낮 더위를 피하는 계곡 끼고 걷는 산',
    subtitle: '수목 그늘 70% 이상 · 평균 체감 3도 낮은 코스만',
    chips: [
      { label: '청계산', meta: '그늘길' },
      { label: '수락산', meta: '계곡길' },
      { label: '관악산', meta: '숲길' },
    ],
  },
  {
    id: 'data-pick',
    tone: 'blue',
    label: 'DATA PICK',
    title: '오늘 컨디션 가장 좋은 산 TOP 3',
    subtitle: '날씨·미세먼지·산불위험 종합점수 기준',
    chips: [
      { label: '1 청계산', meta: '92점' },
      { label: '2 아차산', meta: '88점' },
      { label: '3 인왕산', meta: '84점' },
    ],
  },
  {
    id: 'first-hike',
    tone: 'amber',
    label: 'FIRST HIKE',
    title: '처음 산행도 안심 초보자 입문 코스',
    subtitle: '경사 완만 · 탈출로 많음 · 2시간 이내 완주',
    chips: [
      { label: '아차산', meta: '75분' },
      { label: '남산', meta: '60분' },
      { label: '인왕산', meta: '90분' },
    ],
  },
];
