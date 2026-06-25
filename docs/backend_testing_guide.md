# 后端测试使用指南

## 1. 测试入口

后端已有一键测试入口，可以在 `backend` 目录下执行：

```powershell
cd backend
python run_backend_tests.py
```

也可以在项目根目录执行：

```powershell
python backend\run_backend_tests.py
```

## 2. 当前覆盖的测试脚本

* `test_sensitive_filter.py`：敏感词过滤
* `test_duplicate_content_filter.py`：重复内容检测
* `test_engagement_report.py`：用户参与度报告
* `test_content_api.py`：内容接口
* `test_interactions_api.py`：互动接口
* `test_admin_api.py`：管理后台
* `test_discovery_api.py`：搜索/发现/热榜
* `test_community_api.py`：群组/私信
* `test_social_api.py`：关注/用户社交
* `test_e2e.py`：端到端流程测试

## 3. 预期输出

当前正常结果为：

```text
RESULTS: 10 passed, 0 failed
```

## 4. Windows 测试注意事项

* 部分测试会生成临时 SQLite 数据库
* 已通过安全清理逻辑释放连接并删除临时库
* `.gitignore` 已忽略 `backend/test_*.db`
* 如果测试被中断后残留 `backend/test_*.db`，可以手动删除

PowerShell 清理命令：

```powershell
Remove-Item -Force backend\test_*.db -ErrorAction SilentlyContinue
```

## 5. 新增测试时的维护要求

* 新增后端测试脚本后，应考虑加入 `backend/run_backend_tests.py`
* 如果测试会生成临时文件，应同步更新 `.gitignore`
* 测试主体失败不能被清理逻辑掩盖
* 清理失败可以降级为 warning，但不能影响真实测试结果判断

## 6. 边界说明

* 一键测试入口用于后端冒烟验证
* 不能替代完整系统测试、前端联调测试、生产数据库测试
* 不保证覆盖所有业务边界
