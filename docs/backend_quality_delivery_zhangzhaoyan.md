# 张照炎后端质量保障交付总结

## 1. 负责方向

张照炎本阶段主要负责后端质量保障、测试稳定性和内容安全相关收尾能力建设，重点围绕测试可运行性、冒烟验证、敏感词过滤以及 Windows 环境下测试清理稳定性展开，不与内容系统、隐私设置、积分等级、@提及等其他同学负责的功能冲突。

## 2. 已完成工作

### 2.1 自动敏感词过滤

已在后端发布链路中接入自动敏感词检查，复用后台敏感词库能力：

* 发帖时检查 `title` 和 `content`
* 评论时检查 `content`
* `block` 命中后返回 HTTP 400
* `review` 命中后进入 `REVIEWING`
* `warn` 命中后正常放行
* 已有对应测试覆盖

关联提交：

* `a9ad445 feat: add automatic sensitive word filtering`

### 2.2 敏感词任务记录文档

已补充敏感词过滤任务的实现记录，便于后续查阅、交接和维护。

关联提交：

* `af334c6 docs: add backend task record for sensitive word filtering`

### 2.3 上传依赖修复

已补充 `python-multipart` 依赖，解决 `uploads` 路由引入后导致后端测试导入阻塞的问题。

关联提交：

* `0a3fc48 fix: add multipart dependency for uploads`

### 2.4 后端冒烟测试报告

已补充后端冒烟测试报告，统一汇总主要测试脚本的覆盖范围、测试结果和已知问题，方便项目汇报与验收。

关联提交：

* `907293a docs: add backend smoke test report`

### 2.5 Windows SQLite 测试清理稳定性修复

已修复多个测试脚本在 Windows 下删除 SQLite 临时库时出现 `PermissionError` 的问题，处理方式包括：

* 清理前释放数据库连接
* 增加删除重试
* 清理失败时降级为 warning
* 不掩盖测试主体失败

关联提交：

* `f3bc477 test: stabilize remaining sqlite cleanup on Windows`

### 2.6 后端一键测试入口

已新增 `backend/run_backend_tests.py`，支持在 `backend` 目录或项目根目录运行，顺序执行 9 个主要后端测试脚本并输出统一汇总结果。

当前验证结果：

* `RESULTS: 9 passed, 0 failed`

关联提交：

* `a57b205 test: add backend smoke test runner`

### 2.7 全项目冒烟验证

已新增并更新 `docs/project_smoke_test_zhangzhaoyan.md`，完成后端一键测试和前端生产构建验证，形成全项目基础冒烟闭环。

当前结果：

* `RESULTS: 9 passed, 0 failed`
* `npm run build` 通过

关联提交：

* `cfd191d docs: add project smoke test report`
* `00eaf81 docs: update project smoke test report`

### 2.8 前端构建缺失依赖修复

已修复 Markdown 渲染链路缺失依赖导致的 Vite build 失败，补齐 `marked` / `dompurify` 后，前端生产构建恢复通过。

关联提交：

* `d865c1b fix: add missing marked dependency`

### 2.9 README 验证入口说明

已在 README 中增加“项目验证 / 冒烟测试”小节，补充后端一键测试、前端构建命令和验证报告位置，方便组员和老师快速复现验证结果。

关联提交：

* `7660b1e docs: add project validation instructions`

### 2.10 前端构建 warning 清理

已清理 `auth.js` / `comments.js` 的动态导入与静态导入混用 warning，不处理 Dashboard chunk size，保证 build 通过且仅保留非阻塞提示。

关联提交：

* `efae993 fix: clean mixed dynamic imports in frontend build`

### 2.11 重复内容检测后端最小闭环

已完成发帖重复内容检测的后端最小闭环，采用同一用户维度检测，减少误杀：

* 完全重复内容返回 HTTP 400
* 高度相似内容进入 `REVIEWING`
* 同一用户维度检测
* 测试结果为 `RESULTS: 17 passed, 0 failed`

关联提交：

* `354516b feat: add duplicate post detection`

## 3. 当前验证结果

```text
RESULTS: 9 passed, 0 failed
```

前端：`npm run build` 通过

剩余问题：`Dashboard` chunk size 超 500KB 的 Vite 非阻塞 warning

覆盖测试：

* `test_sensitive_filter.py`
* `test_content_api.py`
* `test_interactions_api.py`
* `test_admin_api.py`
* `test_discovery_api.py`
* `test_community_api.py`
* `test_social_api.py`
* `test_e2e.py`

## 4. 价值说明

* 提高后端测试的可运行性和稳定性
* 降低多人协作下的回归风险
* 为内容安全基础能力提供可验证闭环
* 为后续联调提供统一的一键验证入口
* 方便项目汇报、分工说明和答辩展示
* 从后端质量保障扩展到全项目基础冒烟验证
* 提供 README 级别的验证入口，方便团队复现
* 修复前端构建阻塞依赖并清理部分构建 warning
* 当前项目具备“后端回归 + 前端构建”的基础验收闭环

## 5. 边界说明

* 本阶段没有改动隐私设置、积分等级、@提及等其他同学负责的功能
* 一键测试入口不能替代完整系统测试、前端联调测试和生产数据库测试
* 后续如果继续扩展新接口，应同步补充到 `run_backend_tests.py` 和冒烟测试报告中
