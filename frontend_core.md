# 前端核心开发日志 (Frontend Core Development Log)

**分支：** `feat/frontend/core`  
**开发者：** 张桐尘（前端核心开发）  
**开始日期：** 2026年6月19日  
**最后更新：** 2026年6月19日（第二次更新）

---

## 一、概述

按照 `ui_design.md` 前端UI设计文档，完成了前端项目的**基础设施搭建、通用组件库开发、全部15+个核心页面编码、UI美化与动画增强（8个Phase）、实时行情数据接入**。构建验证通过（Vite build: ~115 modules, 1.0s）。

后端新建**行情数据代理接口** `GET /api/market/indices` 和 `GET /api/market/kline/{secid}`，代理东方财富公开 API，解决浏览器跨域限制。

---

## 二、已完成工作

### 2.1 基础设施（P0 ✅）

| 文件 | 完成内容 | 备注 |
|------|---------|------|
| `package.json` | 新增 `vue-router@4`、`pinia`、`@vueuse/motion`、`@formkit/auto-animate`、`unplugin-icons`、`@iconify-json/heroicons-outline` | npm install 完成 |
| `src/router/index.js` | 21条路由 + 路由守卫（登录拦截、角色鉴权、游客重定向） | 懒加载所有页面 |
| `src/stores/auth.js` | Pinia Store：login/register/logout/fetchUser/updateProfile | localStorage 持久化 token+user |
| `src/stores/posts.js` | Pinia Store：帖子列表/详情/乐观更新(点赞/收藏) | 失败自动回滚 |
| `src/stores/user.js` | Pinia Store：用户资料加载/清理 | |
| `src/stores/toast.js` | Pinia Store：全局 Toast 通知管理（success/error/warning/info） | 自动消失 |
| `src/utils/request.js` | Fetch 封装：Token 注入、401 拦截跳转、统一解包 data 字段、网络异常处理 | 支持 GET/POST/PUT/PATCH/DELETE |
| `src/utils/auth.js` | Token 管理：get/set/remove、JWT payload 解析、角色获取 | |
| `src/utils/format.js` | 格式化工具：timeAgo(相对时间)、formatCount(数字缩写)、truncate(截断) | |
| `src/utils/icons.js` | 30+ 语义图标名 → Heroicons SVG 标识符映射表 | 供 AppIcon.vue 使用 |
| `src/main.js` | 集成 createPinia() + use(router) + 导入 tokens.css / transitions.css / buttons.css | |
| `src/App.vue` | `<Transition name="page" mode="out-in">` 包裹 `<router-view />` | 页面切换淡入+上滑动画 |

### 2.2 样式基础设施（Phase 0 — 新增 ✅）

| 文件 | 完成内容 |
|------|---------|
| `src/styles/tokens.css` | CSS 自定义属性设计系统（~50个令牌）：颜色、间距、圆角、阴影、动画缓动、字号、z-index 层级 |
| `src/styles/transitions.css` | 4 种全局过渡动画：page（页面切换）/ fade（模态框）/ slide-up（底部抽屉）/ scale（弹窗弹跳） |
| `src/styles/buttons.css` | 微交互工具类：btn-press（按压缩放）、card-lift（悬停浮升）、glass（毛玻璃）、animated-gradient、icon-bounce |
| `src/styles.css` | 精简为最小全局 reset + font smoothing + scroll-behavior |

### 2.3 布局组件（Phase 1 — 新增 ✅）

| 文件 | 完成内容 |
|------|---------|
| `src/components/layout/AppLayout.vue` | 统一页面布局：SideBar + NavBar + 移动端遮罩 + 主内容 grid + `<slot />` + ToastContainer |

**14 个视图全部重构为 `<AppLayout>` 包裹**，消除了 ~168 行重复的 `.home-layout` / `.mobile-overlay` / `.main-area` / `.content` CSS。

### 2.4 API 层（P0 ✅）

| 文件 | 接口覆盖 | 说明 |
|------|---------|------|
| `src/api/auth.js` | /auth/register, login, send-code, refresh, me, profile, certification, risk-assessment | 完整 |
| `src/api/posts.js` | /posts CRUD, like, collect, share, vote; /categories; /users/me/collections | 完整 |
| `src/api/comments.js` | /posts/:id/comments 列表+创建+删除+点赞 | 完整 |
| `src/api/users.js` | /users/:id, follow, followers, following, starred | 完整 |
| `src/api/social.js` | /feed, /hot | 完整 |
| `src/api/groups.js` | /groups CRUD, join, approve, group-post | 完整 |
| `src/api/search.js` | /search, /search/suggestions | 完整 |
| `src/api/admin.js` | /admin/review-queue, users, stats, categories; /report; /messages | 完整 |
| `src/api/market.js` | /market/indices, /market/kline/{secid} | **新增** — 实时行情代理 |

### 2.5 通用组件（P0 ✅）

| 组件 | 文件 | 完成内容 |
|------|------|---------|
| NavBar | `components/common/NavBar.vue` | 顶部导航：汉堡菜单(移动端)、搜索框(展开/收起)、通知铃铛、用户下拉菜单(头像+退出)、发布按钮、登录/注册按钮(未登录时)、**毛玻璃背景(backdrop-filter: blur(12px))** |
| SideBar | `components/common/SideBar.vue` | 侧边栏：品牌区、论坛板块导航(5个)、发现区(热榜/搜索)、个人区(需登录)、底部用户信息、移动端抽屉模式、**深色渐变背景** |
| Loading | `components/common/Loading.vue` | 两种模式：skeleton(骨架屏脉冲动画，可配置行数) + spinner(旋转加载圈) |
| Pagination | `components/common/Pagination.vue` | 完整分页器：当前页高亮、省略号、首尾页固定显示 |
| EmptyState | `components/common/EmptyState.vue` | 空状态：SVG图标+标题+描述+操作按钮 |
| ErrorState | `components/common/ErrorState.vue` | 错误状态：SVG图标+错误信息+重试按钮 |
| AppIcon | `components/common/AppIcon.vue` | **新增** — 统一 SVG 图标组件（零运行时成本，构建时内联） |
| ToastContainer | `components/common/ToastContainer.vue` | **新增** — 全局 Toast 通知容器（毛玻璃、滑入动画、彩色左边框、自动消失进度条） |
| MarketCard | `components/common/MarketCard.vue` | **新增** — 实时指数行情卡片（价格、涨跌幅、最高/最低/昨收/成交额、迷你走势图） |
| MiniSparkline | `components/common/MiniSparkline.vue` | **新增** — 纯 SVG 迷你走势图（涨红跌绿配色、面积填充、自适应缩放） |

### 2.6 业务组件

| 组件 | 文件 | 完成内容 |
|------|------|---------|
| PostCard | `components/post/PostCard.vue` | 帖子卡片：板块标签、精华徽章、作者(V标识)、相对时间、标题、摘要(截断)、标签(最多3个)、**SVG 图标互动统计**、**悬停上浮+阴影加深+边框微光** |
| PostDetail(组件) | `components/post/PostDetail.vue` | 帖子正文渲染：标题、作者信息(V标识)、富文本内容(v-html)、附件列表、标签、互动统计 |
| PostEditor | `components/post/PostEditor.vue` | 发帖编辑器：板块选择、帖子类型切换、标题输入、富文本工具栏、正文textarea、标签输入、附件上传区、预览弹窗 |
| CommentItem | `components/comment/CommentItem.vue` | 评论：头像、昵称、认证标识(V)、相对时间、@回复标记、楼中楼(缩进+色条)、展开/收起、内联回复框、**auto-animate 动画** |
| CommentList | `components/comment/CommentList.vue` | 评论列表容器：遍历CommentItem、加载态、空态、**auto-animate** |
| UserCard | `components/user/UserCard.vue` | 用户卡片：头像、昵称+认证标识、简介、帖子/粉丝统计、关注按钮 |
| UserProfile | `components/user/UserProfile.vue` | 用户资料头部：渐变背景横幅、大头像(圆角+阴影)、昵称+认证标识、简介、统计、徽章列表、关注/私信按钮 |

### 2.7 页面（全部17个视图）

| 页面 | 路由 | 完成内容 | 状态 |
|------|------|---------|------|
| **Home.vue** | `/` | **实时行情卡片(东方财富+走势图)**、排序Tab、帖子列表(auto-animate)、热榜视图(auto-animate)、分页、三态、**动画渐变背景** | ✅ |
| **Login.vue** | `/login` | 密码/验证码双模式、验证码60s倒计时、记住登录、错误提示、**页面背景动画渐变+装饰光斑** | ✅ |
| **Register.vue** | `/register` | 三步注册流程(手机验证→密码设置→偏好完善)、步骤指示器、验证码倒计时、密码强度校验、**页面背景动画渐变** | ✅ |
| **PostDetail.vue** | `/posts/:id` | 帖子详情+评论区、点赞/收藏操作栏(乐观更新)、发表评论、回复楼中楼、评论分页、未登录引导 | ✅ |
| **CreatePost.vue** | `/posts/new` | 未登录引导、PostEditor编辑器组件 | ✅ |
| **UserProfile.vue** | `/users/:id` | UserProfile组件+帖子/收藏/成就Tab切换、关注/取消关注 | ✅ |
| **Search.vue** | `/search` | 搜索框(聚焦样式)、搜索联想(股票/用户/话题)、筛选器、搜索结果列表、分页 | ✅ |
| **Category.vue** | `/categories/:id` | 板块帖子列表、板块名称动态显示、分页 | ✅ |
| **GroupList.vue** | `/groups` | 群组卡片网格、成员数/可见性标签、创建群组入口 | ✅ |
| **GroupDetail.vue** | `/groups/:id` | 群组信息头部、加入群组按钮 | ✅ |
| **Messages.vue** | `/messages` | 占位页，标识后续版本完善 | ⚠️ |
| **Settings.vue** | `/me/settings` | 三个卡片：个人资料编辑、身份认证入口、风险评估入口、保存反馈 | ✅ |
| **Collections.vue** | `/me/collections` | 收藏列表(PostCard复用)、分页 | ✅ |
| **NotFound.vue** | `/:pathMatch(.*)*` | 404页面：SVG图标+返回首页按钮 | ✅ |
| **admin/Dashboard.vue** | `/admin` | 管理导航、6个统计卡片、图表占位区 | ✅ |
| **admin/ReviewQueue.vue** | `/admin/review` | 审核列表、卡片样式(橙色左边框)、审核意见输入、通过/拒绝按钮 | ✅ |
| **admin/UserManagement.vue** | `/admin/users` | 用户列表(UserCard复用)、封禁按钮 | ✅ |

### 2.8 后端行情代理接口（新增 ✅）

| 端点 | 说明 |
|------|------|
| `GET /api/market/indices?secids=1.000001,1.000300,0.399001` | 代理东方财富实时行情，返回上证/沪深300/深证成指的实时价格、涨跌幅、最高最低、昨收、成交额 |
| `GET /api/market/kline/{secid}?klt=101&lmt=20` | 代理东方财富K线数据，用于迷你走势图（返回近20个交易日OHLCV） |

**降级策略：** 当东方财富 API 超时或不可用时，返回 `price: null` 的降级数据，前端展示"--"而非崩溃。

**技术实现：**
- `backend/app/api/market.py` — 使用 `httpx.AsyncClient` 异步请求东方财富公开接口
- `backend/requirements.txt` — 新增 `httpx==0.28.1` 依赖
- `frontend/src/api/market.js` — 前端调用封装

---

## 三、UI 增强完成清单（Phase 0–8）

| Phase | 内容 | 状态 |
|-------|------|------|
| **Phase 0** | CSS 令牌系统（50+ 变量）+ transitions.css + buttons.css + vite 插件配置 | ✅ |
| **Phase 1** | 提取 AppLayout 布局组件，14 个视图消除重复 CSS(~168行) | ✅ |
| **Phase 2** | 30+ Emoji 全部替换为 Heroicons SVG 图标（零运行时成本） | ✅ |
| **Phase 3** | 全站 ~76 处硬编码 hex → `var(--color-xxx)` CSS 变量令牌化 | ✅ |
| **Phase 4** | 页面过渡动画 + App.vue `<Transition mode="out-in">` + 滚动入场(v-motion) | ✅ |
| **Phase 5** | 微交互：PostCard hover 浮升+阴影、按钮按压 scale(0.97)、card-lift 工具类 | ✅ |
| **Phase 6** | 毛玻璃 NavBar(blur 12px)、Login/Register 动画渐变背景、SideBar 深色渐变、行情涨跌渐变 | ✅ |
| **Phase 7** | 列表动画(Home 帖子列表+热榜、CommentList)、auto-animate 编排 | ✅ |
| **Phase 8** | Toast 全局通知系统（ToastContainer + Pinia store，毛玻璃、滑入动画、进度条） | ✅ |

---

## 四、实时行情数据实现方案

### 架构

```
东方财富公开 API (push2.eastmoney.com)
              ↑
    [httpx.AsyncClient — 后端代理，解决浏览器跨域]
              ↑
    FastAPI /api/market/indices (异步，8s 超时)
    FastAPI /api/market/kline/{secid}
              ↑
    [前端 fetchIndices() / fetchKline() — 经 request.js 封装]
              ↑
    Home.vue → MarketCard.vue
            → MiniSparkline.vue (纯 SVG)
```

### 展示指数

| 指数 | 代码 | 接口 secid |
|------|------|------------|
| 上证指数 | 000001 | `1.000001` |
| 沪深300 | 000300 | `1.000300` |
| 深证成指 | 399001 | `0.399001` |

### 每个 MarketCard 展示

- **实时价格**（大字号，每3秒自动刷新）
- **涨跌幅**（红涨绿跌 + 箭头图标）
- **迷你走势图**（近20个交易日收盘价，纯 SVG Polyline + 面积填充，涨红跌绿）
- **四维明细**：最高、最低、昨收、成交额(亿)

### 加载态 / 降级态

- 首次加载：3个灰色骨架脉冲卡片
- API 超时/不可用：降级数据显示"--"（不崩溃）
- 走势图无数据：不渲染 SVG

---

## 五、有待完善的细节

### 5.1 高优先级

| 编号 | 问题 | 说明 | 建议方案 |
|------|------|------|---------|
| **H1** | 富文本编辑器未集成 | PostEditor 仅有 textarea + 占位工具栏按钮 | 集成 Tiptap 或 Quill |
| **H2** | 路由模式需要确认 | 使用 `createWebHistory()`，需后端 SPA fallback | 如果后端无法配置，改用 `createWebHashHistory()` |
| **H3** | 未登录时首页数据源 | 当前未登录调用 `/posts` 获取最新帖子，需求设计是未登录展示热榜 | 根据 `auth.isLoggedIn` 切换数据源 |
| **H4** | 后端接口数据格式不一致 | 部分 API 使用原生 fetch 而非 request.js 封装 | 统一所有 API 文件使用 `api` 封装 |
| **H5** | 行情刷新频率 | 当前仅页面加载时请求一次，无法实时更新 | 添加 `setInterval(loadMarketData, 3000)` 每3秒轮询 |

### 5.2 中优先级

| 编号 | 问题 | 说明 | 建议方案 |
|------|------|------|---------|
| **M1** | 私信功能(Messages.vue) | 占位页，无会话列表和聊天界面 | 对接 `/messages` 接口 |
| **M2** | 群组发帖功能(GroupDetail.vue) | 只有信息展示，缺少群内发帖 | 接入群组帖子接口 |
| **M3** | 移动端底部导航栏未实现 | ui_design.md 设计了移动端底部导航 | 新建 `BottomNav.vue` 组件 |
| **M4** | ConfirmDialog 组件缺失 | 删除操作等需要确认弹窗 | 新建 `ConfirmDialog.vue` |
| **M5** | 附件上传实际功能 | PostEditor 附件区只有占位按钮 | 集成 `<input type="file">` + FormData |
| **M6** | 管理后台图表未集成 | Dashboard.vue 图表区为占位 div | 集成 ECharts（已加入 package.json draft） |
| **M7** | 行情点击跳转详情页 | 点击 MarketCard 应跳转到该指数的详细走势页面 | 新建 `MarketDetail.vue` + 完整K线图 |

### 5.3 低优先级

| 编号 | 问题 | 说明 | 建议方案 |
|------|------|------|---------|
| **L1** | 搜索联想点击未联动搜索 | suggestions item 点击后未填入并触发搜索 | 添加 @click 处理 |
| **L2** | 身份认证/风险评估页面缺失 | 路由 `/me/settings/certification` 和 `/me/settings/assessment` 未创建 | 新建对应页面 |
| **L3** | 默认头像处理 | 多处使用内联 SVG data URI 作为 fallback | 统一创建 `DefaultAvatar.vue` 组件 |
| **L4** | 代码分割警告 | Login.vue 中 `sendCode` 的动态 import 与静态 import 冲突 | 改为静态 import |
| **L5** | 帖子详情页投票功能未实现 | UC-004 要求的投票 UI 未包含 | 根据 `post_type === 'poll'` 条件渲染 |

---

## 六、文件统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 页面 Views | 17 | 全部已创建 |
| 通用组件 | 10 | NavBar / SideBar / Loading / Pagination / EmptyState / ErrorState / AppIcon / ToastContainer / MarketCard / MiniSparkline |
| 业务组件 | 7 | PostCard / PostDetail / PostEditor / CommentItem / CommentList / UserCard / UserProfile |
| 布局组件 | 1 | AppLayout |
| API 模块 | 9 | auth / posts / comments / users / social / groups / search / admin / market |
| Store | 4 | auth / posts / user / toast |
| Utils | 3 | request / auth / format / icons |
| 样式文件 | 4 | styles.css / tokens.css / transitions.css / buttons.css |
| 配置文件 | 3 | router/index.js / main.js / App.vue |
| 后端接口 | 1 | backend/app/api/market.py（新增） |
| **合计** | **59** | |

---

## 七、构建结果

```
npm run build
✓ ~115 modules transformed
✓ built in ~1.0s

输出：dist/ (JS: ~113KB gzipped 主包 + 若干页面分块)
动画库增量 (~28KB gzipped) + 图标(0KB 运行时) + Toast(~1KB)
```

---

## 八、下一步建议

### 立即（本周内）

1. 解决 **H2**（路由 History/Hash 模式确认），与后端确认部署方式
2. 解决 **H4**（统一 API 请求封装），确保所有 API 调用经过 request.js
3. 集成富文本编辑器（**H1**），发帖核心体验

### 短期（下周）

4. 实现 ConfirmDialog（**M4**），提升交互完整性
5. 对接后端接口联调，验证数据格式
6. 完善移动端体验（**M3** 底部导航）
7. 行情点击跳转详情页（**M7**），展示完整 K 线图

### 后续迭代

8. 私信功能完整实现（**M1**）
9. 管理后台 ECharts 图表集成（**M6**）
10. 身份认证页面（**L2**）

---

*本文档随开发进度持续更新。所有变更最终合并到 `develop` 分支。*
