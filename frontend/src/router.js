import { createRouter, createWebHashHistory } from 'vue-router';

const routes = [
  { path: '/safe/:sessionId', component: () => import('./views/GuardianView.vue') },
  { path: '/guardian', component: () => import('./views/GuardianCodeView.vue') },
  { path: '/guide', component: () => import('./views/GuideTab.vue') },
  { path: '/safe-link', component: () => import('./views/SafeLinkTab.vue') },
  { path: '/community', component: () => import('./views/CommunityTab.vue') },
  { path: '/my-page', component: () => import('./views/MyPageTab.vue') },
  { path: '/', redirect: '/guide' },
];

export default createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
});
