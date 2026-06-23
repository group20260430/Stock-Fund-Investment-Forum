# 前端页面开发日志 (Frontend Pages Development Log)

**分支：** `feat/frontend/pages`  
**基于：** `feat/frontend/core`  
**开发者：** 杨文弢（前端开发与文档）  
**开始日期：** 2026年6月21日  
**最后更新：** 2026年6月23日 (最新)  

---

## 一、概述

基于 `feat/frontend/core` 提供的前端基础设施（Vue 3 + Vite + Pinia + 路由 + API 层 + 通用组件），完成了以下六个模块的前端页面开发与功能实现。

---

## 二、已完成工作

### 2.1 帖子详情页与评论组件（楼中楼、@提及）

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/components/common/MentionTextarea.vue` | **新建** | @提及自动补全组件，输入 `@` 触发用户搜索下拉，支持键盘导航（↑↓选择/Enter确认/Escape关闭），250ms 防抖，调用 `searchSuggestions(keyword, "user")` |
| `src/components/comment/CommentItem.vue` | 修改 | 新增删除按钮（仅作者可见），回复框替换为 MentionTextarea，集成 Toast 反馈 |
| `src/components/comment/CommentList.vue` | 修改 | 转发 `delete` 事件到父组件 |
| `src/views/PostDetail.vue` | 修改 | 主评论框替换为 MentionTextarea，新增评论删除处理（动画移除+计数同步），新增举报弹窗（选原因+补充说明），Toast 反馈 |

### 2.2 投票功能

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/components/post/PollWidget.vue` | **新建** | 投票组件：单选/多选模式，进度条动画（`ease-out-expo`），乐观更新，截止时间倒计时，已结束标签，调用 `voteOnPost(id, optionIds)` |
| `src/components/post/PostDetail.vue` | 修改 | 集成 PollWidget（`post_type === 'poll'` 时渲染），新增「投票」角标 |

### 2.3 搜索页面与筛选组件

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/views/Search.vue` | 重写 | 修复联想词点击联动搜索（L1），新增搜索历史（localStorage 持久化），筛选器升级为 pill 胶囊按钮 + 自定义下拉，新增精华/市场筛选，清除按钮 |

### 2.4 社交功能页面

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/views/FollowList.vue` | **新建** | 关注/粉丝统一页面，标签切换，UserCard 网格展示，分页，路由 `/users/:id/follow` |
| `src/views/GroupDetail.vue` | 重写 | 群内发帖功能（M2），群组成员审核界面（管理员可见待审核成员，一键通过），调用 `createGroupPost`，帖子列表分页，群组类型标签，加入按钮 |
| `src/views/UserProfile.vue` | 修改 | 新增星标用户功能（`setStarred` API），星标按钮 + 已星标状态 + Toast 反馈 |
| `src/components/user/UserProfile.vue` | 修改 | 新增星标 emit 和按钮，昵称旁 ⭐ 标识，统计数据链接修正 |
| `src/router/index.js` | 修改 | 新增 `/users/:id/follow` 路由 |

### 2.5 管理后台页面

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/views/admin/Dashboard.vue` | 重写 | 集成 ECharts（M6）：活跃趋势折线图、热门话题/活跃股票横向柱状图，vue-echarts 按需引入，品牌色配色 |
| `src/views/admin/ReviewQueue.vue` | 修改 | Toast 反馈，拒绝校验（必填审核意见），举报标签彩色 pill，审核中 loading 态 |

### 2.6 项目文档

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/user_guid.md` | **新建** | 用户使用指南：系统概述、快速开始、六大功能模块说明、路由一览、常见问题 |
| `frontend_pages.md` | **新建** | 本文档，开发日志 |

### 2.7 2026-06-22 补充完善

根据前后端功能完成状态总表，补充前端缺失项：

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/views/GroupDetail.vue` | 修改 | 新增成员审核界面：管理员在群组详情页可见「⏳ 待审核成员」区域，展开后列表展示待审核成员，一键「✓ 通过」，调用 `approveGroupMember` API（P1） |
| `src/views/UserProfile.vue` | 修改 | 新增星标用户功能：调用 `setStarred` API，按钮切换「☆ 星标」/「⭐ 已星标」，Toast 反馈 |
| `src/components/user/UserProfile.vue` | 修改 | 新增星标 emit + ⭐ 标识 + 按钮 UI，统计数据链接修复 |
| `src/views/PostDetail.vue` | 修改 | 新增举报弹窗：操作栏「⚠ 举报」按钮 → 选择举报原因（虚假信息/人身攻击/违规荐股/垃圾广告/其他）+ 补充说明 → 调用 `submitReport` API |

### 2.8 2026-06-23 市场分组导航

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/components/common/SideBar.vue` | 修改 | 新增「市场」导航区域：4 个可展开市场分组（🇨🇳 A股 / 🇭🇰 港股 / 🇺🇸 美股 / 💰 基金），每项含「讨论」和「热门」子链接，点击跳转搜索页并自动预填市场筛选条件 |

---

## 三、文件统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 新建组件 | 3 | MentionTextarea / PollWidget / FollowList |
| 修改组件 | 4 | CommentItem / CommentList / UserProfile / SideBar |
| 重写页面 | 4 | Search / GroupDetail / Dashboard / ReviewQueue |
| 修改页面 | 2 | PostDetail / UserProfile |
| 修改配置 | 1 | router/index.js |
| 新建文档 | 2 | user_guid.md / frontend_pages.md |
| **合计** | **16** | |

---

## 四、构建结果

```
npm run build
✓ 688 modules transformed
✓ built in ~6.8s
```

---

## 五、技术要点

### 设计规范遵循

- 全站统一使用 `tokens.css` 中的 CSS 自定义属性
- 组件命名 PascalCase，函数 camelCase，CSS 类 kebab-case
- 所有交互使用 Toast 反馈（success/error/warning）
- API 调用统一通过 `request.js` 封装

### 新增功能依赖的 API

| 功能 | API 接口 | 前端状态 | 后端状态 |
|------|---------|---------|---------|
| @提及 | `GET /search/suggestions?type=user` | ✅ 已对接 | 待实现 |
| 投票 | `POST /posts/:id/vote` | ✅ 已对接 | 待实现 |
| 评论删除 | `DELETE /comments/:id` | ✅ 已对接 | 待实现 |
| 群内发帖 | `POST /groups/:id/posts` | ✅ 已对接 | 待实现 |
| 成员审核 | `POST /groups/:id/members/:userId/approve` | ✅ 已对接 | 待实现 |
| 关注/粉丝 | `GET /users/:id/following`, `followers` | ✅ 已对接 | 待实现 |
| 星标用户 | `PUT /users/me/starred` | ✅ 已对接 | API 就绪 |
| 举报帖子 | `POST /report` | ✅ 已对接 | 待实现 |
| 审核操作 | `POST /admin/review-queue/:id/review` | ✅ 已对接 | 待实现 |
| 数据统计 | `GET /admin/stats/overview` | ✅ 已对接 | 待实现 |
| 市场搜索 | `GET /search?market=` | ✅ 已对接 | 待实现 |

---

## 六、与 core 分支的关系

```
feat/frontend/core  ← 张桐尘（基础设施、布局、API层、通用组件）
        │
        └── feat/frontend/pages  ← 杨文弢（本分支，页面功能开发）
```

本分支完全基于 core 分支，未修改 core 的基础代码，仅在其基础上新增和扩展页面功能。最终由组长贺嘉轩合并到 `develop` 分支。

---

*本文档随开发进度持续更新。*



### 2.9 2026-06-23 修复

| 文件 | 操作 | 说明 |
|------|------|------|
| src/components/common/SideBar.vue | 修改 | 分组导航默认全部收起（不再自动展开）；修复底部用户认证标识中文编码（专业认证/实名认证/普通用户） |

---
