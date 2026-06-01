<template>
  <!-- ══ 보호자 전용 뷰 (URL에 #/safe/UUID 있을 때) ══════════════════════ -->
  <main v-if="isGuardianView" class="guardian-shell">
    <header class="guardian-header">
      <img src="/logo.png" alt="올라" class="guardian-logo-img" />
      <span :class="['guardian-status-chip', guardianStatusClass]">{{ guardianStatusLabel }}</span>
    </header>

    <div v-if="guardianLoading" class="guardian-loading">위치 정보를 불러오는 중입니다…</div>
    <div v-else-if="guardianSession">
      <!-- 지도 -->
      <div ref="guardianMapEl" class="guardian-map kakao-map" aria-label="산행자 현재 위치 지도"></div>

      <!-- 상태 카드 -->
      <section class="guardian-card">
        <div class="guardian-info-row">
          <div>
            <p class="eyebrow">산행 중</p>
            <h2>{{ guardianSession.course_name }}</h2>
            <p class="guardian-mountain">{{ guardianSession.mountain }}</p>
          </div>
          <span :class="['safety-badge', guardianStatusClass]">{{ guardianSession.safety_label }}</span>
        </div>

        <div class="guardian-meta-row">
          <span>📍 마지막 위치 수신: <strong>{{ guardianLastUpdate }}</strong></span>
          <span>🕐 {{ guardianSession.duration_min }}분 코스</span>
        </div>

        <div v-if="guardianSession.risk_factors?.length" class="risk-tags guardian-risks">
          <span v-for="f in guardianSession.risk_factors" :key="f">{{ f }}</span>
        </div>

        <div v-if="guardianSession.status === 'ended'" class="guardian-ended-banner">
          산행이 종료되었습니다.
        </div>
      </section>

      <!-- 긴급 버튼 -->
      <section class="guardian-actions">
        <a href="tel:119" class="emergency-btn">🚨 119 신고</a>
        <button class="outline-btn" type="button" @click="refreshGuardian">새로고침</button>
      </section>

      <p v-if="guardianPollError" class="guardian-error">{{ guardianPollError }}</p>
    </div>
    <div v-else class="guardian-not-found">
      <p>세이프 링크를 찾을 수 없습니다.<br>산행자에게 링크를 다시 받으세요.</p>
    </div>
  </main>

  <!-- ══ 본 앱 ═════════════════════════════════════════════════════════ -->
  <main v-else class="app-shell">
    <!-- ─── 헤더 ──────────────────────────────────────────────────────── -->
    <header class="app-header">
      <div class="header-text">
        <p class="eyebrow">AI 산행 안전 진단 · 연간 산악구조 8,000건+</p>
        <img src="/logo.png" alt="올라" class="app-logo" />
        <p>동반자가 있는 모든 산행은 더 꼼꼼한 준비가 필요합니다. 올라가 날씨·코스·위험 데이터를 종합해 안전 등급을 알려드립니다.</p>
      </div>

      <!-- 해 + 산 일러스트 -->
      <div class="header-illust" aria-hidden="true">
        <svg viewBox="0 0 160 140" fill="none" xmlns="http://www.w3.org/2000/svg">
          <!-- 하늘 그라디언트 -->
          <defs>
            <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#bef264" stop-opacity="0.18"/>
              <stop offset="100%" stop-color="#86efac" stop-opacity="0.04"/>
            </linearGradient>
            <linearGradient id="sunGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#fde68a"/>
              <stop offset="100%" stop-color="#f97316"/>
            </linearGradient>
            <linearGradient id="mtn1" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#16a34a"/>
              <stop offset="100%" stop-color="#15803d"/>
            </linearGradient>
            <linearGradient id="mtn2" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#22c55e"/>
              <stop offset="100%" stop-color="#16a34a"/>
            </linearGradient>
            <linearGradient id="mtn3" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#4ade80"/>
              <stop offset="100%" stop-color="#22c55e"/>
            </linearGradient>
          </defs>

          <!-- 배경 -->
          <rect width="160" height="140" rx="16" fill="url(#skyGrad)"/>

          <!-- 햇살 -->
          <g opacity="0.35" stroke="#f97316" stroke-width="1.5" stroke-linecap="round">
            <line x1="120" y1="28" x2="120" y2="18"/>
            <line x1="120" y1="52" x2="120" y2="62"/>
            <line x1="108" y1="40" x2="98"  y2="40"/>
            <line x1="132" y1="40" x2="142" y2="40"/>
            <line x1="111.5" y1="31.5" x2="104.4" y2="24.4"/>
            <line x1="128.5" y1="48.5" x2="135.6" y2="55.6"/>
            <line x1="128.5" y1="31.5" x2="135.6" y2="24.4"/>
            <line x1="111.5" y1="48.5" x2="104.4" y2="55.6"/>
          </g>

          <!-- 태양 -->
          <circle cx="120" cy="40" r="13" fill="url(#sunGrad)" opacity="0.9"/>
          <circle cx="120" cy="40" r="9"  fill="#fef3c7" opacity="0.6"/>

          <!-- 구름 -->
          <g opacity="0.55" fill="white">
            <ellipse cx="44" cy="38" rx="18" ry="10"/>
            <ellipse cx="34" cy="42" rx="12" ry="8"/>
            <ellipse cx="56" cy="42" rx="10" ry="7"/>
          </g>

          <!-- 뒷 산 (가장 어두운) -->
          <path d="M0 140 L0 90 L30 55 L60 88 L90 45 L130 90 L160 72 L160 140 Z"
                fill="url(#mtn1)" opacity="0.45"/>

          <!-- 중간 산 -->
          <path d="M0 140 L0 105 L25 75 L55 100 L80 60 L110 95 L140 70 L160 85 L160 140 Z"
                fill="url(#mtn2)" opacity="0.7"/>

          <!-- 앞 산 (가장 밝은) -->
          <path d="M0 140 L0 118 L20 100 L50 115 L72 85 L95 112 L120 92 L145 108 L160 98 L160 140 Z"
                fill="url(#mtn3)" opacity="0.9"/>

          <!-- 등산객 실루엣 -->
          <g fill="#15803d" opacity="0.8">
            <!-- 몸 -->
            <circle cx="73" cy="80" r="3"/>
            <line x1="73" y1="83" x2="73" y2="91" stroke="#15803d" stroke-width="1.8" stroke-linecap="round"/>
            <!-- 다리 -->
            <line x1="73" y1="91" x2="70" y2="97" stroke="#15803d" stroke-width="1.8" stroke-linecap="round"/>
            <line x1="73" y1="91" x2="76" y2="97" stroke="#15803d" stroke-width="1.8" stroke-linecap="round"/>
            <!-- 팔 (스틱) -->
            <line x1="73" y1="85" x2="69" y2="90" stroke="#15803d" stroke-width="1.8" stroke-linecap="round"/>
            <line x1="69" y1="90" x2="67" y2="95" stroke="#15803d" stroke-width="1.4" stroke-linecap="round"/>
          </g>

          <!-- 나무들 -->
          <g fill="#15803d" opacity="0.7">
            <polygon points="18,115 22,105 26,115"/>
            <rect x="21" y="115" width="2" height="5" rx="0.5"/>
            <polygon points="30,118 34,108 38,118"/>
            <rect x="33" y="118" width="2" height="4" rx="0.5"/>
          </g>
          <g fill="#16a34a" opacity="0.6">
            <polygon points="130,110 134,99 138,110"/>
            <rect x="133" y="110" width="2" height="5" rx="0.5"/>
            <polygon points="142,107 146,97 150,107"/>
            <rect x="145" y="107" width="2" height="4" rx="0.5"/>
          </g>
        </svg>

        <!-- 로그인·새로고침 버튼 -->
        <div class="header-actions">
          <button v-if="authUser" class="auth-user-btn" type="button" @click="showAuthModal = true">
            <span class="auth-avatar">{{ authUser.nickname[0] }}</span>
            <span class="auth-nickname">{{ authUser.nickname }}</span>
          </button>
          <button v-else class="login-btn" type="button" @click="showAuthModal = true">로그인</button>
          <button class="icon-btn" type="button" title="새로고침" @click="loadEverything">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M21 12a9 9 0 0 1-15.5 6.2M3 12A9 9 0 0 1 18.5 5.8M18 3v4h-4M6 21v-4h4" />
            </svg>
          </button>
        </div>
      </div>
    </header>

    <!-- ─── 에러 배너 ──────────────────────────────────────────────────── -->
    <div v-if="error" class="error-banner" role="alert">
      <span>⚠️ {{ error }}</span>
      <button class="error-close" type="button" aria-label="닫기" @click="error = ''">✕</button>
    </div>

    <!-- ─── 탭바 ──────────────────────────────────────────────────────── -->
    <nav class="tabbar" aria-label="주요 화면">
      <!-- 사이드바 브랜딩 (데스크톱에서만 표시) -->
      <div class="sidebar-brand">
        <img src="/logo.png" alt="올라" class="sidebar-logo-img" />
        <p class="sidebar-tagline">함께 오르는 안전 산행</p>
      </div>
      <button :class="{ active: activeTab === 'guide' }" type="button" @click="activeTab = 'guide'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"></polygon><line x1="9" y1="3" x2="9" y2="21"></line><line x1="15" y1="3" x2="15" y2="21"></line></svg>
        <span>안전코스</span>
      </button>
      <button :class="{ active: activeTab === 'safeLink' }" type="button" @click="activeTab = 'safeLink'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
        <span>안전공유</span>
      </button>
      <button :class="{ active: activeTab === 'community' }" type="button" @click="activeTab = 'community'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
        <span>커뮤니티</span>
      </button>
      <button :class="{ active: activeTab === 'myPage' }" type="button" @click="activeTab = 'myPage'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
        <span>내정보</span>
      </button>
    </nav>

    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- 안전코스 탭                                                         -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <section v-if="activeTab === 'guide'" class="screen-stack guide-layout">

      <!-- ── 왼쪽 컬럼: 입력 폼 + 날씨 조건 (데스크톱) ── -->
      <div class="guide-left">

      <!-- 플래너 입력 폼 -->
      <section class="panel planner-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Safe Course</p>
            <h2>약자 동반 안전코스추천</h2>
          </div>
          <span class="mini-status">{{ loading ? '분석 중' : '준비됨' }}</span>
        </div>

        <form class="planner" @submit.prevent="submit">
          <!-- 산 선택 + GPS 버튼 -->
          <div class="field wide-field gps-field">
            <span>산 선택</span>
            <div class="gps-row">
              <select v-model="profile.mountainName" @change="handleMountainChange">
                <option v-for="mountain in mountainOptions" :key="mountain.name" :value="mountain.name">
                  {{ mountain.name }} · {{ mountain.count }}개 코스
                </option>
              </select>
              <button
                class="gps-btn"
                type="button"
                :class="gpsStatus"
                :disabled="gpsStatus === 'loading'"
                :title="gpsBtnTitle"
                @click="handleGPS"
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
                  <path v-if="gpsStatus === 'loading'" d="M12 6a6 6 0 0 1 6 6" class="gps-spin" />
                </svg>
              </button>
            </div>
            <!-- GPS 결과 메시지 -->
            <p v-if="gpsStatus === 'success'" class="gps-message success">
              📍 현재 위치 감지 완료 — 가장 가까운 코스를 우선합니다
            </p>
            <p v-if="gpsStatus === 'error'" class="gps-message error">⚠️ {{ gpsError }}</p>
          </div>

          <label class="field">
            <span>출발 일자</span>
            <input v-model="profile.departureDate" type="date" :min="minDepartureDate" :max="maxDepartureDate" />
          </label>
          <label class="field">
            <span>출발 시간</span>
            <input v-model="profile.departureTime" type="time" :min="minDepartureTime" @change="ensureFutureDepartureTime" />
          </label>
          <label class="field">
            <span>희망 산행 시간</span>
            <select v-model.number="profile.desiredHikingMinutes">
              <option :value="60">1시간</option>
              <option :value="120">2시간</option>
              <option :value="180">3시간</option>
              <option :value="240">4시간</option>
            </select>
          </label>
          <div class="field wide-field">
            <span>동반자 유형</span>
            <div class="segment-group wrap">
              <label v-for="type in companionTypes" :key="type.value" class="segment-btn">
                <input type="radio" v-model="profile.companion" :value="type.value" name="companion_form" @change="submit" />
                <span>{{ type.label }}</span>
              </label>
            </div>
          </div>
          <button class="primary-btn wide-field" :class="{ loading }" type="submit" :disabled="loading">
            {{ loading ? '안전 등급 계산 중…' : '동반자 기준 안전코스 찾기' }}
          </button>
        </form>
      </section>

      <!-- ✅ 실시간 산행 조건 카드 -->
      <section v-if="weatherData" class="panel conditions-card">
        <div class="conditions-header">
          <div>
            <p class="eyebrow">오늘의 조건</p>
            <h2>실시간 산행 환경</h2>
          </div>
          <span :class="weatherData?.source === 'mock' ? 'live-badge mock-badge' : 'live-badge'">
            {{ weatherData?.source === 'mock' ? '추정 데이터' : '● LIVE' }}
          </span>
        </div>

        <!-- 날씨 안전도 게이지 -->
        <div class="weather-safety-gauge">
          <div class="gauge-label-row">
            <span class="gauge-label">기상 안전도</span>
            <span :class="['gauge-badge', weatherSafetyClass]">{{ weatherSafetyLabel }}</span>
          </div>
          <div class="gauge-track">
            <div
              class="gauge-fill"
              :class="weatherSafetyClass"
              :style="{ width: weatherSafetyScore + '%' }"
            ></div>
          </div>
          <span class="gauge-score">{{ weatherSafetyScore }}점</span>
        </div>

        <div class="conditions-grid">
          <div class="condition-item">
            <span class="condition-icon">{{ weatherIcon }}</span>
            <span class="condition-label">날씨</span>
            <strong class="condition-value">{{ weatherLabel }}<br/>{{ weatherData.temperature_c }}°C</strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">🌅</span>
            <span class="condition-label">오늘 일몰</span>
            <strong class="condition-value">{{ weatherData.sunset || '확인 중' }}</strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">💧</span>
            <span class="condition-label">강수량</span>
            <strong :class="['condition-value', weatherData.rainfall_mm > 0 ? 'warning' : '']">
              {{ weatherData.rainfall_mm ?? 0 }}mm
            </strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">💨</span>
            <span class="condition-label">풍속</span>
            <strong :class="['condition-value', weatherData.wind_speed_ms >= 5 ? 'warning' : '']">
              {{ weatherData.wind_speed_ms }}m/s
            </strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">💦</span>
            <span class="condition-label">습도</span>
            <strong class="condition-value">{{ weatherData.humidity_pct ?? '-' }}%</strong>
          </div>
          <div class="condition-item">
            <span class="condition-icon">🔥</span>
            <span class="condition-label">산불 위험</span>
            <strong :class="['condition-value', wildfireClass]">{{ wildfireLabel }}</strong>
          </div>
        </div>
      </section>

      </div><!-- /guide-left -->

      <!-- ── 오른쪽 컬럼: 결과 목록 (데스크톱) ── -->
      <div class="guide-right">

      <!-- 로딩 스켈레톤 -->
      <section v-if="loading" class="panel">
        <div class="skeleton-card">
          <div class="skeleton-line short"></div>
          <div class="skeleton-line full"></div>
          <div class="skeleton-line medium"></div>
        </div>
        <div class="skeleton-card">
          <div class="skeleton-line short"></div>
          <div class="skeleton-line full"></div>
          <div class="skeleton-line medium"></div>
        </div>
      </section>

      <!-- 준비 화면 (검색 전) -->
      <div v-if="resultState === 'idle' && !loading" class="idle-screen">

        <!-- 통계 배너 -->
        <div class="idle-stats">
          <div class="idle-stat">
            <span class="idle-stat-num">8,000<span class="idle-stat-unit">건+</span></span>
            <span class="idle-stat-label">연간 산악구조 출동</span>
          </div>
          <div class="idle-stat">
            <span class="idle-stat-num">{{ publicCourses.length || 631 }}<span class="idle-stat-unit">개</span></span>
            <span class="idle-stat-label">분석 탐방로</span>
          </div>
          <div class="idle-stat">
            <span class="idle-stat-num">3<span class="idle-stat-unit">단계</span></span>
            <span class="idle-stat-label">추천·주의·비추천</span>
          </div>
        </div>

        <!-- 빠른 산 선택 -->
        <div class="idle-quick-mountains">
          <p class="idle-section-label">⚡ 인기 산 바로 선택</p>
          <div class="mountain-chip-row">
            <button
              v-for="m in quickMountains"
              :key="m"
              class="mountain-chip"
              :class="{ active: profile.mountainName === m }"
              type="button"
              @click="selectQuickMountain(m)"
            >{{ m }}</button>
          </div>
        </div>

        <!-- 사용 방법 -->
        <div class="idle-how">
          <p class="idle-section-label">📋 이용 방법</p>
          <div class="how-steps">
            <div class="how-step">
              <span class="how-num">1</span>
              <span class="how-text">산 선택<br><small>날씨 자동 로드</small></span>
            </div>
            <div class="how-arrow">→</div>
            <div class="how-step">
              <span class="how-num">2</span>
              <span class="how-text">조건 입력<br><small>동반자·시간</small></span>
            </div>
            <div class="how-arrow">→</div>
            <div class="how-step">
              <span class="how-num">3</span>
              <span class="how-text">안전 등급<br><small>추천 코스 확인</small></span>
            </div>
            <div class="how-arrow">→</div>
            <div class="how-step">
              <span class="how-num">4</span>
              <span class="how-text">보호자 공유<br><small>세이프 링크</small></span>
            </div>
          </div>
        </div>

        <!-- 오늘의 안전 팁 -->
        <div class="idle-tip">
          <span class="idle-tip-icon">💡</span>
          <span class="idle-tip-text">{{ dailyTip }}</span>
        </div>

        <!-- 데이터 출처 -->
        <div class="idle-sources">
          <p class="idle-section-label">📡 연동 데이터</p>
          <div class="source-chips">
            <span class="source-chip">기상청 초단기실황</span>
            <span class="source-chip">한국천문연구원 일몰</span>
            <span class="source-chip">산림청 산불예보</span>
            <span class="source-chip">국립공원 탐방로</span>
            <span class="source-chip">재난위험지구</span>
            <span class="source-chip">브이월드 등산로</span>
          </div>
        </div>

      </div>

      <!-- 비추천 공지 -->
      <article v-if="resultState === 'no_safe_course'" class="empty-state">
        <span class="safety-badge red">비추천</span>
        <h3>현재 조건에서 권장할 코스가 없습니다</h3>
        <p>{{ agentSummary }}</p>
        <div class="chip-row">
          <button v-for="action in alternativeActions" :key="action" type="button">{{ action }}</button>
        </div>
      </article>

      <!-- 추천 코스 목록 -->
      <section v-if="!loading && recommendations.length" class="panel">
        <div class="section-title compact">
          <div>
            <p class="eyebrow">Recommended</p>
            <h2>추천 코스</h2>
          </div>
          <span class="mini-status">{{ displayPrimaryCourses.length }}개</span>
        </div>

        <!-- ✅ 개인화 라인 -->
        <div class="personalization-line">
          <span class="companion-chip">{{ companionChipLabel }}</span>
          <span class="personalization-dots">
            <span>날씨·일몰·동반자 조건 반영</span>
            <span v-if="weatherData">·</span>
            <span v-if="weatherData">{{ weatherLabel }} {{ weatherData.temperature_c }}°C</span>
          </span>
        </div>

        <p v-if="!strictMountainMatch" class="notice">
          선택한 산과 정확히 일치하는 후보가 부족해 주변 안전 후보를 함께 보여줍니다.
        </p>
        <div class="course-list">
          <CourseCard
            v-for="(course, index) in displayPrimaryCourses"
            :key="course.id"
            :course="course"
            :rank="index + 1"
            :is-selected="selectedCourse?.id === course.id"
            :is-favorite="favorites.some((f) => f.course_id === course.id)"
            @select="selectCourse"
            @toggle-favorite="toggleFavorite"
          />
        </div>
      </section>

      <!-- 대체 코스 -->
      <section v-if="!loading && nearbyAlternativeCourses.length" class="panel subtle-panel">
        <div class="section-title compact">
          <div>
            <p class="eyebrow">Alternative</p>
            <h2>주변 대체 코스</h2>
          </div>
          <span class="mini-status">{{ nearbyAlternativeCourses.length }}개</span>
        </div>
        <button
          v-for="course in nearbyAlternativeCourses"
          :key="course.id"
          class="alternative-row"
          type="button"
          @click="selectCourse(course)"
        >
          <span>
            <strong>{{ course.name }}</strong>
            <small>{{ course.mountain }} · {{ course.distance_km }}km · {{ durationLabel(course.duration_min) }}</small>
          </span>
          <span :class="['safety-badge', safetyClass(course)]">
            {{ course.safety_label || fallbackSafetyLabel(course) }}
          </span>
        </button>
      </section>

      <!-- 코스 상세 (지도 + 타임라인) -->
      <section v-if="selectedCourse" class="panel detail-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Course Detail</p>
            <h2>{{ selectedCourse.name }}</h2>
          </div>
          <button class="outline-btn" type="button" @click="activeTab = 'safeLink'">공유 카드</button>
        </div>
        <div class="detail-map">
          <div ref="detailMapEl" class="kakao-map" aria-label="선택 코스 카카오 지도"></div>
          <div class="legend">
            <span><i class="line green-line"></i>위치</span>
            <span><i class="line yellow-line"></i>주의</span>
          </div>
        </div>
        <div v-if="mapStatus" class="map-status-msg">
          <span class="info-icon">ℹ️</span>
          <span>{{ mapStatus }}</span>
        </div>
        <div class="route-summary">
          <div><strong>코스 단계</strong></div>
          <span class="mini-status">{{ courseTimelineItems.length }}단계</span>
        </div>
        <ol class="route-timeline" aria-label="코스 진행 단계">
          <li v-for="item in courseTimelineItems" :key="item.label + item.value">
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
          </li>
        </ol>
        <p class="detail-copy">{{ selectedCourse.agent_briefing }}</p>

        <!-- 재난위험지구 -->
        <div v-if="disasterZones.length" class="disaster-zone-panel">
          <p class="disaster-zone-title">⚠️ 인근 재난위험지구 {{ disasterZones.length }}개</p>
          <ul class="disaster-zone-list">
            <li v-for="zone in disasterZones.slice(0, 4)" :key="zone.id">
              <strong>{{ zone.district || zone.location }}</strong>
              <span v-if="zone.risk_factor"> · {{ zone.risk_factor }}</span>
            </li>
          </ul>
        </div>
      </section>

      </div><!-- /guide-right -->
    </section>

    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- 안전공유 탭 (구 세이프링크)                                          -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <section v-else-if="activeTab === 'safeLink'" class="screen-stack">
      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Safe Link</p>
            <h2>보호자 공유카드</h2>
          </div>
        </div>

        <article class="safe-link-card">
          <div class="safe-link-map">
            <div ref="safeLinkMapEl" class="kakao-map" aria-label="보호자 공유 카카오 지도"></div>
          </div>
          <div v-if="safeLinkMapStatus" class="map-status-msg">
            <span class="info-icon">ℹ️</span>
            <span>{{ safeLinkMapStatus }}</span>
          </div>
          <div class="safe-link-status">
            <span :class="['safety-badge', selectedCourse ? safetyClass(selectedCourse) : 'yellow']">
              {{ selectedCourse?.safety_label || '진단 대기' }}
            </span>
            <h3>{{ selectedCourse?.name || '안전 진단 후 공유 가능' }}</h3>
            <p>{{ safeLinkSummary }}</p>
          </div>
        </article>

        <!-- 현재 공유 상태 표시 (Mock UI) -->
        <div v-if="selectedCourse" class="safe-link-status-bar">
          <div class="status-dot" :class="selectedCourse.safety_decision === 'recommend' ? 'dot-green' : 'dot-yellow'"></div>
          <span>{{ selectedCourse.safe_link_preview?.status || '정상 이동' }}</span>
          <span class="status-time">마지막 확인: 방금 전</span>
        </div>
      </section>

      <!-- ── 산행 시작 / 세이프링크 생성 패널 ── -->
      <section class="panel share-panel">
        <!-- 세이프링크 활성화 전 -->
        <div v-if="!safeLinkActive && safeLinkStatus !== 'ended'">
          <p class="safe-link-guide">코스를 선택한 뒤 산행을 시작하면 보호자 전용 실시간 위치 링크가 생성됩니다.</p>
          <button
            class="primary-btn wide-field"
            type="button"
            :disabled="!selectedCourse || safeLinkStatus === 'creating'"
            @click="startHiking(selectedCourse)"
          >
            {{ safeLinkStatus === 'creating' ? '링크 생성 중…' : '산행 시작 &amp; 세이프링크 생성' }}
          </button>
          <p v-if="safeLinkError" class="share-status error">{{ safeLinkError }}</p>
        </div>

        <!-- 세이프링크 활성화 후 -->
        <div v-else-if="safeLinkActive" class="safe-link-active-panel">
          <div class="safe-link-live-badge">
            <span class="status-dot dot-green"></span> 산행 중 · GPS 추적 활성
            <span v-if="lastLocationTs" class="status-time">방금 전 갱신</span>
          </div>
          <p class="safe-link-url-label">보호자 링크 (공유하면 실시간 위치 확인 가능)</p>
          <div class="safe-link-url-box">
            <span class="safe-link-url-text">{{ safeLinkUrl }}</span>
          </div>
          <div class="share-actions">
            <button class="primary-btn" type="button" @click="copyAndShareSafeLink">링크 공유</button>
            <button class="outline-btn danger" type="button" @click="stopHikingAndRecord">산행 종료</button>
          </div>
        </div>

        <!-- 종료 후 -->
        <div v-else class="safe-link-ended">
          <p>산행이 종료되었습니다. 새 산행을 시작하려면 코스를 다시 선택하세요.</p>
        </div>

        <!-- 기존 문자 공유 -->
        <details class="share-message-details" v-if="selectedCourse">
          <summary>문자 공유 문구 보기</summary>
          <textarea class="share-message" :value="safeLinkMessage" readonly aria-label="보호자 공유 메시지"></textarea>
          <div class="share-actions">
            <button class="outline-btn" type="button" @click="shareSafeLink">문자 공유</button>
            <button class="outline-btn" type="button" @click="copySafeLinkMessage">문구 복사</button>
          </div>
        </details>
        <p v-if="shareStatus" class="share-status">{{ shareStatus }}</p>
      </section>

      <section class="panel kakao-actions">
        <a :class="['map-action', !selectedCourse ? 'disabled' : '']" :href="selectedCourse ? kakaoMapUrl : undefined" target="_blank" rel="noreferrer">
          <strong>카카오맵에서 위치 보기</strong>
          <span>보호자가 코스 위치를 바로 확인합니다.</span>
        </a>
        <a :class="['map-action', !selectedCourse ? 'disabled' : '']" :href="selectedCourse ? kakaoLocationSharingUrl : undefined" target="_blank" rel="noreferrer">
          <strong>카카오맵 친구위치 공유</strong>
          <span>현재 나의 위치를 친구들과 카카오맵으로 실시간 공유합니다.</span>
        </a>
        <!-- 119 신고 CTA -->
        <a class="map-action emergency" href="tel:119">
          <strong>🚨 119 신고</strong>
          <span>산악 사고 발생 시 즉시 119에 신고하세요.</span>
        </a>
      </section>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- 커뮤니티 탭                                                          -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <section v-else-if="activeTab === 'community'" class="screen-stack">

      <!-- ── 목록 뷰 ── -->
      <template v-if="communityView === 'list'">
        <section class="panel community-feed">
          <div class="section-title compact">
            <div>
              <p class="eyebrow">Community</p>
              <h2>동반 산행 커뮤니티</h2>
            </div>
            <button v-if="authUser" class="primary-btn" type="button" @click="openWrite">글쓰기</button>
            <button v-else class="outline-btn" type="button" @click="showAuthModal = true">로그인 후 글쓰기</button>
          </div>

          <div class="community-search-row">
            <input
              v-model="communitySearch"
              type="search"
              placeholder="제목·내용 검색…"
              class="community-search-input"
              @keydown.enter="loadPosts(1)"
            />
            <button class="outline-btn" type="button" @click="loadPosts(1)">검색</button>
          </div>
          <div class="filter-row">
            <button :class="{ active: communityCategory === '' }" type="button" @click="filterCategory('')">전체</button>
            <button :class="{ active: communityCategory === 'review' }" type="button" @click="filterCategory('review')">등산 후기</button>
            <button :class="{ active: communityCategory === 'question' }" type="button" @click="filterCategory('question')">질문</button>
            <button :class="{ active: communityCategory === 'safety' }" type="button" @click="filterCategory('safety')">안전 제보</button>
            <button :class="{ active: communityCategory === 'general' }" type="button" @click="filterCategory('general')">자유</button>
          </div>

          <div v-if="communityLoading" class="community-loading">게시글을 불러오는 중입니다…</div>
          <div v-else-if="communityError" class="error-banner">{{ communityError }}</div>
          <div v-else-if="communityPosts.length === 0" class="community-empty">
            <p>아직 게시글이 없습니다.</p>
            <button v-if="authUser" class="primary-btn" type="button" @click="openWrite">첫 글 작성하기</button>
          </div>

          <article
            v-for="post in communityPosts"
            :key="post.id"
            class="community-post-modern"
            style="cursor:pointer"
            @click="openPost(post.id)"
          >
            <div class="post-header">
              <div class="post-avatar">{{ post.author[0] }}</div>
              <div class="post-meta">
                <strong>{{ post.author }}</strong>
                <span>{{ formatRelativeTime(post.created_at) }} · <span class="category-tag">{{ post.category_label }}</span></span>
              </div>
              <span v-if="post.mountain" class="post-mountain">⛰️ {{ post.mountain }}</span>
            </div>
            <div class="post-content">
              <strong>{{ post.title }}</strong>
              <p>{{ post.content.length > 120 ? post.content.slice(0, 120) + '…' : post.content }}</p>
            </div>
            <div class="post-actions">
              <span>👍 {{ post.like_count }}</span>
              <span>💬 {{ post.comment_count }}</span>
              <span>👀 {{ post.view_count }}</span>
            </div>
          </article>

          <div v-if="communityTotal > 15" class="pagination-row">
            <button class="outline-btn" type="button" :disabled="communityPage === 1" @click="loadPosts(communityPage - 1)">이전</button>
            <span>{{ communityPage }} / {{ Math.ceil(communityTotal / 15) }}</span>
            <button class="outline-btn" type="button" :disabled="communityPage * 15 >= communityTotal" @click="loadPosts(communityPage + 1)">다음</button>
          </div>
        </section>
      </template>

      <!-- ── 상세 뷰 ── -->
      <template v-else-if="communityView === 'detail' && communityPost">
        <section class="panel">
          <div class="post-detail-nav">
            <button class="back-btn" type="button" @click="communityView = 'list'">← 목록</button>
            <span class="category-tag">{{ communityPost.category_label }}</span>
          </div>
          <h2 class="post-detail-title">{{ communityPost.title }}</h2>
          <div class="post-detail-meta">
            <span>{{ communityPost.author }}</span>
            <span>{{ formatRelativeTime(communityPost.created_at) }}</span>
            <span v-if="communityPost.mountain">⛰️ {{ communityPost.mountain }}</span>
            <span>👀 {{ communityPost.view_count }}</span>
          </div>
          <div class="post-detail-content">{{ communityPost.content }}</div>
          <div class="post-detail-actions">
            <button
              :class="['like-btn', { liked: communityPost.is_liked }]"
              type="button"
              @click="toggleLike"
            >👍 {{ communityPost.is_liked ? '좋아요 취소' : '좋아요' }} {{ communityPost.like_count }}</button>
            <template v-if="communityPost.is_owner">
              <button class="outline-btn" type="button" @click="openEdit">수정</button>
              <button class="outline-btn danger" type="button" @click="removePost">삭제</button>
            </template>
          </div>

          <!-- 댓글 -->
          <div class="comments-section">
            <h3>댓글 {{ communityPost.comments?.length ?? 0 }}개</h3>
            <div v-for="c in communityPost.comments" :key="c.id" class="comment-item">
              <div class="comment-header">
                <span class="comment-author">{{ c.author }}</span>
                <span class="comment-time">{{ formatRelativeTime(c.created_at) }}</span>
                <button v-if="c.is_owner" class="comment-delete" type="button" @click="removeComment(c.id)">삭제</button>
              </div>
              <p class="comment-content">{{ c.content }}</p>
            </div>
            <div v-if="authUser" class="comment-form">
              <textarea v-model="communityCommentInput" placeholder="댓글을 입력하세요…" rows="2"></textarea>
              <button class="primary-btn" type="button" :disabled="!communityCommentInput.trim()" @click="submitComment">댓글 달기</button>
            </div>
            <div v-else class="comment-login-prompt">
              <button class="outline-btn" type="button" @click="showAuthModal = true">로그인 후 댓글 작성</button>
            </div>
          </div>
        </section>
      </template>

      <!-- ── 작성/수정 뷰 ── -->
      <template v-else-if="communityView === 'write' || communityView === 'edit'">
        <section class="panel">
          <div class="section-title">
            <div>
              <p class="eyebrow">{{ communityView === 'edit' ? 'Edit' : 'Write' }}</p>
              <h2>{{ communityView === 'edit' ? '게시글 수정' : '게시글 작성' }}</h2>
            </div>
            <button class="outline-btn" type="button" @click="communityView = communityPost ? 'detail' : 'list'">취소</button>
          </div>
          <div v-if="writeError" class="error-banner" role="alert">{{ writeError }}</div>
          <form class="write-form" @submit.prevent="submitWrite">
            <label class="field">
              <span>카테고리</span>
              <select v-model="writeForm.category">
                <option value="review">등산 후기</option>
                <option value="question">질문</option>
                <option value="safety">안전 제보</option>
                <option value="general">자유게시판</option>
              </select>
            </label>
            <label class="field">
              <span>관련 산 (선택)</span>
              <input v-model="writeForm.mountain" type="text" placeholder="예: 북한산" />
            </label>
            <label class="field wide-field">
              <span>제목</span>
              <input v-model="writeForm.title" type="text" placeholder="제목을 입력하세요" required />
            </label>
            <label class="field wide-field">
              <span>내용</span>
              <textarea v-model="writeForm.content" placeholder="내용을 입력하세요" rows="8" required></textarea>
            </label>
            <button class="primary-btn wide-field" type="submit" :disabled="writeLoading">
              {{ writeLoading ? '저장 중…' : (communityView === 'edit' ? '수정 완료' : '게시하기') }}
            </button>
          </form>
        </section>
      </template>
    </section>

    <!-- ══════════════════════════════════════════════════════════════════ -->
    <!-- 내정보 탭                                                           -->
    <!-- ══════════════════════════════════════════════════════════════════ -->
    <section v-else class="screen-stack">

      <!-- ─── 로그인 유도 (미로그인) ─── -->
      <div v-if="!authUser" class="panel mypage-login-prompt">
        <p>로그인하면 산행 기록, 즐겨찾기, 긴급 연락처를 저장할 수 있습니다.</p>
        <button class="primary-btn" type="button" @click="showAuthModal = true">로그인 / 회원가입</button>
      </div>

      <!-- ─── 프로필 설정 ─── -->
      <section class="panel profile-settings">
        <div class="section-title compact">
          <div><p class="eyebrow">My Info</p><h2>개인 설정</h2></div>
          <span class="mini-status">{{ myProfileStatus }}</span>
        </div>
        <div class="field">
          <span>산행 경험</span>
          <div class="segment-group">
            <label class="segment-btn"><input type="radio" v-model="profile.experience" value="beginner" name="exp" /><span>🌱 초보</span></label>
            <label class="segment-btn"><input type="radio" v-model="profile.experience" value="intermediate" name="exp" /><span>👟 보통</span></label>
            <label class="segment-btn"><input type="radio" v-model="profile.experience" value="advanced" name="exp" /><span>⛰️ 숙련</span></label>
          </div>
        </div>
        <div class="field">
          <span>컨디션</span>
          <div class="segment-group">
            <label class="segment-btn"><input type="radio" v-model.number="profile.condition" :value="2" name="cond" /><span>📉 낮음</span></label>
            <label class="segment-btn"><input type="radio" v-model.number="profile.condition" :value="3" name="cond" /><span>➖ 보통</span></label>
            <label class="segment-btn"><input type="radio" v-model.number="profile.condition" :value="4" name="cond" /><span>💪 좋음</span></label>
          </div>
        </div>
      </section>

      <!-- ─── 즐겨찾기 코스 ─── -->
      <section class="panel">
        <div class="section-title compact">
          <div><p class="eyebrow">Favorites</p><h2>즐겨찾기 코스</h2></div>
          <span class="mini-status">{{ favorites.length }}개</span>
        </div>
        <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
        <div v-else-if="favorites.length === 0" class="community-empty"><p>즐겨찾기한 코스가 없습니다.<br>코스 카드의 ♡ 버튼으로 추가하세요.</p></div>
        <div v-else class="fav-list">
          <div v-for="fav in favorites" :key="fav.course_id" class="fav-item">
            <div class="fav-info">
              <strong>{{ fav.course_name }}</strong>
              <small>{{ fav.mountain }} · {{ fav.distance_km ?? '-' }}km · {{ fav.duration_min ? durationLabel(fav.duration_min) : '-' }}</small>
            </div>
            <button class="fav-remove-btn" type="button" title="즐겨찾기 해제" @click="removeFav(fav.course_id)">✕</button>
          </div>
        </div>
      </section>

      <!-- ─── 산행 기록 ─── -->
      <section class="panel">
        <div class="section-title compact">
          <div><p class="eyebrow">History</p><h2>산행 기록</h2></div>
          <span class="mini-status">{{ hikingRecords.length }}회</span>
        </div>
        <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
        <div v-else-if="hikingRecords.length === 0" class="community-empty"><p>아직 산행 기록이 없습니다.<br>산행 종료 시 자동으로 저장됩니다.</p></div>
        <div v-else class="hiking-record-list">
          <div v-for="rec in hikingRecords" :key="rec.id" class="hiking-record-item">
            <div class="record-info">
              <strong>{{ rec.mountain ? rec.mountain + ' ' : '' }}{{ rec.course_name }}</strong>
              <small>{{ rec.hiked_date }} · {{ rec.duration_min ? durationLabel(rec.duration_min) : '-' }}</small>
              <span v-if="rec.safety_label" :class="['safety-badge', rec.safety_label === '추천' ? 'green' : rec.safety_label === '주의' ? 'yellow' : 'gray']" style="font-size:11px">{{ rec.safety_label }}</span>
            </div>
            <button class="fav-remove-btn" type="button" @click="removeRecord(rec.id)">✕</button>
          </div>
        </div>
      </section>

      <!-- ─── 내가 쓴 글 ─── -->
      <section v-if="authUser" class="panel">
        <div class="section-title compact">
          <div><p class="eyebrow">My Posts</p><h2>내가 쓴 글</h2></div>
          <span class="mini-status">{{ myPostsTotal }}개</span>
        </div>
        <div v-if="myPostsLoading" class="community-loading">불러오는 중…</div>
        <div v-else-if="myPosts.length === 0" class="community-empty"><p>아직 작성한 글이 없습니다.</p></div>
        <div v-else>
          <div
            v-for="post in myPosts"
            :key="post.id"
            class="mypost-item"
            @click="goToPost(post.id)"
          >
            <span class="category-tag">{{ post.category_label }}</span>
            <strong>{{ post.title }}</strong>
            <small>{{ formatRelativeTime(post.created_at) }} · 👍 {{ post.like_count }} · 💬 {{ post.comment_count }}</small>
          </div>
        </div>
      </section>

      <!-- ─── 긴급 연락처 ─── -->
      <section class="panel">
        <div class="section-title compact">
          <div><p class="eyebrow">Emergency</p><h2>긴급 연락처</h2></div>
          <span class="mini-status">{{ emergencyContacts.length }}명</span>
        </div>
        <div v-if="!authUser" class="mypage-login-needed">로그인 후 이용 가능합니다.</div>
        <div v-else>
          <div v-for="contact in emergencyContacts" :key="contact.id" class="contact-item">
            <div class="contact-info">
              <strong>{{ contact.name }}</strong>
              <span v-if="contact.relation" class="contact-relation">{{ contact.relation }}</span>
              <a :href="`tel:${contact.phone}`" class="contact-phone">{{ contact.phone }}</a>
            </div>
            <button class="fav-remove-btn" type="button" @click="removeContact(contact.id)">✕</button>
          </div>
          <form class="contact-add-form" @submit.prevent="addContact">
            <input v-model="contactForm.name" type="text" placeholder="이름" required />
            <input v-model="contactForm.phone" type="tel" placeholder="전화번호" required />
            <input v-model="contactForm.relation" type="text" placeholder="관계 (선택)" />
            <button class="outline-btn" type="submit" :disabled="contactLoading">추가</button>
          </form>
          <p v-if="contactError" class="auth-error">{{ contactError }}</p>
        </div>
      </section>

      <!-- ─── 출발 전 체크리스트 ─── -->
      <section class="panel guardian-checklist">
        <div class="section-title compact">
          <div><p class="eyebrow">Checklist</p><h2>출발 전 체크리스트</h2></div>
          <span class="mini-status">{{ checkedCount }}/{{ checklistItems.length }}</span>
        </div>
        <label v-for="(item, i) in checklistItems" :key="item.id" class="custom-check-item">
          <input type="checkbox" class="hidden-check" v-model="item.checked" @change="saveChecklist" />
          <span class="check-box"></span>
          <span>{{ item.text }}</span>
          <button class="checklist-del-btn" type="button" @click.prevent="removeChecklistItem(i)">✕</button>
        </label>
        <div class="checklist-add-row">
          <input v-model="newChecklistText" type="text" placeholder="새 항목 추가…" @keydown.enter.prevent="addChecklistItem" />
          <button class="outline-btn" type="button" @click="addChecklistItem">추가</button>
        </div>
      </section>
    </section>
    <!-- ─── 로그인/회원가입 모달 ────────────────────────────────────────── -->
    <div v-if="showAuthModal" class="modal-overlay" role="dialog" aria-modal="true" @click.self="showAuthModal = false">
      <div class="auth-modal">
        <button class="modal-close" type="button" aria-label="닫기" @click="showAuthModal = false">✕</button>
        <div class="auth-tabs">
          <button :class="{ active: authMode === 'login' }" type="button" @click="authMode = 'login'; authError = ''">로그인</button>
          <button :class="{ active: authMode === 'register' }" type="button" @click="authMode = 'register'; authError = ''">회원가입</button>
        </div>
        <form class="auth-form" @submit.prevent="authMode === 'login' ? login() : register()">
          <div v-if="authError" class="auth-error">{{ authError }}</div>
          <label class="field">
            <span>아이디</span>
            <input v-model="authForm.username" type="text" placeholder="아이디 (3자 이상)" autocomplete="username" required />
          </label>
          <label v-if="authMode === 'register'" class="field">
            <span>닉네임</span>
            <input v-model="authForm.nickname" type="text" placeholder="닉네임 (미입력 시 아이디 사용)" />
          </label>
          <label class="field">
            <span>비밀번호</span>
            <input v-model="authForm.password" type="password" placeholder="비밀번호 (6자 이상)" autocomplete="current-password" required />
          </label>
          <label v-if="authMode === 'register'" class="field">
            <span>이메일 (선택)</span>
            <input v-model="authForm.email" type="email" placeholder="이메일" />
          </label>
          <button class="primary-btn wide-field" type="submit" :disabled="authLoading">
            {{ authLoading ? '처리 중…' : (authMode === 'login' ? '로그인' : '가입하기') }}
          </button>
          <p v-if="authUser" class="auth-logout-row">
            <button class="outline-btn" type="button" @click="logout">로그아웃</button>
          </p>
        </form>
      </div>
    </div>
  </main>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue';
import {
  fetchCourses, fetchDataSources, fetchRecommendations, fetchDisasterZones, getSafeLink, fetchWeather,
  apiRegister, apiLogin, apiLogout, apiMe,
  fetchPosts, fetchPost, createPost, updatePost, deletePost, likePost, createComment, deleteComment,
  fetchMyPosts, fetchHikingRecords, createHikingRecord, deleteHikingRecord,
  fetchFavorites, addFavorite, removeFavorite,
  fetchEmergencyContacts, addEmergencyContact, removeEmergencyContact,
} from './api';
import { useLocation } from './composables/useLocation.js';
import { useKakaoMap } from './composables/useKakaoMap.js';
import { useSafeLink, useGuardianView } from './composables/useSafeLink.js';
import { safetyClass, fallbackSafetyLabel, durationLabel, daylightLabel, daylightColor } from './utils/courseHelpers.js';
import CourseCard from './components/CourseCard.vue';

// ─── 보호자 뷰 감지 ───────────────────────────────────────────────────────
const _hashMatch = window.location.hash.match(/^#\/safe\/(.+)$/);
const _guardianSessionId = _hashMatch ? _hashMatch[1] : null;
const isGuardianView = computed(() => !!_guardianSessionId);

const guardianMapEl = ref(null);
const guardianSession = ref(null);
const guardianLoading = ref(true);
const guardianPollError = ref('');
let _guardianPollTimer = null;

async function fetchGuardianSession() {
  if (!_guardianSessionId) return;
  try {
    guardianSession.value = await getSafeLink(_guardianSessionId);
    guardianPollError.value = '';
    await nextTick();
    if (guardianMapEl.value && guardianSession.value) {
      renderGuardianMap(guardianMapEl.value, guardianSession.value);
    }
  } catch {
    guardianPollError.value = '위치 정보를 불러오지 못했습니다.';
  } finally {
    guardianLoading.value = false;
  }
}

function refreshGuardian() {
  guardianLoading.value = true;
  fetchGuardianSession();
}

const guardianLastUpdate = computed(() => {
  const ts = guardianSession.value?.location_ts;
  if (!ts) return '위치 미수신';
  const elapsed = Math.floor(Date.now() / 1000 - ts);
  if (elapsed < 60) return `${elapsed}초 전`;
  return `${Math.floor(elapsed / 60)}분 전`;
});

const guardianStatusLabel = computed(() => {
  if (!guardianSession.value) return '연결 중';
  if (guardianSession.value.status === 'ended') return '산행 종료';
  const d = guardianSession.value.safety_decision;
  return d === 'not_recommended' ? '주의 필요' : d === 'caution' ? '주의 구간' : '정상 이동';
});

const guardianStatusClass = computed(() => {
  if (!guardianSession.value || guardianSession.value.status === 'ended') return 'gray';
  const d = guardianSession.value.safety_decision;
  return d === 'not_recommended' ? 'red' : d === 'caution' ? 'yellow' : 'green';
});

// ─── 상태 ─────────────────────────────────────────────────────────────────
const activeTab = ref('guide');
const loading = ref(false);
const error = ref('');
const publicCourses = ref([]);
const dataSources = ref([]);
const recommendations = ref([]);
const alternatives = ref([]);
const selectedCourse = ref(null);
const resultState = ref('idle');
const agentSummary = ref('산과 출발 조건을 선택하면 실제 탐방로, 날씨, 일몰, 위험 데이터를 종합해 안전 등급을 계산합니다.');
const alternativeActions = ref([]);
const detailMapEl = ref(null);
const safeLinkMapEl = ref(null);
const disasterZones = ref([]);
const shareStatus = ref('');
const weatherData = ref(null); // 실시간 날씨 데이터

// ─── Composables ──────────────────────────────────────────────────────────
const { location, gpsStatus, gpsError, detectGPS } = useLocation();
const { mapStatus, safeLinkMapStatus, renderDetailMap, renderSafeLinkMap, renderGuardianMap, addDisasterZoneOverlays } = useKakaoMap();
const { sessionId: safeLinkSessionId, sessionStatus: safeLinkStatus, shareUrl: safeLinkUrl, isActive: safeLinkActive, errorMsg: safeLinkError, lastLocationTs, startHiking, stopHiking } = useSafeLink();

// ─── 날짜/시간 초기값 ────────────────────────────────────────────────────
const initialDepartureAt = addMinutes(new Date(), 5);
const minDepartureDate = formatDateForInput(initialDepartureAt);
const maxDepartureDate = formatDateForInput(addDays(initialDepartureAt, 3));
const minDepartureTime = computed(() =>
  profile.departureDate === minDepartureDate ? formatTimeForInput(addMinutes(new Date(), 5)) : undefined,
);

// ─── 프로필 ───────────────────────────────────────────────────────────────
const profile = reactive({
  mountainName: '',
  departureDate: minDepartureDate,
  departureTime: formatTimeForInput(initialDepartureAt),
  availableMinutes: 240,
  desiredHikingMinutes: 120,
  companion: 'vulnerable',
  experience: 'beginner',
  condition: 4,
  intensity: 'moderate',
  purpose: 'balanced',
  transport: 'public',
  maxDistanceKm: 30,
});

// ─── 정적 데이터 ──────────────────────────────────────────────────────────
const guardianChecklist = [
  '아이와 보호자 연락처를 서로 확인했어요',
  '물, 간식, 보조배터리를 챙겼어요',
  '입산 통제와 날씨 변화를 한 번 더 확인했어요',
  '해 지기 전에 내려오는 계획을 세웠어요',
];

const companionTypes = [
  { value: 'vulnerable', label: '어린이·노약자 동반' },
  { value: 'family', label: '가족 동반' },
  { value: 'solo', label: '혼자 산행' },
];

// ─── 인증 상태 ────────────────────────────────────────────────────────────
const authToken = ref(localStorage.getItem('auth_token') || '');
const authUser = ref(null);
const showAuthModal = ref(false);
const authMode = ref('login');
const authForm = reactive({ username: '', password: '', nickname: '', email: '' });
const authLoading = ref(false);
const authError = ref('');

// ─── 커뮤니티 상태 ────────────────────────────────────────────────────────
const communityView = ref('list'); // 'list' | 'detail' | 'write' | 'edit'
const communityPosts = ref([]);
const communityPost = ref(null);
const communityCategory = ref('');
const communitySearch = ref('');
const communityPage = ref(1);
const communityTotal = ref(0);
const communityLoading = ref(false);
const communityError = ref('');
const communityCommentInput = ref('');
const writeForm = reactive({ title: '', content: '', category: 'general', mountain: '', course_name: '' });
const writeError = ref('');
const writeLoading = ref(false);

// ─── 내정보 상태 ──────────────────────────────────────────────────────────
const favorites = ref([]);
const hikingRecords = ref([]);
const myPosts = ref([]);
const myPostsTotal = ref(0);
const myPostsLoading = ref(false);
const emergencyContacts = ref([]);
const contactForm = reactive({ name: '', phone: '', relation: '' });
const contactLoading = ref(false);
const contactError = ref('');

// ─── 체크리스트 ───────────────────────────────────────────────────────────
const DEFAULT_CHECKLIST = [
  '아이와 보호자 연락처를 서로 확인했어요',
  '물, 간식, 보조배터리를 챙겼어요',
  '입산 통제와 날씨 변화를 한 번 더 확인했어요',
  '해 지기 전에 내려오는 계획을 세웠어요',
];

function loadChecklistFromStorage() {
  try {
    const saved = localStorage.getItem('olla_checklist');
    if (saved) return JSON.parse(saved);
  } catch {}
  return DEFAULT_CHECKLIST.map((text, i) => ({ id: i, text, checked: false }));
}

const checklistItems = ref(loadChecklistFromStorage());
const newChecklistText = ref('');
const checkedCount = computed(() => checklistItems.value.filter((i) => i.checked).length);

// ─── GPS 버튼 ─────────────────────────────────────────────────────────────
const gpsBtnTitle = computed(() => {
  if (gpsStatus.value === 'loading') return '위치 감지 중...';
  if (gpsStatus.value === 'success') return '위치 감지 완료';
  if (gpsStatus.value === 'error') return '위치 감지 실패 — 다시 시도';
  return '내 위치 자동 감지';
});

async function handleGPS() {
  const success = await detectGPS();
  if (success) {
    syncLocationToSelectedMountain();
    await submit();
  }
}

// ─── 라이프사이클 ─────────────────────────────────────────────────────────
onMounted(async () => {
  if (isGuardianView.value) {
    fetchGuardianSession();
    _guardianPollTimer = setInterval(fetchGuardianSession, 20000);
  } else {
    await loadMe();
    loadEverything();
    loadPosts();
    if (authToken.value) { loadMyPageData(); loadMyPosts(); }
  }
});

onUnmounted(() => {
  if (_guardianPollTimer) clearInterval(_guardianPollTimer);
});

// ─── 내정보 데이터 로드 ───────────────────────────────────────────────────
async function loadMyPageData() {
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

async function loadMyPosts() {
  if (!authToken.value) return;
  myPostsLoading.value = true;
  try {
    const data = await fetchMyPosts(authToken.value);
    myPosts.value = data.posts || [];
    myPostsTotal.value = data.total || 0;
  } catch {}
  finally { myPostsLoading.value = false; }
}

// ─── 즐겨찾기 함수 ────────────────────────────────────────────────────────
async function toggleFavorite(course) {
  if (!authUser.value) { showAuthModal.value = true; return; }
  const isFav = favorites.value.some((f) => f.course_id === course.id);
  if (isFav) {
    await removeFavorite(course.id, authToken.value).catch(() => {});
    favorites.value = favorites.value.filter((f) => f.course_id !== course.id);
  } else {
    try {
      await addFavorite({
        course_id: course.id,
        course_name: course.name,
        mountain: course.mountain,
        distance_km: course.distance_km,
        duration_min: course.duration_min,
        difficulty: course.difficulty,
      }, authToken.value);
      favorites.value.unshift({
        course_id: course.id,
        course_name: course.name,
        mountain: course.mountain,
        distance_km: course.distance_km,
        duration_min: course.duration_min,
        difficulty: course.difficulty,
      });
    } catch {}
  }
}

async function removeFav(courseId) {
  await removeFavorite(courseId, authToken.value).catch(() => {});
  favorites.value = favorites.value.filter((f) => f.course_id !== courseId);
}

// ─── 산행 기록 함수 ───────────────────────────────────────────────────────
async function saveHikingRecord(course) {
  if (!authToken.value || !course) return;
  try {
    const rec = await createHikingRecord({
      mountain: course.mountain || '',
      course_name: course.name || '',
      hiked_date: new Date().toISOString().slice(0, 10),
      duration_min: course.duration_min || 0,
      weather_summary: weatherData.value
        ? `${weatherData.value.temperature_c}°C, 강수 ${weatherData.value.rainfall_mm}mm`
        : '',
      safety_label: course.safety_label || '',
    }, authToken.value);
    hikingRecords.value.unshift(rec);
  } catch {}
}

async function removeRecord(id) {
  await deleteHikingRecord(id, authToken.value).catch(() => {});
  hikingRecords.value = hikingRecords.value.filter((r) => r.id !== id);
}

// ─── 긴급 연락처 함수 ─────────────────────────────────────────────────────
async function addContact() {
  contactLoading.value = true;
  contactError.value = '';
  try {
    const contact = await addEmergencyContact(contactForm, authToken.value);
    emergencyContacts.value.push(contact);
    contactForm.name = ''; contactForm.phone = ''; contactForm.relation = '';
  } catch (err) { contactError.value = err.message; }
  finally { contactLoading.value = false; }
}

async function removeContact(id) {
  await removeEmergencyContact(id, authToken.value).catch(() => {});
  emergencyContacts.value = emergencyContacts.value.filter((c) => c.id !== id);
}

// ─── 체크리스트 함수 ──────────────────────────────────────────────────────
function saveChecklist() {
  try { localStorage.setItem('olla_checklist', JSON.stringify(checklistItems.value)); } catch {}
}

function addChecklistItem() {
  const text = newChecklistText.value.trim();
  if (!text) return;
  const id = Date.now();
  checklistItems.value.push({ id, text, checked: false });
  newChecklistText.value = '';
  saveChecklist();
}

function removeChecklistItem(index) {
  checklistItems.value.splice(index, 1);
  saveChecklist();
}

// ─── 커뮤니티 → 내정보 탭 연동 ───────────────────────────────────────────
function goToPost(id) {
  activeTab.value = 'community';
  openPost(id);
}

// ─── 인증 함수 ────────────────────────────────────────────────────────────
async function loadMe() {
  if (!authToken.value) return;
  try {
    const data = await apiMe(authToken.value);
    authUser.value = data.user;
    if (!data.user) { authToken.value = ''; localStorage.removeItem('auth_token'); }
  } catch { authToken.value = ''; localStorage.removeItem('auth_token'); }
}

async function login() {
  authLoading.value = true;
  authError.value = '';
  try {
    const data = await apiLogin({ username: authForm.username, password: authForm.password });
    authToken.value = data.token;
    authUser.value = data.user;
    localStorage.setItem('auth_token', data.token);
    showAuthModal.value = false;
    authForm.username = ''; authForm.password = '';
    if (communityView.value === 'list') loadPosts();
    loadMyPageData(); loadMyPosts();
  } catch (err) { authError.value = err.message; }
  finally { authLoading.value = false; }
}

async function register() {
  authLoading.value = true;
  authError.value = '';
  try {
    const data = await apiRegister({ username: authForm.username, password: authForm.password, nickname: authForm.nickname, email: authForm.email });
    authToken.value = data.token;
    authUser.value = data.user;
    localStorage.setItem('auth_token', data.token);
    showAuthModal.value = false;
    authForm.username = ''; authForm.password = ''; authForm.nickname = ''; authForm.email = '';
    loadMyPageData(); loadMyPosts();
  } catch (err) { authError.value = err.message; }
  finally { authLoading.value = false; }
}

async function logout() {
  await apiLogout(authToken.value).catch(() => {});
  authToken.value = '';
  authUser.value = null;
  localStorage.removeItem('auth_token');
  showAuthModal.value = false;
  communityView.value = 'list';
  favorites.value = [];
  hikingRecords.value = [];
  myPosts.value = [];
  emergencyContacts.value = [];
  loadPosts();
}

// ─── 커뮤니티 함수 ────────────────────────────────────────────────────────
async function loadPosts(page = 1) {
  communityLoading.value = true;
  communityError.value = '';
  communityPage.value = page;
  try {
    const data = await fetchPosts({ category: communityCategory.value, search: communitySearch.value, page }, authToken.value);
    communityPosts.value = data.posts;
    communityTotal.value = data.total;
  } catch (err) { communityError.value = err.message; }
  finally { communityLoading.value = false; }
}

async function openPost(id) {
  communityLoading.value = true;
  try {
    communityPost.value = await fetchPost(id, authToken.value);
    communityView.value = 'detail';
  } catch (err) { communityError.value = err.message; }
  finally { communityLoading.value = false; }
}

function openWrite() {
  Object.assign(writeForm, { title: '', content: '', category: 'general', mountain: '', course_name: '' });
  writeError.value = '';
  communityPost.value = null;
  communityView.value = 'write';
}

function openEdit() {
  Object.assign(writeForm, {
    title: communityPost.value.title,
    content: communityPost.value.content,
    category: communityPost.value.category,
    mountain: communityPost.value.mountain,
    course_name: communityPost.value.course_name,
  });
  writeError.value = '';
  communityView.value = 'edit';
}

async function submitWrite() {
  writeLoading.value = true;
  writeError.value = '';
  try {
    if (communityView.value === 'edit') {
      communityPost.value = await updatePost(communityPost.value.id, writeForm, authToken.value);
      communityView.value = 'detail';
    } else {
      const post = await createPost(writeForm, authToken.value);
      await loadPosts();
      communityPost.value = await fetchPost(post.id, authToken.value);
      communityView.value = 'detail';
    }
  } catch (err) { writeError.value = err.message; }
  finally { writeLoading.value = false; }
}

async function toggleLike() {
  if (!authUser.value) { showAuthModal.value = true; return; }
  try {
    const data = await likePost(communityPost.value.id, authToken.value);
    communityPost.value.is_liked = data.is_liked;
    communityPost.value.like_count = data.like_count;
  } catch {}
}

async function submitComment() {
  if (!communityCommentInput.value.trim()) return;
  try {
    const comment = await createComment(communityPost.value.id, communityCommentInput.value, authToken.value);
    communityPost.value.comments.push(comment);
    communityPost.value.comment_count = (communityPost.value.comment_count || 0) + 1;
    communityCommentInput.value = '';
  } catch (err) { communityError.value = err.message; }
}

async function removeComment(id) {
  try {
    await deleteComment(id, authToken.value);
    communityPost.value.comments = communityPost.value.comments.filter((c) => c.id !== id);
    communityPost.value.comment_count = Math.max(0, (communityPost.value.comment_count || 1) - 1);
  } catch {}
}

async function removePost() {
  if (!confirm('게시글을 삭제하시겠습니까?')) return;
  try {
    await deletePost(communityPost.value.id, authToken.value);
    communityPost.value = null;
    communityView.value = 'list';
    loadPosts();
  } catch (err) { communityError.value = err.message; }
}

function filterCategory(cat) {
  communityCategory.value = cat;
  loadPosts(1);
}

function formatRelativeTime(isoString) {
  const diff = Math.floor((Date.now() - new Date(isoString)) / 1000);
  if (diff < 60) return '방금 전';
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  return `${Math.floor(diff / 86400)}일 전`;
}

async function loadEverything() {
  await Promise.all([loadSources(), loadCourses()]);
  if (!profile.mountainName && mountainOptions.value.length) {
    profile.mountainName = mountainOptions.value[0].name;
  }
  syncLocationToSelectedMountain();
  loadWeather();
  // 자동 검색하지 않음 — 사용자가 버튼을 눌러야 시작
}

async function loadWeather() {
  const mountain = mountainOptions.value.find((m) => m.name === profile.mountainName);
  const lat = location.value?.lat ?? mountain?.lat ?? 37.5665;
  const lng = location.value?.lng ?? mountain?.lng ?? 126.978;
  try {
    weatherData.value = await fetchWeather({ lat, lng });
  } catch {}
}

async function loadSources() {
  try {
    const data = await fetchDataSources();
    dataSources.value = data.connected_sources || [];
  } catch { dataSources.value = []; }
}

async function loadCourses() {
  try {
    const data = await fetchCourses();
    publicCourses.value = data.courses || [];
  } catch { publicCourses.value = []; }
}

async function submit() {
  loading.value = true;
  error.value = '';
  try {
    const [data, zonesData] = await Promise.all([
      fetchRecommendations({ profile, location: location.value }),
      fetchDisasterZones(profile.mountainName).catch(() => ({ zones: [] })),
    ]);
    recommendations.value = data.recommendations || [];
    alternatives.value = data.alternatives || [];
    resultState.value = data.result_state || 'has_recommendations';
    agentSummary.value = data.agent_summary || recommendations.value[0]?.agent_briefing || '';
    alternativeActions.value = data.alternative_actions || [];
    weatherData.value = data.weather || recommendations.value[0]?.weather || weatherData.value;
    disasterZones.value = zonesData.zones || [];
    selectedCourse.value = displayPrimaryCourses.value[0] || recommendations.value[0] || null;
    renderMaps();
  } catch (err) {
    error.value = err.message || '추천 데이터를 불러오지 못했습니다.';
  } finally {
    loading.value = false;
  }
}

function handleMountainChange() {
  syncLocationToSelectedMountain();
  loadWeather();
  // 산 변경만으로는 검색하지 않음
}

function ensureFutureDepartureTime() {
  if (profile.departureDate !== minDepartureDate) return;
  const minimum = minDepartureTime.value;
  if (minimum && (!profile.departureTime || profile.departureTime < minimum)) {
    profile.departureTime = minimum;
  }
}

function syncLocationToSelectedMountain() {
  const selected = mountainOptions.value.find((item) => item.name === profile.mountainName);
  if (selected?.lat && selected?.lng) {
    location.value = { lat: selected.lat, lng: selected.lng };
  }
}

function selectCourse(course) {
  selectedCourse.value = course;
  shareStatus.value = '';
  renderMaps();
}

// ─── 감시자 ───────────────────────────────────────────────────────────────
watch([selectedCourse, activeTab], () => { renderMaps(); });
watch(activeTab, (tab) => {
  if (tab === 'community' && communityPosts.value.length === 0) loadPosts();
  if (tab === 'myPage' && authUser.value && myPosts.value.length === 0) loadMyPosts();
});
watch(() => [profile.departureDate, profile.departureTime], () => { ensureFutureDepartureTime(); });

// ─── 계산 속성 ────────────────────────────────────────────────────────────

// 날씨 조건 표시용
const weatherIcon = computed(() => {
  const w = weatherData.value;
  if (!w) return '🌤️';
  if (w.rainfall_mm >= 10) return '🌧️';
  if (w.rainfall_mm > 0) return '🌦️';
  if (w.wind_speed_ms >= 8) return '💨';
  return '☀️';
});

const weatherLabel = computed(() => {
  const w = weatherData.value;
  if (!w) return '확인 중';
  if (w.rainfall_mm >= 10) return '비';
  if (w.rainfall_mm > 0) return '흐리고 비';
  if (w.wind_speed_ms >= 8) return '강풍';
  return '맑음';
});

const wildfireClass = computed(() => {
  const risk = weatherData.value?.wildfire_risk || 'low';
  return { low: 'safe', medium: 'warning', high: 'danger', very_high: 'danger' }[risk] || 'safe';
});

const wildfireLabel = computed(() => {
  return { low: '낮음', medium: '중간', high: '높음', very_high: '매우 높음' }[weatherData.value?.wildfire_risk] || '낮음';
});

const weatherSafetyScore = computed(() => {
  const w = weatherData.value;
  if (!w) return 100;
  let score = 100;
  const rainfall = parseFloat(w.rainfall_mm ?? 0);
  const wind = parseFloat(w.wind_speed_ms ?? 0);
  const temp = parseFloat(w.temperature_c ?? 15);
  if (rainfall >= 10) score -= 45;
  else if (rainfall > 0) score -= 20;
  if (wind >= 8) score -= 30;
  else if (wind >= 5) score -= 15;
  if (temp <= 0 || temp >= 32) score -= 20;
  if (rainfall >= 5 && wind >= 5) score -= 20;
  if (temp <= 2 && rainfall > 0) score -= 15;
  if (temp >= 30 && wind < 2) score -= 10;
  return Math.max(score, 0);
});

const weatherSafetyLabel = computed(() => {
  const s = weatherSafetyScore.value;
  if (s >= 80) return '산행 적합';
  if (s >= 55) return '주의 필요';
  return '산행 부적합';
});

const weatherSafetyClass = computed(() => {
  const s = weatherSafetyScore.value;
  if (s >= 80) return 'safe';
  if (s >= 55) return 'caution';
  return 'danger';
});

const quickMountains = ['관악산', '북한산', '청계산', '도봉산', '남산', '수락산', '설악산', '지리산'];

const dailyTip = computed(() => {
  const h = new Date().getHours();
  if (h < 6)  return '이른 새벽 산행은 일출 후 시작하세요. 저체온과 시야 확보가 중요합니다.';
  if (h < 10) return '오전 이른 출발이 가장 안전합니다. 일몰 전 여유 있는 하산을 꼭 지켜주세요.';
  if (h < 14) return '한낮 산행 시 충분한 수분 보충과 그늘 휴식을 챙기세요. 자외선 차단도 필수입니다.';
  if (h < 17) return '오후 출발 시 일몰 시간을 반드시 확인하세요. 올라가 하산 여유 시간을 자동으로 계산합니다.';
  return '일몰이 가까운 시간입니다. 오늘 산행은 내일 아침으로 연기하거나 짧은 산책 코스를 선택하세요.';
});

function selectQuickMountain(mountainName) {
  profile.mountainName = mountainName;
  handleMountainChange();
}

// 동반자 칩 라벨
const companionChipLabel = computed(() => {
  const map = {
    vulnerable: '👨‍👧 어린이·노약자 동반 기준',
    family:     '👨‍👩‍👦 가족 동반 기준',
    solo:       '🧍 개인 산행 기준',
  };
  return map[profile.companion] || '동반자 기준';
});

const mountainOptions = computed(() => {
  const buckets = new Map();
  for (const course of publicCourses.value) {
    const name = course.mountain || '산 정보 없음';
    if (!buckets.has(name)) {
      buckets.set(name, { name, count: 0, lat: course.lat, lng: course.lng, region: course.region });
    }
    const item = buckets.get(name);
    item.count += 1;
    if (!item.lat && course.lat) item.lat = course.lat;
    if (!item.lng && course.lng) item.lng = course.lng;
  }
  return [...buckets.values()]
    .filter((item) => item.name && item.name !== '산 정보 없음')
    .filter((item) => item.name !== '국립공원')
    .sort((a, b) => b.count - a.count)
    .slice(0, 40);
});

const selectedMountainName = computed(() => profile.mountainName || mountainOptions.value[0]?.name || '');
const normalizedSelectedMountain = computed(() => normalizeText(selectedMountainName.value));
const matchedRecommendations = computed(() =>
  recommendations.value.filter((course) => isSelectedMountainCourse(course)),
);
const strictMountainMatch = computed(() => matchedRecommendations.value.length > 0);
const displayPrimaryCourses = computed(() =>
  (strictMountainMatch.value ? matchedRecommendations.value : recommendations.value).slice(0, 3),
);
const nearbyAlternativeCourses = computed(() => {
  const seen = new Set(displayPrimaryCourses.value.map((c) => c.id));
  return [...recommendations.value, ...alternatives.value]
    .filter((c) => !seen.has(c.id))
    .filter((c) => !isSelectedMountainCourse(c))
    .slice(0, 3);
});

const selectedCourseLat = computed(() => Number(selectedCourse.value?.lat));
const selectedCourseLng = computed(() => Number(selectedCourse.value?.lng));
const hasSelectedCourseLocation = computed(
  () => Number.isFinite(selectedCourseLat.value) && Number.isFinite(selectedCourseLng.value),
);
const courseTimelineItems = computed(() => {
  const highlights = selectedCourse.value?.highlights || [];
  const parsed = highlights.map(parseTimelineHighlight).filter(Boolean);
  if (parsed.length) return parsed;
  if (!selectedCourse.value) return [];
  return [{ label: '코스', value: selectedCourse.value.name }];
});
const kakaoMapUrl = computed(() => {
  if (!hasSelectedCourseLocation.value) return '';
  return `https://map.kakao.com/link/map/${encodeURIComponent(selectedCourse.value.name)},${selectedCourseLat.value},${selectedCourseLng.value}`;
});
const kakaoLocationSharingUrl = computed(() => {
  if (!hasSelectedCourseLocation.value) return '';
  return 'https://m.map.kakao.com/scheme/open?page=locationsharing';
});
const safeLinkSummary = computed(() => {
  if (!selectedCourse.value) return '안전 진단 후 보호자에게 보낼 공유 카드가 생성됩니다.';
  return `${selectedCourse.value.mountain} ${selectedCourse.value.name} 코스의 안전 등급과 카카오 지도 위치를 보호자에게 공유합니다.`;
});
const myProfileStatus = computed(() => {
  const companion = companionTypes.find((t) => t.value === profile.companion)?.label || '동반자';
  return companion.replace(' 동반', '');
});
const safeLinkMessage = computed(() => {
  if (!selectedCourse.value) return '안전 진단 후 공유 메시지가 생성됩니다.';
  const course = selectedCourse.value;
  const riskFactors = (course.risk_factors || []).slice(0, 2).join(', ') || '특이 위험 요인 없음';
  const locationLine = hasSelectedCourseLocation.value
    ? `카카오맵 위치: ${kakaoMapUrl.value}`
    : '카카오맵 위치: 좌표 정보 없음';
  return [
    '[올라 안전공유]',
    `산/코스: ${course.mountain} · ${course.name}`,
    `안전 등급: ${course.safety_label || fallbackSafetyLabel(course)}`,
    `예상 산행: 약 ${durationLabel(course.duration_min)} / 거리 ${course.distance_km}km`,
    `하산 여유: ${daylightLabel(course.daylight_margin_min)}`,
    `주의 요인: ${riskFactors}`,
    locationLine,
    '현장 통제, 기상 변화, 입산 제한 여부를 함께 확인해 주세요.',
  ].join('\n');
});

// ─── 산행 종료 + 기록 저장 ───────────────────────────────────────────────
async function stopHikingAndRecord() {
  await stopHiking();
  await saveHikingRecord(selectedCourse.value);
}

// ─── 지도 렌더링 ──────────────────────────────────────────────────────────
async function renderMaps() {
  await nextTick();
  if (activeTab.value === 'guide') {
    renderDetailMap(detailMapEl.value, selectedCourse.value, disasterZones.value, location.value);
  }
  if (activeTab.value === 'safeLink') {
    renderSafeLinkMap(safeLinkMapEl.value, selectedCourse.value);
  }
}

// ─── Safe Link 공유 ───────────────────────────────────────────────────────
async function copyAndShareSafeLink() {
  const url = safeLinkUrl.value;
  if (!url) return;
  if (navigator.share) {
    try {
      await navigator.share({
        title: '올라 세이프링크',
        text: `${selectedCourse.value?.mountain} ${selectedCourse.value?.name} 산행 중입니다. 아래 링크에서 실시간 위치를 확인하세요.`,
        url,
      });
      return;
    } catch (err) {
      if (err?.name === 'AbortError') return;
    }
  }
  try {
    await navigator.clipboard.writeText(url);
    shareStatus.value = '보호자 링크를 복사했습니다.';
  } catch {
    shareStatus.value = '링크를 직접 복사해 주세요: ' + url;
  }
}

// ─── 공유 기능 ────────────────────────────────────────────────────────────
async function copySafeLinkMessage() {
  if (!selectedCourse.value) return;
  try {
    await navigator.clipboard.writeText(safeLinkMessage.value);
    shareStatus.value = '보호자 공유 문구를 복사했습니다.';
  } catch {
    shareStatus.value = '브라우저에서 복사를 허용하지 않았습니다. 문구를 직접 선택해 복사해 주세요.';
  }
}

async function shareSafeLink() {
  if (!selectedCourse.value) return;
  const sharePayload = {
    title: '올라 안전공유',
    text: safeLinkMessage.value,
    url: hasSelectedCourseLocation.value ? kakaoMapUrl.value : window.location.href,
  };
  if (navigator.share) {
    try {
      await navigator.share(sharePayload);
      shareStatus.value = '보호자 공유 창을 열었습니다.';
      return;
    } catch (err) {
      if (err?.name === 'AbortError') { shareStatus.value = '공유를 취소했습니다.'; return; }
    }
  }
  await copySafeLinkMessage();
  if (hasSelectedCourseLocation.value) window.open(kakaoMapUrl.value, '_blank', 'noreferrer');
}

// ─── 유틸 함수 ────────────────────────────────────────────────────────────
function isSelectedMountainCourse(course) {
  const target = normalizedSelectedMountain.value;
  if (!target) return false;
  return normalizeText(course.mountain).includes(target) || normalizeText(course.name).includes(target);
}

function normalizeText(value) { return String(value || '').replace(/\s/g, '').toLowerCase(); }

function parseTimelineHighlight(item) {
  const text = String(item || '').trim();
  if (!text) return null;
  const [label, ...rest] = text.split(':');
  if (rest.length) return { label: label.trim(), value: rest.join(':').trim() };
  return { label: '정보', value: text };
}

function addDays(date, days) { const d = new Date(date); d.setDate(d.getDate() + days); return d; }
function addMinutes(date, minutes) { const d = new Date(date); d.setMinutes(d.getMinutes() + minutes); return d; }
function formatDateForInput(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}
function formatTimeForInput(date) {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}
</script>
