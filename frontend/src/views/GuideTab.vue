<template>
  <section class="screen-stack guide-layout">

    <!-- ── 지도 (왼쪽, 양 단계 공통) ── -->
    <div class="guide-map">
      <div ref="overviewMapEl" class="overview-map-container" aria-label="등산 추천 지도"></div>
      <div class="map-legend">
<div class="map-legend-body">
          <div class="mli-col">
            <img src="/marker-easy.png" class="mli-icon" />
            <span class="mli-label mli-easy">초급</span>
          </div>
          <div class="mli-divider"></div>
          <div class="mli-col">
            <img src="/marker-medium.png" class="mli-icon" />
            <span class="mli-label mli-medium">중급</span>
          </div>
          <div class="mli-divider"></div>
          <div class="mli-col">
            <img src="/marker-hard.png" class="mli-icon" />
            <span class="mli-label mli-hard">고급</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 오른쪽 패널 ── -->
    <div class="guide-panel">

      <!-- ════════════════════════════════
           PHASE 1: 산 선택
           ════════════════════════════════ -->
      <template v-if="guideStep === 'browse'">

        <!-- ── 통합 찾기 패널 ── -->
        <section class="panel browse-find-panel">
          <div class="recommend-hero">
            <p class="eyebrow">Today Match</p>
            <h2 class="bfp-title">오늘 어떤 산이 좋을까요?</h2>
            <p class="recommend-copy">산 이름을 몰라도 괜찮아요. 오늘의 시간, 산행 강도, 이동 거리를 알려주면 지금 가기 좋은 산을 먼저 골라드릴게요.</p>
          </div>

          <!-- 출발지 -->
          <div class="bfp-field">
            <span class="bfp-label">출발지</span>
            <div class="bfp-loc-row">
              <div class="bfp-loc-status" :class="{ active: !!location || !!customStartLocation }">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="13" height="13"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                <span>{{ locationLabel }}</span>
              </div>
              <div class="bfp-loc-actions">
                <button
                  type="button"
                  class="bfp-loc-btn"
                  :class="{ loading: gpsStatus === 'loading', error: gpsStatus === 'error' }"
                  :disabled="gpsStatus === 'loading'"
                  @click="handleGPS"
                  title="현재 위치 감지"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" :class="gpsStatus === 'loading' ? 'spin' : ''"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M1 12h4M19 12h4"/></svg>
                  현재 위치 감지
                </button>
                <button
                  type="button"
                  class="bfp-loc-btn"
                  :class="{ active: pickingLocation }"
                  @click="toggleLocationPick"
                  title="지도에서 출발지 선택"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                  {{ pickingLocation ? '취소' : '지도 선택' }}
                </button>
              </div>
            </div>
            <p v-if="pickingLocation" class="bfp-error" style="color:var(--accent)">🗺 지도를 클릭해 출발지를 선택하세요</p>
            <p v-else-if="gpsStatus === 'error'" class="bfp-error">⚠️ {{ gpsError }}</p>
          </div>

          <!-- 출발 시간 -->
          <div class="bfp-field">
            <span class="bfp-label">출발 시간</span>
            <!-- 구간 버튼 -->
            <div class="chips">
              <button type="button" class="chip chip-now" @click="setTimeNow">지금</button>
              <button v-for="seg in TIME_SEGMENTS" :key="seg.key" type="button"
                :class="['chip time-seg-chip', activeTimeSegment === seg.key ? 'active' : '']"
                @click="selectTimeSegment(seg.key)">{{ seg.label }}</button>
            </div>
            <!-- 타임바 -->
            <div class="time-bar-wrap">
              <div class="time-bar-header">
                <span class="time-bar-val">{{ profile.departureTime || '--:--' }} 출발</span>
              </div>
              <input
                type="range"
                class="time-bar-input"
                :min="TIME_MIN"
                :max="TIME_MAX"
                step="30"
                :value="departureMinutes"
                @input="onTimeBarInput"
              />
              <div class="time-bar-ticks">
                <span v-for="(tick, i) in TIME_TICKS" :key="tick.h"
                  class="time-bar-tick"
                  :class="{ 'tick-first': i === 0, 'tick-last': i === TIME_TICKS.length - 1 }"
                  :style="{ left: timeTickPct(tick.h) + '%' }">{{ tick.label }}</span>
              </div>
            </div>
          </div>

          <div class="recommend-form-grid">
            <!-- 산행 강도 -->
            <div class="bfp-field">
              <span class="bfp-label">산행 강도</span>
              <div class="chips">
                <button type="button" :class="['chip diff-all', profile.difficultyFilter === 'all' ? 'active' : '']" @click="setDifficulty('all')">전체</button>
                <button type="button" :class="['chip diff-easy', profile.difficultyFilter === 'easy' ? 'active' : '']" @click="setDifficulty('easy')">초급</button>
                <button type="button" :class="['chip diff-medium', profile.difficultyFilter === 'medium' ? 'active' : '']" @click="setDifficulty('medium')">중급</button>
                <button type="button" :class="['chip diff-hard', profile.difficultyFilter === 'hard' ? 'active' : '']" @click="setDifficulty('hard')">고급</button>
              </div>
            </div>

            <!-- 등산 가능 시간 스텝퍼 -->
            <div class="bfp-field">
              <span class="bfp-label">등산 가능 시간</span>
              <div class="stepper-card">
                <button type="button" class="stepper-btn"
                  :disabled="profile.desiredHikingMinutes <= 60"
                  @click="profile.desiredHikingMinutes = Math.max(60, profile.desiredHikingMinutes - 60)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" width="16" height="16"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
                <div class="stepper-display">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" class="stepper-icon" width="16" height="16"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  <span class="stepper-val">{{ profile.desiredHikingMinutes / 60 }}시간</span>
                </div>
                <button type="button" class="stepper-btn"
                  :disabled="profile.desiredHikingMinutes >= 480"
                  @click="profile.desiredHikingMinutes = Math.min(480, profile.desiredHikingMinutes + 60)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" width="16" height="16"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
              </div>
            </div>

            <!-- 이동 거리 스텝퍼 -->
            <div class="bfp-field">
              <span class="bfp-label">이동 거리</span>
              <div class="stepper-card">
                <button type="button" class="stepper-btn"
                  :disabled="profile.maxDistanceKm <= 50"
                  @click="profile.maxDistanceKm = Math.max(50, profile.maxDistanceKm - 50)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" width="16" height="16"><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
                <div class="stepper-display">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="stepper-icon" width="16" height="16"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                  <span class="stepper-val">{{ profile.maxDistanceKm }}km</span>
                </div>
                <button type="button" class="stepper-btn"
                  :disabled="profile.maxDistanceKm >= 500"
                  @click="profile.maxDistanceKm = Math.min(500, profile.maxDistanceKm + 50)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" width="16" height="16"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
              </div>
            </div>
          </div>

          <!-- 선택 요약 -->
          <div class="selection-summary">
            <span class="ss-pill" :class="`ss-diff-${profile.difficultyFilter}`">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/></svg>
              {{ difficultyLabel }}
            </span>
            <span v-if="profile.departureTime" class="ss-pill ss-depart">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="12" height="12"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              출발 {{ profile.departureTime }}
            </span>
            <span class="ss-pill ss-time">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" width="12" height="12"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
              {{ profile.desiredHikingMinutes / 60 }}시간
            </span>
            <span class="ss-pill ss-distance">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              {{ profile.maxDistanceKm }}km 이내
            </span>
          </div>

          <div class="recommend-actions">
            <button class="primary-btn wide-field" type="button" :disabled="loading" @click="handleMountainRecommend">
              {{ loading ? '분석 중…' : '오늘의 산 추천받기' }}
            </button>
            <button class="text-link-btn" type="button" @click="directBrowseOpen = !directBrowseOpen">
              {{ directBrowseOpen ? '직접 찾기 닫기' : '산 이름을 알고 있어요' }}
            </button>
          </div>
        </section>

        <!-- ── AI 추천 결과 ── -->
        <section v-if="hasRecommendationResult" class="panel">
          <div class="section-title compact">
            <div><p class="eyebrow">AI Picks</p><h2>오늘의 추천 산</h2></div>
            <button class="clear-rec-btn" type="button" @click="handleRetryRecommendation">다시 추천</button>
          </div>
          <p v-if="agentSummary" class="rec-summary">{{ agentSummary }}</p>

          <!-- 추천 산 카드 -->
          <div v-if="recommendedMountains.length" class="mountain-card-list">
            <MountainCard
              v-for="(mountain, idx) in recommendedMountains.slice(0, 3)"
              :key="mountain.id"
              :mountain="mountain"
              :rank="idx + 1"
              :is-selected="false"
              :is-favorite="isMountainFavorite(mountain.id)"
              @select="enterCourseStep"
              @toggle-favorite="toggleMountainFavorite"
            />
          </div>

          <!-- 추천 산 없을 때 -->
          <div v-else class="rec-empty">
            <p class="rec-empty-msg">현재 조건에서 안전 추천 산이 없습니다.</p>
            <p class="rec-empty-sub">아래 대안 산을 참고하거나 조건을 변경해보세요.</p>
          </div>

          <!-- 대안 산 (항상 표시) -->
          <div v-if="alternativeMountains.length" class="alternative-mountain-strip">
            <p class="bfp-label">{{ recommendedMountains.length ? '다른 선택지' : '대안 산 목록' }}</p>
            <button
              v-for="mountain in alternativeMountains.slice(0, recommendedMountains.length ? 2 : 5)"
              :key="mountain.id"
              class="alternative-mountain-btn"
              type="button"
              @click="enterCourseStep(mountain)"
            >
              <strong>{{ mountain.name }}</strong>
              <span>{{ mountain.safety_label || '대안 코스' }}</span>
            </button>
          </div>
        </section>

        <!-- ── 직접 찾기 ── -->
        <section v-if="directBrowseOpen || mountainSearch" class="panel mountain-list-panel">
          <div class="section-title compact">
            <div>
              <p class="eyebrow">Manual Search</p>
              <h2>직접 산 찾기<span class="mini-status" style="margin-left:6px">{{ filteredMountains.length }}</span></h2>
            </div>
          </div>

          <div class="bfp-search-row">
            <svg class="bfp-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-model="mountainSearch"
              class="bfp-search-input"
              type="text"
              placeholder="산 이름 또는 지역 검색…"
              autocomplete="off"
            />
          </div>

          <div v-if="loading && !filteredMountains.length" class="community-loading">분석 중…</div>

          <div class="mountain-browse-list">
            <button
              v-for="mountain in filteredMountains"
              :key="mountain.id"
              class="mountain-browse-row"
              type="button"
              @click="enterCourseStep(mountain)"
            >
              <i class="mbr-diff-dot" :style="{ background: diffDotColor(mountain.difficulty) }"></i>
              <div class="mbr-body">
                <strong class="mbr-name">{{ mountain.name }}</strong>
                <span class="mbr-meta">{{ mountain.region }}&nbsp;·&nbsp;{{ mountain.elevation_m }}m</span>
              </div>
              <span v-if="mountain.national_park" class="mc-np-badge" style="flex-shrink:0">국립공원</span>
              <svg class="mbr-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </div>
        </section>

      </template>

      <!-- ════════════════════════════════
           PHASE 2: 산 정보 대시보드
           ════════════════════════════════ -->
      <template v-else-if="selectedMountain">

        <!-- 산 헤더 -->
        <section class="panel course-step-header">
          <!-- 상단 내비 행: 뒤로가기 + 즐겨찾기 -->
          <div class="csh-nav">
            <button class="back-to-browse-btn" type="button" @click="backToBrowse">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="15 18 9 12 15 6"/></svg>
              산 목록
            </button>
            <button
              class="csh-fav-btn"
              type="button"
              :class="{ active: isMountainFavorite(selectedMountain.id) }"
              @click="toggleMountainFavorite(selectedMountain)"
              :title="isMountainFavorite(selectedMountain.id) ? '즐겨찾기 해제' : '즐겨찾기 추가'"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="20" height="20">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
            </button>
          </div>

          <!-- 산 제목 -->
          <div class="csh-title-block">
            <p class="eyebrow">{{ selectedMountain.region }}</p>
            <div class="csh-title-row">
              <h2 class="csh-mountain-name">{{ selectedMountain.name }}</h2>
              <span v-if="selectedMountain.national_park" class="mc-np-badge">국립공원</span>
            </div>
          </div>

          <!-- 오늘 산행 안전 등급 -->
          <div class="mountain-safety-rating" v-if="mountainSafetyDecision">
            <span :class="['safety-badge', mountainSafetyDecision.class]">
              {{ mountainSafetyDecision.label }}
            </span>
            <p class="msr-sub">오늘 {{ selectedMountain.name }} 산행 안전 평가</p>
          </div>

          <!-- 통계 -->
          <div class="mountain-detail-stats">
            <div class="mds-item"><span class="mds-icon">⛰</span><span class="mds-label">해발</span><strong>{{ selectedMountain.elevation_m }}m</strong></div>
            <div class="mds-item"><span class="mds-icon">⏱</span><span class="mds-label">산행 시간</span><strong>{{ Math.floor(selectedMountain.walk_time_min/60) }}~{{ Math.floor(selectedMountain.walk_time_max/60) }}h</strong></div>
            <div class="mds-item"><span class="mds-icon">🏔</span><span class="mds-label">난이도</span><strong>{{ { easy:'초급', medium:'중급', hard:'고급' }[selectedMountain.difficulty] || '-' }}</strong></div>
            <div class="mds-item"><span class="mds-icon">👥</span><span class="mds-label">혼잡도</span><strong>{{ crowdingLabel(selectedMountain.crowding) }}</strong></div>
          </div>

          <!-- 날씨 카드 -->
          <div v-if="weatherData" class="mountain-weather-card">
            <div class="mwc-header">
              <span class="mwc-label">📡 {{ selectedMountain.name }} 날씨</span>
              <span class="mwc-source">{{ weatherData.source === 'mock' ? '추정값' : '기상청 실황' }}</span>
            </div>
            <div class="mwc-row">
              <span class="mwc-item">
                <span class="mwc-icon">🌡</span>
                <span>{{ weatherData.temperature_c }}°C</span>
              </span>
              <span class="mwc-item" :class="weatherData.rainfall_mm > 0 ? 'mwc-warn' : ''">
                <span class="mwc-icon">💧</span>
                <span>강수 {{ weatherData.rainfall_mm ?? 0 }}mm</span>
              </span>
              <span class="mwc-item" :class="weatherData.wind_speed_ms >= 5 ? 'mwc-warn' : ''">
                <span class="mwc-icon">💨</span>
                <span>풍속 {{ weatherData.wind_speed_ms }}m/s</span>
              </span>
              <span class="mwc-item">
                <span class="mwc-icon">🌄</span>
                <span>일출 {{ weatherData.sunrise || '-' }}</span>
              </span>
              <span class="mwc-item" :class="sunsetWarning ? 'mwc-warn' : ''">
                <span class="mwc-icon">🌅</span>
                <span>일몰 {{ weatherData.sunset || '-' }}</span>
              </span>
            </div>
            <p v-if="selectedMountainSunsetNote" class="mwc-sunset-note">{{ selectedMountainSunsetNote }}</p>
          </div>

          <!-- 산림 생태 현황 카드 -->
          <div v-if="fluxData && fluxData.ok" class="forest-flux-card">
            <div class="ffc-header">
              <span class="ffc-title">🌳 산림 생태 현황</span>
              <span class="ffc-station">{{ fluxData.station_name }} 관측소</span>
            </div>
            <div class="ffc-badges">
              <span :class="['ffc-badge', 'ffc-carbon', fluxData.carbon_status === '강한탄소흡수' || fluxData.carbon_status === '탄소흡수' ? 'ffc-green' : fluxData.carbon_status === '탄소방출' ? 'ffc-red' : 'ffc-gray']">
                {{ fluxData.carbon_status === '강한탄소흡수' ? '💚 강한 탄소흡수' : fluxData.carbon_status === '탄소흡수' ? '🌿 탄소흡수 중' : fluxData.carbon_status === '탄소방출' ? '⚠️ 탄소방출 중' : '⚖️ 탄소균형' }}
              </span>
              <span v-if="fluxData.uv_risk" :class="['ffc-badge', fluxData.uv_index >= 8 ? 'ffc-red' : fluxData.uv_index >= 6 ? 'ffc-orange' : fluxData.uv_index >= 3 ? 'ffc-yellow' : 'ffc-gray']">
                ☀️ 자외선 {{ fluxData.uv_risk }} (UV {{ fluxData.uv_index }})
              </span>
              <span v-if="fluxData.discomfort_label" :class="['ffc-badge', fluxData.discomfort_index >= 80 ? 'ffc-red' : fluxData.discomfort_index >= 75 ? 'ffc-orange' : fluxData.discomfort_index >= 68 ? 'ffc-yellow' : 'ffc-green']">
                🌡 불쾌지수 {{ fluxData.discomfort_index }} ({{ fluxData.discomfort_label }})
              </span>
              <span v-if="fluxData.humidity_level" class="ffc-badge ffc-blue">
                💧 {{ fluxData.humidity_level }}
              </span>
              <span v-if="fluxData.soil_status" class="ffc-badge ffc-gray">
                🪨 토양 {{ fluxData.soil_status }}
              </span>
            </div>
            <p v-if="fluxData.carbon_footprint_msg" class="ffc-footprint">
              {{ fluxData.carbon_footprint_msg }}
            </p>
            <p v-if="fluxData.uv_index >= 6 && fluxData.uv_advice" class="ffc-uv-advice">
              {{ fluxData.uv_advice }}
            </p>
          </div>

          <!-- ML 사고 위험 분석 -->
          <div v-if="mlRiskInfo" class="ml-risk-card">
            <div class="ml-risk-header">
              <span class="ml-risk-title">📊 소방청 사고 데이터 분석</span>
              <span
                :class="['ml-risk-badge',
                  mlRiskInfo.risk_index >= 0.70 ? 'mlr-high' :
                  mlRiskInfo.risk_index >= 0.45 ? 'mlr-medium' :
                  mlRiskInfo.risk_index >= 0.20 ? 'mlr-low' : 'mlr-safe']"
              >
                {{ mlRiskInfo.risk_index >= 0.70 ? '1인당 사고율 높음' :
                   mlRiskInfo.risk_index >= 0.45 ? '주의 구간' :
                   mlRiskInfo.risk_index >= 0.20 ? '보통' : '상대적 안전' }}
              </span>
            </div>
            <p class="ml-risk-warn">{{ mlRiskInfo.warning }}</p>
            <div class="ml-risk-types">
              <span
                v-for="(prob, type) in mlRiskInfo.type_proba"
                :key="type"
                class="ml-type-chip"
                :class="type === mlRiskInfo.top_type ? 'ml-type-top' : ''"
              >
                {{ { '부상사고':'실족·추락', '조난수색':'길잃음·조난', '질환':'탈진·질환', '기타':'기타' }[type] }}
                {{ Math.round(prob * 100) }}%
              </span>
            </div>
            <p class="ml-risk-note">* {{ mlTrainingNote }} 기반 1인당 사고율 분석</p>
          </div>

          <!-- 산 소개 -->
          <div v-if="storyText" class="mountain-story-card">
            <div class="msc-summary-wrap" :class="{ collapsed: storyNeedsToggle && !storyExpanded }">
              <p class="mountain-story-summary">{{ storyText }}</p>
              <div v-if="storyNeedsToggle && !storyExpanded" class="msc-fade"></div>
            </div>
            <button v-if="storyNeedsToggle" class="msc-toggle" type="button" @click="storyExpanded = !storyExpanded">
              {{ storyExpanded ? '접기 ▲' : '더 보기 ▼' }}
            </button>

            <div v-if="mountainStory?.selection_reason" class="msc-selection">
              <span class="msc-selection-label">🏆 100대 명산 선정 이유</span>
              <p class="msc-selection-text">{{ mountainStory.selection_reason }}</p>
            </div>
          </div>

          <!-- 산사태 예보 경고 -->
          <div v-if="landslideRisk !== 'low'" :class="['landslide-alert', landslideRisk === 'danger' ? 'ls-danger' : 'ls-caution']">
            <div class="ls-icon">{{ landslideRisk === 'danger' ? '⛰' : '⚠️' }}</div>
            <div class="ls-body">
              <p class="ls-title">{{ landslideRisk === 'danger' ? '산사태 경보 발령 지역' : '산사태 주의보 발령 지역' }}</p>
              <p class="ls-desc">{{ landslideRisk === 'danger' ? '현재 이 지역에 산사태 경보가 발령되었습니다. 산행을 삼가세요.' : '현재 이 지역에 산사태 주의보가 발령되었습니다. 산행 시 주의가 필요합니다.' }}</p>
            </div>
          </div>

          <!-- 재난위험지구 -->
          <div v-if="selectedDisasterZones.length" class="disaster-zone-panel">
            <p class="disaster-zone-title">⚠️ 인근 재난위험지구 {{ selectedDisasterZones.length }}개</p>
            <ul class="disaster-zone-list">
              <li v-for="zone in selectedDisasterZones.slice(0, 3)" :key="zone.id">
                <strong>{{ zone.district || zone.location }}</strong>
                <span v-if="zone.risk_factor"> · {{ zone.risk_factor }}</span>
              </li>
            </ul>
          </div>

          <!-- 커뮤니티 안전 제보 -->
          <div v-if="mountainSafetyReports.length" class="disaster-zone-panel">
            <p class="disaster-zone-title">📢 커뮤니티 안전 제보 {{ mountainSafetyReports.length }}건</p>
            <ul class="disaster-zone-list">
              <li v-for="r in mountainSafetyReports.slice(0, 3)" :key="r.id">
                <strong>{{ r.title }}</strong>
                <span> · 👍 {{ r.like_count }} 💬 {{ r.comment_count }}</span>
              </li>
            </ul>
          </div>
        </section>


        <!-- 하이라이트 -->
        <section v-if="selectedMountain.highlights?.length" class="panel">
          <div class="section-title compact">
            <div><p class="eyebrow">Highlights</p><h2>이 산의 매력</h2></div>
          </div>
          <ul class="highlight-list">
            <li v-for="h in selectedMountain.highlights" :key="h">{{ h }}</li>
          </ul>
        </section>

        <!-- AI 도우미 CTA -->
        <div class="chat-cta-panel">
          <p class="chat-cta-text">{{ selectedMountain.name }} 산행, AI에게 더 물어보세요</p>
          <button class="chat-cta-btn" type="button" @click="goToChat">
            🤖 AI 도우미에게 물어보기
          </button>
        </div>

      </template>

    </div>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import {
  loadMountains, publicMountains, recommendedMountains, alternativeMountains,
  selectedMountain, gpsStatus, gpsError, detectGPS, loadWeather, weatherData,
  submitMountainRecommendation, loading, profile, agentSummary,
  location, customStartLocation, guideStep,
} from '../composables/useGuide.js';
import { communitySearch, communityCategory } from '../composables/useCommunity.js';
import { fetchDisasterZones, fetchMountainStory, fetchSafetyReports, fetchLandslide, fetchForestFlux } from '../api.js';
import { useLeafletMap } from '../composables/useLeafletMap.js';
import MountainCard from '../components/MountainCard.vue';
import { isMountainFavorite, toggleMountainFavorite } from '../composables/useUserData.js';

const router = useRouter();
const overviewMapEl = ref(null);

// ── 출발 시간 ─────────────────────────────────────────────────────────────────
const TIME_SEGMENTS = [
  { key: 'dawn',      label: '새벽', jumpHour: 5,  hours: [4, 5, 6] },
  { key: 'morning',   label: '아침', jumpHour: 8,  hours: [7, 8, 9] },
  { key: 'forenoon',  label: '오전', jumpHour: 10, hours: [10, 11, 12] },
  { key: 'afternoon', label: '오후', jumpHour: 14, hours: [13, 14, 15, 16, 17] },
];
const TIME_MIN = 4 * 60;   // 04:00
const TIME_MAX = 18 * 60;  // 18:00
const TIME_TICKS = [
  { h: 4,  label: '04:00' },
  { h: 7,  label: '07:00' },
  { h: 10, label: '10:00' },
  { h: 13, label: '13:00' },
  { h: 18, label: '18:00' },
];

// departureTime에서 자동 계산 — 별도 ref 없이 항상 동기화
const activeTimeSegment = computed(() => {
  if (!profile.departureTime) return null;
  const h = parseInt(profile.departureTime.split(':')[0], 10);
  return TIME_SEGMENTS.find((s) => s.hours.includes(h))?.key ?? null;
});

const departureMinutes = computed(() => {
  if (!profile.departureTime) return 8 * 60;
  const [h, m] = profile.departureTime.split(':').map(Number);
  return Math.max(TIME_MIN, Math.min(TIME_MAX, h * 60 + m));
});

function onTimeBarInput(e) {
  const mins = parseInt(e.target.value, 10);
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  profile.departureTime = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function timeTickPct(h) {
  return ((h * 60 - TIME_MIN) / (TIME_MAX - TIME_MIN)) * 100;
}

function selectTimeSegment(key) {
  const seg = TIME_SEGMENTS.find((s) => s.key === key);
  if (seg) profile.departureTime = `${String(seg.jumpHour).padStart(2, '0')}:00`;
}

function setTimeNow() {
  const now = new Date();
  profile.departureTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
}
const { renderOverviewMap, focusOverviewCourse, enableLocationPick, disableLocationPick, clearLocationPickMarker } = useLeafletMap();

// ── 브라우즈 상태 ─────────────────────────────────────────────────────────────
const mountainSearch = ref('');
const hasRecommendationResult = ref(false);
const directBrowseOpen = ref(false);

// ── 출발지 선택 ───────────────────────────────────────────────────────────────
const pickingLocation = ref(false);

function toggleLocationPick() {
  if (pickingLocation.value) {
    pickingLocation.value = false;
    disableLocationPick();
    return;
  }
  pickingLocation.value = true;
  enableLocationPick(async ({ lat, lng }) => {
    pickingLocation.value = false;
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=10&accept-language=ko`,
        { headers: { 'Accept-Language': 'ko' } },
      );
      const data = await res.json();
      const addr = data.address || {};
      const name = addr.city || addr.county || addr.town || addr.village
        || data.display_name?.split(',')[0]
        || '선택한 위치';
      customStartLocation.value = { lat, lng, name };
    } catch {
      customStartLocation.value = { lat, lng, name: '선택한 위치' };
    }
  });
}

const locationLabel = computed(() => {
  if (customStartLocation.value) return customStartLocation.value.name + ' 기준';
  if (location.value) return '현재 위치 감지됨';
  return '위치 미설정';
});

const difficultyLabel = computed(() => ({
  all: '전체 난이도', easy: '초급', medium: '중급', hard: '고급',
}[profile.difficultyFilter] || '전체 난이도'));

function diffDotColor(difficulty) {
  if (difficulty === 'easy') return '#22c55e';
  if (difficulty === 'medium') return '#f97316';
  if (difficulty === 'hard') return '#ef4444';
  return '#9ca3af';
}

function setDifficulty(level) {
  profile.difficultyFilter = level;
  const expMap = { easy: 'beginner', medium: 'intermediate', hard: 'advanced' };
  if (expMap[level]) {
    profile.experience = expMap[level];
    directBrowseOpen.value = true;
  }
}

async function handleMountainRecommend() {
  await submitMountainRecommendation();
  hasRecommendationResult.value = true;
  directBrowseOpen.value = false;
  await nextTick();
  refreshOverviewMap();
}

async function handleRetryRecommendation() {
  hasRecommendationResult.value = false;
  await handleMountainRecommend();
}

// ── 코스 단계 로컬 상태 ───────────────────────────────────────────────────────
const selectedDisasterZones = ref([]);
const mountainStory = ref(null);
const mountainSafetyReports = ref([]);
const storyExpanded = ref(false);
const landslideRisk = ref('low'); // 'low' | 'caution' | 'danger'
const fluxData = ref(null);

// 중복 산 선택 방지 (빠른 연속 클릭 시 race condition 차단)
let _courseStepToken = 0;

const storyText = computed(() => {
  const story = mountainStory.value;
  if (story?.source === 'seed_mountain_descriptions') {
    return story.intro || story.summary || story.detail || '';
  }

  if (selectedMountain.value?.description_source === 'seed_mountain_descriptions') {
    return selectedMountain.value.intro || selectedMountain.value.description || '';
  }

  return '';
});
const storyNeedsToggle = computed(() => storyText.value.length > 160);

// ── 브라우즈 단계: 필터된 산 목록 ────────────────────────────────────────────
const filteredMountains = computed(() => {
  const search = mountainSearch.value.trim().toLowerCase();
  const diff = profile.difficultyFilter;
  const safetyMap = new Map(
    [...recommendedMountains.value, ...alternativeMountains.value].map((m) => [m.id, m])
  );

  let base = publicMountains.value.map((m) => {
    const scored = safetyMap.get(m.id);
    return scored ? { ...m, ...scored } : m;
  });

  if (diff && diff !== 'all') {
    base = base.filter((m) => m.difficulty === diff);
  }

  if (search) {
    base = base.filter(
      (m) =>
        m.name.toLowerCase().includes(search) ||
        (m.region || '').toLowerCase().includes(search),
    );
  }

  return base.sort((a, b) => {
    const aRanked = !!a.safety_decision;
    const bRanked = !!b.safety_decision;
    if (aRanked !== bRanked) return aRanked ? -1 : 1;
    if (aRanked && bRanked) {
      const order = { recommend: 0, caution: 1, not_recommended: 2 };
      return (order[a.safety_decision] ?? 3) - (order[b.safety_decision] ?? 3);
    }
    return (b.crowding || 0) - (a.crowding || 0);
  });
});

function browseBadgeClass(mountain) {
  return { recommend: 'green', caution: 'yellow', not_recommended: 'red' }[mountain.safety_decision] || '';
}

// ── 지도 ─────────────────────────────────────────────────────────────────────
const mapMountains = computed(() => {
  // 추천 실행 전: 모든 산을 그대로 (난이도 색상으로 표시)
  if (!hasRecommendationResult.value || !recommendedMountains.value.length) {
    return publicMountains.value;
  }
  // 추천 실행 후: 추천된 산에 _highlighted, 나머지는 _muted
  const recommended = new Set(recommendedMountains.value.map((m) => m.id));
  const alternatives = new Set(alternativeMountains.value.map((m) => m.id));
  return publicMountains.value.map((m) => ({
    ...m,
    _highlighted: recommended.has(m.id),
    _muted: !recommended.has(m.id) && !alternatives.has(m.id),
  }));
});

function refreshOverviewMap() {
  if (!overviewMapEl.value) return;
  renderOverviewMap(
    overviewMapEl.value,
    mapMountains.value,
    selectedMountain.value?.id,
    (mountain) => enterCourseStep(mountain),
    {
      startLocation: customStartLocation.value || location.value,
      radiusKm: profile.maxDistanceKm,
      selectedMountain: guideStep.value === 'courses' ? selectedMountain.value : null,
      disasterZones: guideStep.value === 'courses' ? selectedDisasterZones.value : [],
    },
  );
}

// ── 단계 전환 ─────────────────────────────────────────────────────────────────
async function enterCourseStep(mountain) {
  const token = ++_courseStepToken;

  guideStep.value = 'courses';
  selectedMountain.value = mountain;
  mountainStory.value = null;
  mountainSafetyReports.value = [];
  selectedDisasterZones.value = [];
  landslideRisk.value = 'low';
  storyExpanded.value = false;
  fluxData.value = null;

  if (mountain?.lat && mountain?.lng) {
    loadWeather(mountain.lat, mountain.lng, mountain.name);
    fetchForestFlux({ mountain: mountain.name, lat: mountain.lat, lng: mountain.lng })
      .then(d => { fluxData.value = d; })
      .catch(() => {});
  }
  await nextTick();
  if (token !== _courseStepToken) return;

  focusOverviewCourse(mountain);
  refreshOverviewMap();
  const [zonesData, storyData, reportsData, landslideData] = await Promise.allSettled([
    fetchDisasterZones(mountain.name),
    fetchMountainStory(mountain.name),
    fetchSafetyReports(mountain.name),
    fetchLandslide(mountain.region || ''),
  ]);
  if (token !== _courseStepToken) return;

  selectedDisasterZones.value = zonesData.status === 'fulfilled' ? (zonesData.value.zones || []) : [];

  // 산사태 예보: 이 지역에 경보/주의가 있으면 표시
  if (landslideData.status === 'fulfilled') {
    const items = landslideData.value?.items || [];
    const worstRisk = items.reduce((acc, item) => {
      if (item.risk === 'danger') return 'danger';
      if (item.risk === 'caution' && acc !== 'danger') return 'caution';
      return acc;
    }, 'low');
    landslideRisk.value = worstRisk;
  }

  // 재난위험지구 로딩 후 지도 갱신
  refreshOverviewMap();
  const story = storyData.status === 'fulfilled' ? (storyData.value.items?.[0] ?? null) : null;
  mountainStory.value = story;
  if (story?.source === 'seed_mountain_descriptions') {
    selectedMountain.value = {
      ...selectedMountain.value,
      intro: story.intro || story.summary || story.detail || '',
      description: story.summary || story.detail || story.intro || '',
      description_source: story.source,
    };
  }
  mountainSafetyReports.value = reportsData.status === 'fulfilled' ? (reportsData.value.posts || []) : [];

}

function backToBrowse() {
  guideStep.value = 'browse';
  selectedMountain.value = null;
  refreshOverviewMap();
}

// ── 산행 안전 등급 (추천 결과 or 날씨 기반) ──────────────────────────────────
const mountainSafetyDecision = computed(() => {
  const m = selectedMountain.value;
  if (!m) return null;

  const scored = [...recommendedMountains.value, ...alternativeMountains.value].find(
    (r) => r.id === m.id,
  );
  if (scored?.safety_decision) {
    return {
      class: { recommend: 'green', caution: 'yellow', not_recommended: 'red' }[scored.safety_decision] || '',
      label: scored.safety_label || scored.safety_decision,
    };
  }

  const w = weatherData.value;
  if (!w) return null;
  const rain = w.rainfall_mm ?? 0;
  const wind = w.wind_speed_ms ?? 0;
  if (rain >= 20 || wind >= 10) return { class: 'red', label: '비추천' };
  if (rain > 0 || wind >= 5) return { class: 'yellow', label: '주의' };
  return { class: 'green', label: '추천' };
});

// ── ML 위험 정보 ──────────────────────────────────────────────────────────────
const mlRiskInfo = computed(() => {
  const m = selectedMountain.value;
  if (!m) return null;
  const scored = [...recommendedMountains.value, ...alternativeMountains.value].find((r) => r.id === m.id);
  return scored?.ml_risk_info || null;
});

const mlTrainingNote = computed(() => {
  const training = mlRiskInfo.value?.training;
  const rows = training?.rows;
  const years = training?.year_range;
  if (rows && Array.isArray(years) && years.length === 2) {
    return `${years[0]}-${years[1]}년 소방청 산악사고 ${Number(rows).toLocaleString()}건`;
  }
  return '2010-2024년 소방청 산악사고 112,902건';
});

// ── 일몰 경고 ────────────────────────────────────────────────────────────────
const sunsetWarning = computed(() => {
  const w = weatherData.value;
  const m = selectedMountain.value;
  if (!w?.sunset || !m) return false;
  const [sh, sm] = w.sunset.split(':').map(Number);
  const sunsetMin = sh * 60 + sm;
  const now = new Date();
  const nowMin = now.getHours() * 60 + now.getMinutes();
  const walkMax = m.walk_time_max ?? 180;
  return (nowMin + walkMax) > (sunsetMin - 30); // 30분 여유 이하
});

const selectedMountainSunsetNote = computed(() => {
  const m = selectedMountain.value;
  if (!m) return null;
  const scored = [...recommendedMountains.value, ...alternativeMountains.value].find((r) => r.id === m.id);
  return scored?.sunset_note || null;
});


// ── 유틸 ──────────────────────────────────────────────────────────────────────
function crowdingLabel(c) {
  if (c < 0.4) return '한산';
  if (c < 0.65) return '보통';
  return '혼잡';
}

function goToCommunity(mountainName) {
  communitySearch.value = mountainName;
  communityCategory.value = '';
  router.push('/community');
}

function goToChat() {
  router.push('/chat');
}

async function handleGPS() {
  pickingLocation.value = false;
  disableLocationPick();
  clearLocationPickMarker();
  customStartLocation.value = null;
  await detectGPS();
  loadWeather();
}

// ── 반응성 ────────────────────────────────────────────────────────────────────
watch(mapMountains, () => refreshOverviewMap());
watch(selectedMountain, () => refreshOverviewMap());
watch(() => [profile.maxDistanceKm, location.value, customStartLocation.value], () => refreshOverviewMap());

onMounted(async () => {
  await loadMountains();
  loadWeather();
  await nextTick();
  refreshOverviewMap();
});
</script>
