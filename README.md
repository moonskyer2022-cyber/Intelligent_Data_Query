# AIQuery

AIQuery 是一个基于 LangGraph 的本地智能问数项目。它将自然语言问题转换为结构化查询计划，查询本地 MySQL 数据库 `ai_query`，并用 LLM 生成简洁结果说明；当问题适合可视化时，还会自动生成图表。

## 功能特点

- 自然语言问数：支持直接输入业务问题，如 GMV、销量、金额排名等。
- 查询计划解析：通过 LLM 生成单表、多表和聚合查询计划。
- MySQL 实时读取：动态读取 `information_schema` 获取表结构。
- 图表生成：支持柱状图、条形图、折线图、饼图。
- Web 界面：内置一个轻量对话式前端页面。

## 数据表

| 逻辑表名 | 物理表名 | 说明 |
| --- | --- | --- |
| 商品表 | `product` | 商品、价格、库存、类目 |
| 类目表 | `category` | 商品类目层级 |
| 用户表 | `user` | 用户与会员信息 |
| 订单主表 | `orders` | 订单成交、GMV、渠道、地区 |
| 订单明细表 | `order_item` | 订单行、销量、行金额 |
| 采购记录表 | `purchase_record` | 历史采购流水 |
| 对话记录表 | `chat_record` | 问答审计记录 |
| 问数示例表 | `query_example` | 示例问题 |

## 快速开始

1. 创建并激活虚拟环境。

```powershell
python -m venv .venv
.venv\Scripts\activate
```

2. 安装依赖。

```powershell
pip install -e .
```

3. 复制环境变量模板并填写配置。

```powershell
Copy-Item .env.example .env
```

需要至少配置：

- `LLM_API_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

4. 命令行运行问数。

```powershell
python run.py -q "本月订单GMV是多少？"
```

5. 启动 Web 服务。

```powershell
python run.py --server
```

浏览器打开 [http://localhost:8000](http://localhost:8000)。

## API

- `GET /`：前端页面
- `POST /run`：执行问数，body 示例：`{"user_question": "...", "session_id": "可选"}`
- `GET /examples`：加载示例问题
- `GET /tables`：加载数据表列表
- `GET /health`：健康检查
- `GET /static/charts/{filename}`：访问生成的图表图片

## 项目结构

```text
.
├─config/                # LLM 提示词配置
├─frontend/              # 前端页面
├─output/charts/         # 生成的图表
├─src/
│  ├─graphs/             # LangGraph 工作流
│  ├─llm/                # LLM 调用封装
│  ├─query/              # 查询计划与 SQL 生成
│  ├─storage/            # 数据库与元数据访问
│  └─tools/              # 图表工具
└─run.py                 # CLI / Web 启动入口
```

## 注意事项

- `.env`、`.venv/`、数据库文件和生成图表默认已被 `.gitignore` 排除。
- 当前服务需要本地可访问的 MySQL 数据库和可用的 LLM API。
- 如果数据库字段有变更，重启服务后会重新加载表结构。
