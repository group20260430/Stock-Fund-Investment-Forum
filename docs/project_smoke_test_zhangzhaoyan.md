# 张照炎全项目冒烟验证记录

## 1. 验证目标

本次只做当前分支的全项目冒烟验证，不开发新功能，不修改业务代码。

## 2. 验证环境

* Windows
* 分支：`feat/backend/forum-api`
* 后端：Python 3.13，`backend\.venv313`
* 前端：Node `v24.15.0`，npm `11.12.1`
* 最新提交：`73a5e74 test: include e2e in backend test runner`

## 3. 后端验证

执行命令：

```powershell
cd backend
python run_backend_tests.py
```

结果：

```text
RESULTS: 8 passed, 0 failed
```

覆盖：

* 模块接口测试
* 管理后台测试
* 搜索/发现测试
* 社交/群组测试
* 敏感词过滤测试
* 端到端 E2E 测试

## 4. 前端验证

执行命令：

```powershell
cd frontend
npm run build
```

结果：

* 成功
* 前端生产构建通过，已补齐 `marked` 和 `dompurify` 依赖
* Vite 产物已生成，构建过程仅出现 chunk size 和动态导入 warning

## 5. 已知边界

* 本次验证不等于完整人工 UI 测试
* 不等于生产环境部署验证
* 不等于真实 MySQL/线上环境压测
* 前后端接口联调仍需启动服务后在浏览器确认

## 6. 结论

当前分支完成一次基础全项目冒烟验证：后端一键测试通过，前端生产构建通过，未发现阻塞性构建或后端回归问题。
