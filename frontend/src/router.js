import { createRouter, createWebHashHistory } from 'vue-router';

const routes = [
  { path: '/safe/:sessionId', component: () => import('./views/GuardianView.vue') },
  { path: '/guide', component: () => import('./views/GuideTab.vue') },
  { path: '/safe-link', component: () => import('./views/SafeLinkTab.vue') },
  { path: '/community', component: () => import('./views/CommunityTab.vue') },
  { path: '/login', component: () => import('./views/MyPageTab.vue') },
  { path: '/my-page', component: () => import('./views/MyPageTab.vue') },
  { path: '/mypage', redirect: '/my-page' },
  { path: '/chat', component: () => import('./views/ChatTab.vue') },
  { path: '/', redirect: '/guide' },
];

export default createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});
