import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, getUserRole } from '../utils/auth'

const routes = [
  // ===== 公开页面 =====
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/Register.vue'),
    meta: { guest: true },
  },
  {
    path: '/posts/:id',
    name: 'post-detail',
    component: () => import('../views/PostDetail.vue'),
  },
  {
    path: '/categories/:id',
    name: 'category',
    component: () => import('../views/Category.vue'),
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('../views/Search.vue'),
  },
  {
    path: '/users/:id',
    name: 'user-profile',
    component: () => import('../views/UserProfile.vue'),
  },
  {
    path: '/groups',
    name: 'groups',
    component: () => import('../views/GroupList.vue'),
  },

  // ===== 需登录 =====
  {
    path: '/posts/new',
    name: 'create-post',
    component: () => import('../views/CreatePost.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/posts/:id/edit',
    name: 'edit-post',
    component: () => import('../views/CreatePost.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/groups/:id',
    name: 'group-detail',
    component: () => import('../views/GroupDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/messages',
    name: 'messages',
    component: () => import('../views/Messages.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/messages/:userId',
    name: 'messages-conversation',
    component: () => import('../views/Messages.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/me/settings',
    name: 'settings',
    component: () => import('../views/Settings.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/me/collections',
    name: 'collections',
    component: () => import('../views/Collections.vue'),
    meta: { requiresAuth: true },
  },

  // ===== 管理后台 =====
  {
    path: '/admin',
    name: 'admin-dashboard',
    component: () => import('../views/admin/Dashboard.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/review',
    name: 'admin-review',
    component: () => import('../views/admin/ReviewQueue.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('../views/admin/UserManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },

  // ===== 404 =====
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authenticated = isLoggedIn()

  // 需登录页面
  if (to.meta.requiresAuth && !authenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  // 仅游客页面（如登录/注册），已登录则跳首页
  if (to.meta.guest && authenticated) {
    return next({ name: 'home' })
  }

  // 管理员页面
  if (to.meta.requiresAdmin) {
    const role = getUserRole()
    if (role !== 'admin') {
      return next({ name: 'home' })
    }
  }

  next()
})

export default router
