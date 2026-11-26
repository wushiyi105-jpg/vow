# 参与

## 本地跑起来

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m vow seed
python -m vow doctor
pytest -q
```

## 提 PR 之前

1. 规则改动必须落在 `domain/rules/`，并且新增一条 `rule_id`；
2. 每条 `rule_id` 至少一条断言；
3. `ruff check .`、`mypy vow`、`pytest -q` 全过；
4. 界面和命令里不要写死规则，规则只在 domain 里。

## 提交信息

`type: 一句话说清改了什么`，type 用 feat / fix / docs / test / refactor。
