/**
 * 코스 관련 공통 헬퍼 함수 모음
 * App.vue, CourseCard.vue 등 여러 컴포넌트에서 공유 사용
 */

export function durationLabel(minutes) {
  const value = Number(minutes || 0);
  const hours = Math.floor(value / 60);
  const mins = value % 60;
  if (!hours) return `${mins}분`;
  if (!mins) return `${hours}시간`;
  return `${hours}시간 ${mins}분`;
}

export function safetyClass(course) {
  return (
    {
      recommend: 'green',
      caution: 'yellow',
      not_recommended: 'red',
    }[course.safety_decision] || 'green'
  );
}

export function fallbackSafetyLabel(course) {
  return { safe: '추천', caution: '주의', danger: '비추천' }[course.safety_grade] || '추천';
}

export function daylightLabel(minutes) {
  if (minutes === null || minutes === undefined) return '확인 중';
  if (minutes < 30) return '부족';
  if (minutes < 60) return '짧음';
  return '충분';
}

export function daylightColor(minutes) {
  if (minutes === null || minutes === undefined) return 'yellow';
  if (minutes < 30) return 'red';
  if (minutes < 60) return 'yellow';
  return 'green';
}

export function safetyDotColor(course) {
  return (
    {
      recommend: 'green',
      caution: 'yellow',
      not_recommended: 'red',
    }[course?.safety_decision] || 'green'
  );
}

export function sourceLabel(course) {
  const source = String(course.source || '');
  if (source.includes('SHP')) return '로컬 SHP';
  if (source.includes('국립공원')) return '국립공원';
  if (source.includes('VWorld')) return 'VWorld';
  return '공공 데이터';
}

export function scoreLabel(key) {
  return (
    { fitness: '체력 적합도', weather: '날씨 안전도', accessibility: '접근성', time: '시간 적합도' }[key] || key
  );
}

export function scoreBarClass(value) {
  if (value >= 80) return 'bar-green';
  if (value >= 55) return 'bar-yellow';
  return 'bar-red';
}
