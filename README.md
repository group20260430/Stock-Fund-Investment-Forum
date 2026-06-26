# 股票基金投资论坛

**课程名称：** 软件工程理论与实践课程设计  
**项目周期：** 2026年4月30日 ~ 2026年6月20日  

---

## 项目简介

面向股票、基金投资者的社区论坛系统，支持用户认证、板块分类、发帖互动、关注私信、内容审核等功能。  
本课程设计遵循软件工程五大阶段流程（需求→设计→实现→测试→交付），全程采用 AI（ChatGPT / Claude / Copilot）辅助提效。

---

## 小组成员

| 角色 | 班级 | 学号 | 姓名 | GitHub 用户名 |
|------|------|------|------|--------------|
| 项目负责人 | 软件2402班 | U202415227 | 贺嘉轩 | [kkk431](https://github.com/kkk431) |
| 后端开发 | 软件2402班 | U202410032 | 陶畅 | [AsimaBivcaks](https://github.com/AsimaBivcaks) |
| 后端开发/测试 | 软件2402班 | U202410003 | 张照炎 | [sshadow-sky](https://github.com/sshadow-sky) |
| 前端开发/文档 | 软件2402班 | U202411334 | 刘嘉成 | [Teamanmade](https://github.com/Teamanmade) |
| 前端开发 | 软件2402班 | U202410002 | 张桐尘 | [yigongwugezi](https://github.com/yigongwugezi) |
| 后端开发/运维 | 软件2402班 | U202415026 | 杨文弢 | [Luvef](https://github.com/Luvef) |

---

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | Vue 3 + Vite | Vue 3.x / Vite 5.x |
| UI 样式 | Tailwind CSS | 最新 |
| 后端框架 | Python FastAPI | FastAPI 0.109+ |
| 数据库 | MySQL | 8.0+ |
| ORM | SQLAlchemy | 2.0+ |
| 认证方式 | JWT Token | PyJWT |
| API 规范 | OpenAPI 3.0 | Swagger UI 自动生成 |
| 版本控制 | Git + GitHub | — |

---

## 项目结构

```text
Stock-Fund-Investment-Forum/
|   .gitignore
|   check_categories.py
|   openapi.yaml
|   package-lock.json
|   package.json
|   project_code_full.docx
|   README.md
|   render.yaml
|
+---backend
|   |   .env.example
|   |   .env.production
|   |   fix_categories.py
|   |   migrate_categories.py
|   |   pytest.ini
|   |   README.md
|   |   requirements.txt
|   |   test_auth_output.txt
|   |
|   +---app
|   |   |   main.py
|   |   |   __init__.py
|   |   |
|   |   +---api
|   |   |       admin.py
|   |   |       auth.py
|   |   |       community.py
|   |   |       discovery.py
|   |   |       health.py
|   |   |       interactions.py
|   |   |       market.py
|   |   |       notifications.py
|   |   |       posts.py
|   |   |       social_users.py
|   |   |       uploads.py
|   |   |       __init__.py
|   |   |
|   |   +---config
|   |   |       questions.py
|   |   |       __init__.py
|   |   |
|   |   +---core
|   |   |       config.py
|   |   |       dependencies.py
|   |   |       security.py
|   |   |       __init__.py
|   |   |
|   |   +---db
|   |   |       base.py
|   |   |       session.py
|   |   |       __init__.py
|   |   |
|   |   +---models
|   |   |       certification.py
|   |   |       community.py
|   |   |       content.py
|   |   |       notification.py
|   |   |       oauth.py
|   |   |       operations.py
|   |   |       points.py
|   |   |       professional_certification.py
|   |   |       refresh_token.py
|   |   |       risk_assessment.py
|   |   |       social.py
|   |   |       user.py
|   |   |       __init__.py
|   |   |
|   |   +---schemas
|   |   |       community.py
|   |   |       content.py
|   |   |       interactions.py
|   |   |       operations.py
|   |   |       privacy.py
|   |   |       social.py
|   |   |       user.py
|   |   |       __init__.py
|   |   |
|   |   \---services
|   |           achievement_service.py
|   |           activity_service.py
|   |           compliance_service.py
|   |           duplicate_content_service.py
|   |           email_service.py
|   |           email_service.py.bak
|   |           mention_service.py
|   |           points_service.py
|   |           qq_oauth_service.py
|   |           quality_service.py
|   |           sensitive_word_service.py
|   |           user_service.py
|   |           wechat_oauth_service.py
|   |           weibo_oauth_service.py
|   |           __init__.py
|   |
|   \---tests
|       |   conftest.py
|       |   run_backend_tests.py
|       |   test_admin_api.py
|       |   test_admin_category_api.py
|       |   test_admin_mute_api.py
|       |   test_admin_warn_api.py
|       |   test_advanced_search_api.py
|       |   test_auth_api.py
|       |   test_community_api.py
|       |   test_content_api.py
|       |   test_discovery_api.py
|       |   test_duplicate_content_filter.py
|       |   test_e2e.py
|       |   test_email_auth_api.py
|       |   test_engagement_report.py
|       |   test_interactions_api.py
|       |   test_market_api.py
|       |   test_message_types_api.py
|       |   test_notifications_api.py
|       |   test_oauth_api.py
|       |   test_professional_certification_api.py
|       |   test_sensitive_filter.py
|       |   test_social_api.py
|       |   test_upload_api.py
|       |   __init__.py
|       |
|       \---unit
|               test_achievement_service.py
|               test_compliance_service.py
|               test_duplicate_content_service.py
|               test_market_service.py
|               test_mention_service.py
|               test_points_service.py
|               test_quality_service.py
|               test_refresh_token.py
|               test_sensitive_word_service.py
|               test_user_service_email_registration.py
|               test_user_service_login.py
|               test_user_service_profile_update.py
|               test_user_service_register.py
|               test_user_service_send_code.py
|               test_verification_code_store.py
|               __init__.py
|
+---database
|       README.md
|       schema.sql
|       seed.sql
|
+---deploy
|       cloudflared-config.yml
|       deploy.sh
|       stock-forum-api.service
|
+---docs
|   |   ai.md
|   |   architect.md
|   |   assign.md
|   |   backend_api.md
|   |   db.md
|   |   install.md
|   |   test.md
|   |   ui_design.md
|   |   user_guid.md
|   |   user_stories.md
|   |   use_cases.md
|   |   股票基金投资论坛-贺嘉轩-陶畅-张照炎-刘嘉成-张桐尘-杨文弢.docx
|   |   股票基金投资论坛-贺嘉轩-陶畅-张照炎-刘嘉成-张桐尘-杨文弢.md
|   |
|   \---images
|           mermaid_040c7ad4.png
|           mermaid_97c3b847.png
|
+---frontend
|   |   .env.example
|   |   index.html
|   |   package-lock.json
|   |   package.json
|   |   README.md
|   |   vite.config.js
|   |
|   \---src
|       |   App.vue
|       |   main.js
|       |   styles.css
|       |
|       +---api
|       |       admin.js
|       |       auth.js
|       |       comments.js
|       |       groups.js
|       |       market.js
|       |       messages.js
|       |       notifications.js
|       |       posts.js
|       |       search.js
|       |       social.js
|       |       users.js
|       |
|       +---components
|       |   |   PostCard.vue
|       |   |
|       |   +---comment
|       |   |       CommentItem.vue
|       |   |       CommentList.vue
|       |   |
|       |   +---common
|       |   |       AppIcon.vue
|       |   |       EmptyState.vue
|       |   |       ErrorState.vue
|       |   |       Loading.vue
|       |   |       MarketCard.vue
|       |   |       MentionTextarea.vue
|       |   |       MiniSparkline.vue
|       |   |       NavBar.vue
|       |   |       Pagination.vue
|       |   |       SideBar.vue
|       |   |       ToastContainer.vue
|       |   |
|       |   +---layout
|       |   |       AppLayout.vue
|       |   |
|       |   +---post
|       |   |       PollWidget.vue
|       |   |       PostCard.vue
|       |   |       PostDetail.vue
|       |   |       PostEditor.vue
|       |   |       RichTextEditor.vue
|       |   |
|       |   \---user
|       |           UserCard.vue
|       |           UserProfile.vue
|       |
|       +---router
|       |       index.js
|       |
|       +---stores
|       |       auth.js
|       |       posts.js
|       |       toast.js
|       |       user.js
|       |
|       +---styles
|       |       buttons.css
|       |       tokens.css
|       |       transitions.css
|       |
|       +---utils
|       |       auth.js
|       |       editor.js
|       |       format.js
|       |       icons.js
|       |       markdown.js
|       |       request.js
|       |
|       \---views
|           |   Category.vue
|           |   Collections.vue
|           |   CreateGroup.vue
|           |   CreatePost.vue
|           |   FollowList.vue
|           |   ForgotPassword.vue
|           |   ForumHome.vue
|           |   GroupDetail.vue
|           |   GroupList.vue
|           |   Home.vue
|           |   Login.vue
|           |   Messages.vue
|           |   NotFound.vue
|           |   Notifications.vue
|           |   OAuthCallback.vue
|           |   PostDetail.vue
|           |   Register.vue
|           |   RegisterEmail.vue
|           |   RegisterEmail.vue.bak
|           |   Search.vue
|           |   Settings.vue
|           |   SettingsAssessment.vue
|           |   SettingsCertification.vue
|           |   SettingsProfessionalCertification.vue
|           |   UserProfile.vue
|           |
|           \---admin
|                   ActivityLogs.vue
|                   BehaviorMonitor.vue
|                   Categories.vue
|                   Certifications.vue
|                   Compliance.vue
|                   Dashboard.vue
|                   DuplicateContent.vue
|                   Engagement.vue
|                   HotTopics.vue
|                   ReviewQueue.vue
|                   SensitiveWords.vue
|                   UserManagement.vue
|
+---images
|       mermaid_040c7ad4.png
|       mermaid_97c3b847.png
|
\---scripts
        cleanup_admin_nav.py
        run_project_checks.py

---

## 文档索引

| 文档 | 阶段 | 说明 |
|------|------|------|
| `user_stories.md` | 模块1 - 需求分析 | 16条用户故事 + 验收标准 |
| `use_cases.md` | 模块1 - 需求分析 | 14个完整交互场景 |
| `architect.md` | 模块2 - 系统设计 | 架构图、类设计、技术选型 |
| `db.md` | 模块2 - 系统设计 | 数据库ER图、表结构说明 |
| `backend_api.md` | 模块2 - 系统设计 | OpenAPI 3.0 接口规范 |
| `ui_design.md` | 模块2 - 系统设计 | 前端页面设计 |
| `frontend_core.md` | 模块3 - 实现 | 前端核心实现记录 |
| `frontend_pages.md` | 模块3 - 实现 | 前端页面开发日志 |
| `ai.md` | — | AI辅助使用记录 |
| `assign.md` | — | 成员工作完成情况 |

---

## 快速启动

### 1. 初始化数据库

```bash
cd database
mysql -u root -p < schema.sql
mysql -u root -p < seed.sql
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

后端默认地址：http://localhost:8000  
API 文档（Swagger UI）：http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：http://localhost:5173

---

## 项目验证 / 冒烟测试

### 后端一键测试

进入后端目录后执行：

```powershell
cd backend
python run_backend_tests.py
```

当前后端一键测试覆盖主要接口测试和端到端测试，最新验证结果：

```text
RESULTS: 10 passed, 0 failed
```

也可以在项目根目录执行：

```powershell
python backend\run_backend_tests.py
```

### 前端构建验证

进入前端目录后执行：

```powershell
cd frontend
npm run build
```

当前前端生产构建已通过。构建过程中可能存在 Vite 非阻塞 warning，例如 chunk size 或动态导入提示，不影响 build 通过。

### 验证报告

详细验证记录见：

* `docs/backend_testing_guide.md`
* `docs/backend_quality_delivery_zhangzhaoyan.md`
* `docs/project_smoke_test_zhangzhaoyan.md`

注意：

* 以上验证不能替代完整人工 UI 测试、生产环境部署验证或真实数据库压测。
* 新增后端测试脚本后，应同步考虑加入 `backend/run_backend_tests.py`。

---

## 已实现功能

### 用户系统
- [x] 注册 / 登录（密码登录 + 验证码登录）
- [x] JWT 双 Token 认证（Access Token + Refresh Token）
- [x] 个人资料编辑与隐私设置
- [x] 积分与等级系统
- [x] 星标用户

### 内容系统
- [x] 帖子发布（富文本 + 话题标签 + 股票关联）
- [x] 帖子分类浏览
- [x] 评论、点赞、收藏、转发
- [x] 投票组件

### 社交系统
- [x] 关注 / 取关
- [x] 私信（一对一 + 群聊）
- [x] 未读消息计数与轮询
- [x] 用户搜索与推荐

### 社区
- [x] 群组创建与管理
- [x] 分组导航（市场讨论 / 主题专区 / 公司研究 / 问答求助）
- [x] 搜索（帖子 / 用户 / 股票 / 群组）

### 后台管理
- [x] 用户管理
- [x] 敏感词过滤
- [x] 内容审核
- [x] 操作日志

---

## 下一步建议

- 接入真实第三方登录（微信 / GitHub）
- 增加 WebSocket 实时消息推送
- 完善移动端适配
- 生产环境部署（Docker + Nginx）
- 性能优化与缓存策略

### 全项目一键验证

在项目根目录执行：

```powershell
python scripts\run_project_checks.py
```

该脚本会顺序运行后端一键测试和前端生产构建，并输出统一汇总结果。
