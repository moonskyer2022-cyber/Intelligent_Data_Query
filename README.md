# AIQuery - 本地智能问数

基于 LangGraph 的自然语言数据查询，连接本地 MySQL 数据库 `ai_query`，使用 DeepSeek 作为 LLM。

## 数据表

| 逻辑名 | 物理表 | 说明 |
|--------|--------|------|
| 商品表 | product | 商品、价格、库存、类目 |
| 类目表 | category | 商品类目层级 |
| 用户表 | user | 用户与会员信息 |
| 订单主表 | orders | 订单成交、GMV、渠道、地区 |
| 订单明细表 | order_item | 订单行、销量、行金额 |
| 采购记录表 | purchase_record | 历史扁平采购流水 |
| 对话记录表 | chat_record | 问答审计记录 |
| 问数示例表 | query_example | 示例问题（驱动前端示例） |

表结构从数据库 `information_schema` 动态加载，字段变更后重启服务即可生效。

## 快速开始

```powershell
cd C:\Users\admin\Desktop\智能问数\AIQuery

python -m venv .venv
.venv\Scripts\activate
pip install -e .

copy .env.example .env
# 编辑 .env 填入 LLM_API_KEY 和 DB_PASSWORD

python run.py -q "本月订单GMV是多少？"
python run.py --server
# 浏览器打开 http://localhost:8000
```

## API

- `GET /` — 前端页面
- `POST /run` — body: `{"user_question": "...", "session_id": "可选"}`
- `GET /examples` — 从 query_example 表加载示例问题
- `GET /tables` — 可查询数据表列表
- `GET /health` — 健康检查
- `GET /static/charts/{filename}` — 图表文件

## 前端

`frontend/` 为 Web 对话界面，示例问题与数据表列表从 API 动态加载。
