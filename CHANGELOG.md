# 更新记录

## Unreleased

- 新增 `report`：一条命令出预算表、供应商比价、28 项倒排，支持 `--out`
- 28 项筹备清单与 30 条报价加价词典落为本地数据；模型只补疑点，本地词典兜底
- 模型隐藏费从 `review_vendor` 进入 `plan.hidden` 与最终报告，不再只生成不展示
- `0001_init` 改为显式 `op.create_table` / `op.create_index`，运行期走 `alembic upgrade`
- `app/` 只依赖 `ports`，新增内存假实现用例
- 开 ruff `E2`/`E3`；CI 增加 `docker build` 与 `/health` 探活

## 1.0.0

- 预算分类预警（5% / 15%）
- 桌数与人均换算
- 婚期倒排与逾期高亮
- 报价隐藏项原文校验
- 每日逾期扫描
