import { createRouter, createWebHistory } from "vue-router"
import { isLoggedIn, getUserRole } from "../utils/auth"

const routes = [
  // ===== 公开页面 =====
  { path: "/", name: "home", component: () => import("../views/Home.vue") },
  { path: "/login", name: "login", component: () => import("../views/Login.vue"), meta: { guest: true, layout: false } },
  { path: "/register", name: "register", component: () => import("../views/Register.vue"), meta: { guest: true, layout: false } },
  { path: "/register/email", name: "register-email", component: () => import("../views/RegisterEmail.vue"), meta: { guest: true, layout: false } },
  { path: "/posts/:id", name: "post-detail", component: () => import("../views/PostDetail.vue") },
  { path: "/categories/:id", name: "category", component: () => import("../views/Category.vue") },
  { path: "/search", name: "search", component: () => import("../views/Search.vue") },
  { path: "/users/:id", name: "user-profile", component: () => import("../views/UserProfile.vue") },
  { path: "/users/:id/follow", name: "follow-list", component: () => import("../views/FollowList.vue") },
  { path: "/groups", name: "groups", component: () => import("../views/GroupList.vue") },

  // ===== 需登录 =====
  { path: "/posts/new", name: "create-post", component: () => import("../views/CreatePost.vue"), meta: { requiresAuth: true } },
  { path: "/posts/:id/edit", name: "edit-post", component: () => import("../views/CreatePost.vue"), meta: { requiresAuth: true } },
  { path: "/groups/new", name: "create-group", component: () => import("../views/CreateGroup.vue"), meta: { requiresAuth: true } },
  { path: "/groups/:id", name: "group-detail", component: () => import("../views/GroupDetail.vue"), meta: { requiresAuth: true } },
  { path: "/notifications", name: "notifications", component: () => import("../views/Notifications.vue"), meta: { requiresAuth: true } },
  { path: "/messages", name: "messages", component: () => import("../views/Messages.vue"), meta: { requiresAuth: true } },
  { path: "/messages/:userId", name: "messages-conversation", component: () => import("../views/Messages.vue"), meta: { requiresAuth: true } },
  { path: "/me/settings", name: "settings", component: () => import("../views/Settings.vue"), meta: { requiresAuth: true } },
  { path: "/me/settings/certification", name: "settings-certification", component: () => import("../views/SettingsCertification.vue"), meta: { requiresAuth: true } },
  { path: "/me/settings/professional-certification", name: "settings-professional-certification", component: () => import("../views/SettingsProfessionalCertification.vue"), meta: { requiresAuth: true } },
  { path: "/me/settings/assessment", name: "settings-assessment", component: () => import("../views/SettingsAssessment.vue"), meta: { requiresAuth: true } },
  { path: "/me/collections", name: "collections", component: () => import("../views/Collections.vue"), meta: { requiresAuth: true } },

  // ===== 管理后台 =====
  { path: "/admin", name: "admin-dashboard", component: () => import("../views/admin/Dashboard.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: "/admin/review", name: "admin-review", component: () => import("../views/admin/ReviewQueue.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: "/admin/users", name: "admin-users", component: () => import("../views/admin/UserManagement.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: "/admin/certifications", name: "admin-certifications", component: () => import("../views/admin/Certifications.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: "/admin/sensitive-words", name: "admin-sensitive-words", component: () => import("../views/admin/SensitiveWords.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: "/admin/logs", name: "admin-logs", component: () => import("../views/admin/ActivityLogs.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: "/admin/categories", name: "admin-categories", component: () => import("../views/admin/Categories.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: "/admin/hot-topics", name: "admin-hot-topics", component: () => import("../views/admin/HotTopics.vue"), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: "/admin/engagement", name: "admin-engagement", component: () => import("../views/admin/Engagement.vue"), meta: { requiresAuth: true, requiresAdmin: true } },

  // ===== 404 =====
  { path: "/:pathMatch(.*)*", name: "not-found", component: () => import("../views/NotFound.vue"), meta: { layout: false } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const authenticated = isLoggedIn()
  if (to.meta.requiresAuth && !authenticated) return next({ name: "login", query: { redirect: to.fullPath } })
  if (to.meta.guest && authenticated) return next({ name: "home" })
  if (to.meta.requiresAdmin) {
    const role = getUserRole()
    if (role !== "admin") return next({ name: "home" })
  }
  next()
})

export default router
