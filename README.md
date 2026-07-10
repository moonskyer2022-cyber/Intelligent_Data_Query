# AIQuery 本地智能问数平台

AIQuery 是一个基于 FastAPI、LangGraph、MySQL 和 LLM 的本地智能问数项目。它可以把自然语言业务问题解析成结构化查询计划，读取本地 `ai_query` 数据库，生成可读的业务结论，并在适合可视化的场景下自动输出图表。

当前版本包含一个作品展示式 Web 原型页面：页面整合了项目介绍、处理链路、数据模型、系统状态、示例问题和在线问数演示，适合用于课程设计、项目路演或本地功能验收。

## 功能亮点

- 自然语言问数：支持用中文直接询问 GMV、订单量、销量、金额排名、类目对比等业务问题。
- 意图分析：通过 LLM 生成结构化查询计划，识别目标表、字段、聚合方式、排序和筛选条件。
- MySQL 查询：动态读取 `information_schema`，结合白名单表结构生成并执行 SQL。
- 结果总结：将查询结果整理成更适合业务阅读的自然语言结论。
- 图表生成：支持柱状图、条形图、折线图、饼图等常见可视化输出。
- 会话上下文：通过 `session_id` 保存对话记录，支持连续追问。
- Web 展示：内置响应式前端页面，包含黑色系展示风格、示例问题、健康检查和实时问数入口。

## 技术栈

- Python 3.12+
- FastAPI / Uvicorn
- LangGraph / LangChain Core
- OpenAI-compatible LLM API
- MySQL / PyMySQL
- Matplotlib
- 原生 HTML、CSS、JavaScript

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

3. 创建 `.env` 并填写配置。

```powershell
Copy-Item .env.example .env
```

至少需要配置：

```text
LLM_API_KEY=你的模型 API Key
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的数据库密码
DB_NAME=ai_query
```

4. 初始化 MySQL 数据库。

```powershell
mysql -h 127.0.0.1 -P 3306 -u root -p < scripts/init_mysql.sql
```

5. 启动 Web 服务。

```powershell
python run.py --server
```

浏览器打开 [http://localhost:8000](http://localhost:8000) 使用 Web 问数页面。健康检查地址为 [http://localhost:8000/health](http://localhost:8000/health)。

## 命令行使用

```powershell
python run.py -q "本月订单 GMV 是多少？"
```

如果问题适合生成图表，结果中会返回对应的图表路径。

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/` | 前端页面 |
| `POST` | `/run` | 执行问数 |
| `GET` | `/examples` | 获取示例问题 |
| `GET` | `/tables` | 获取数据表列表 |
| `GET` | `/health` | 检查服务、数据库和 LLM 配置状态 |
| `GET` | `/static/charts/{filename}` | 访问生成的图表图片 |

`POST /run` 请求示例：

```json
{
  "user_question": "各省份订单金额排名，并生成图表",
  "session_id": "demo-session"
}
```

## 测试

项目内置了不依赖真实 MySQL 和 LLM 的核心单元测试：

```powershell
python -m unittest discover -s tests
```

测试覆盖内容包括 LLM JSON 解析、会话历史格式化、聚合排序 SQL 生成和健康检查接口。

## 项目结构

```text
.
├── config/                 # LLM 提示词与输出配置
├── frontend/               # Web 前端页面
├── scripts/                # MySQL 初始化脚本
├── src/
│   ├── graphs/             # LangGraph 工作流与节点
│   ├── llm/                # LLM 客户端封装
│   ├── query/              # 查询计划和 SQL 生成
│   ├── storage/            # 数据库和元数据访问
│   └── tools/              # 图表生成工具
├── tests/                  # 单元测试
├── pyproject.toml          # 项目依赖配置
└── run.py                  # CLI / Web 启动入口
```

## 注意事项

- `.env`、`.venv/`、缓存目录、运行日志和生成图表默认不提交到 Git。
- 服务运行前请确保 MySQL 可连接，并已执行 `scripts/init_mysql.sql`。
- 如果数据库字段或表结构发生变化，重启服务后会重新加载元数据。
- 图表生成依赖 Matplotlib；在部分 Windows 环境中首次运行可能会创建本地字体缓存。
