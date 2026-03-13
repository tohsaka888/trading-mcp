# trading-mcp

交易数据与技术指标的 MCP 服务，基于 `uv` + `pydantic` + `akshare` + `TA-Lib` 构建。

**项目内容**
- 提供股票行情数据查询与基础技术指标计算（K 线、RSI、MA、MACD）。
- 提供中长线基本面数据查询（A 股主要指标、美股三大报表、美股主要指标）。
- 统一的市场数据访问层，支持 A 股与美股（如 `AAPL.US`）。
- MCP 工具化接口，支持 Markdown 或 JSON 输出。

**项目架构**
- `data/`：市场数据接入层。`MarketDataClient` 接口 + `AkshareMarketDataClient` 实现。
- `services/`：业务服务层。将原始行情转换为标准结构，并驱动指标计算。
- `indicators/`：指标引擎封装。基于 TA-Lib 统一调用。
- `models/`：工具请求与响应模型（Pydantic）。
- `utils/`：MCP 输出格式化（表格 Markdown 等）。
- `mcp_app.py` / `main.py`：MCP 服务入口与工具注册。

**目录结构**
- `config/`：配置定义（Pydantic Settings）。
- `data/`：市场数据客户端实现。
- `indicators/`：指标计算引擎。
- `models/`：请求/响应模型。
- `services/`：业务服务层。
- `tests/`：单元测试。
- `utils/`：输出格式化与辅助工具。
- `mcp_app.py`：MCP 工具注册。
- `main.py`：服务启动入口。

**安装与依赖**
1. 安装依赖：

```bash
uv sync --extra dev
```

2. 安装 TA-Lib 系统库：
- macOS: `brew install ta-lib`
- Debian/Ubuntu: `sudo apt-get install libta-lib0 libta-lib0-dev`
- Windows: 使用对应 Python 版本的预编译 wheel

**配置说明**
配置通过环境变量 `TRADING_MCP_` 前缀覆盖：

```bash
export TRADING_MCP_ENVIRONMENT=dev
export TRADING_MCP_DATA_DIR=./data
export TRADING_MCP_DEFAULT_SYMBOL=000001
export TRADING_MCP_HOST=0.0.0.0
export TRADING_MCP_PORT=8000
```

字段含义：
- `TRADING_MCP_ENVIRONMENT`：运行环境标识（如 `dev` / `test` / `prod`）。
- `TRADING_MCP_DATA_DIR`：本地数据目录。
- `TRADING_MCP_DEFAULT_SYMBOL`：默认行情标的。
- `TRADING_MCP_HOST`：MCP 服务监听地址。
- `TRADING_MCP_PORT`：MCP 服务端口。

**Python 用法**

```python
from trading_mcp.config import Settings
from trading_mcp.data import AkshareMarketDataClient
from trading_mcp.indicators import IndicatorEngine

settings = Settings(environment="dev", data_dir="./data", default_symbol="000001")
client = AkshareMarketDataClient()
frame = client.fetch(settings.default_symbol, "2024-01-01", "2024-02-01")

engine = IndicatorEngine()
close_series = frame["close"] if "close" in frame.columns else frame.iloc[:, 0]
result = engine.compute("sma", close_series, timeperiod=5)
print(result.tail())
```

**MCP 服务**
启动 MCP 服务（streamable HTTP）：

```bash
python main.py
```

启动 MCP Inspector（适配 WSL，可从宿主机访问）：

```bash
./dev.sh
```

默认会使用以下 Inspector 配置：
- `MCP_INSPECTOR_HOST=0.0.0.0`
- `MCP_INSPECTOR_CLIENT_PORT=6274`
- `MCP_INSPECTOR_SERVER_PORT=6277`
- `MCP_INSPECTOR_AUTO_OPEN=false`

在 Windows 宿主机浏览器中优先访问：

```text
http://localhost:6274
```

如本机未启用 WSL `localhost` 转发，也可以先在 WSL 内执行 `hostname -I` 查看 IP，再从宿主机访问 `http://<wsl-ip>:6274`。

如果你只想本机 Linux 环境访问，可覆盖为：

```bash
MCP_INSPECTOR_HOST=127.0.0.1 ./dev.sh
```

注意：Inspector 代理具备启动本地进程的能力。`0.0.0.0` 仅应在受信任网络环境中使用。

可用工具：
- `trading_kline(symbol, limit=30, offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_macd(symbol, limit, fast_period=12, slow_period=26, signal_period=9, offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_rsi(symbol, limit, period=14, offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_ma(symbol, limit, period=20, ma_type="sma", offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_volume(symbol, limit, offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_fund_flow_individual_em(symbol, limit=200, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_fund_flow_individual_rank_em(indicator="5日", limit=200, offset=0, response_format="markdown")`
- `trading_fund_flow_sector_rank_em(indicator="今日", sector_type="行业资金流", limit=200, offset=0, response_format="markdown")`
- `trading_fund_flow_sector_summary_em(symbol, indicator="今日", limit=200, offset=0, response_format="markdown")`
- `trading_fundamental_cn_indicators(symbol, indicator="按报告期", limit=200, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_fundamental_us_report(stock, symbol="资产负债表", indicator="年报", limit=200, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_fundamental_us_indicators(symbol, indicator="年报", limit=200, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_industry_summary_ths(limit=200, offset=0, response_format="markdown")`
- `trading_industry_index_ths(symbol, limit=200, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_industry_name_em(limit=200, offset=0, response_format="markdown")`
- `trading_industry_spot_em(symbol, limit=200, offset=0, response_format="markdown")`
- `trading_industry_cons_em(symbol, limit=200, offset=0, response_format="markdown")`
- `trading_industry_hist_em(symbol, period="日k", adjust="none", limit=200, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_industry_hist_min_em(symbol, period="5", limit=200, offset=0, response_format="markdown")`

`trading_fundamental_cn_indicators` 参数说明：
- `indicator` 枚举：`按报告期`、`按单季度`
- `symbol` 兼容输入：`000001`、`000001.SZ`、`600519.SH`（自动补全或规范化后缀）
- 基本面结果按原始行格式返回：`columns + items`

`trading_fundamental_us_report` 参数说明：
- `symbol`（报表类型）枚举：`资产负债表`、`综合损益表`、`现金流量表`
- `indicator`（报表周期）枚举：`年报`、`单季报`、`累计季报`
- `stock` 兼容输入：`TSLA`、`AAPL.US`、`105.AAPL`、`BRK.B`（内部规范化为 AkShare 可识别 ticker）

`trading_fundamental_us_indicators` 参数说明：
- `indicator` 枚举：`年报`、`单季报`、`累计季报`
- `symbol` 兼容输入：`TSLA`、`AAPL.US`、`105.AAPL`、`BRK.B`
- 基本面结果按原始行格式返回：`columns + items`

`trading_volume` 字段说明：
- 返回字段：`timestamp`、`volume`、`amount`、`turnover_rate`
- 单位策略：保留数据源原始单位，并通过响应字段返回单位
  - A 股：`volume_unit=lot`，`amount_unit=CNY`
  - 美股：`volume_unit=share`，`amount_unit=USD`
  - `turnover_rate_unit=percent`
- 当周/月是由日线聚合而来时，`turnover_rate` 可能为 `null`

资金流向工具说明：
- `trading_fund_flow_individual_em`：东方财富个股资金流，`symbol` 支持 `000001`、`600519.SH`、`830799.BJ`
- `trading_fund_flow_individual_rank_em`：东方财富个股资金流排名
  - `indicator` 枚举：`今日`、`3日`、`5日`、`10日`
- `trading_fund_flow_sector_rank_em`：东方财富板块资金流排名
  - `indicator` 枚举：`今日`、`5日`、`10日`
  - `sector_type` 枚举：`行业资金流`、`概念资金流`、`地域资金流`
- `trading_fund_flow_sector_summary_em`：东方财富指定板块的成份股资金流
  - `symbol` 为东方财富板块名称，如 `电源设备`
  - `indicator` 枚举：`今日`、`5日`、`10日`
- 资金流向结果统一按原始表格返回：`columns + items`

符号说明：
- A 股示例：`000001`、`300308.SZ`
- 美股示例：`AAPL.US`、`AAPL`、`105.AAPL`、`BRK.B`

行业板块工具说明：
- `trading_industry_summary_ths`：同花顺行业一览表，返回原始板块汇总字段
- `trading_industry_index_ths`：同花顺行业指数，`symbol` 为板块名，支持 `start_date` / `end_date`
- `trading_industry_name_em`：东方财富行业板块名称列表
- `trading_industry_spot_em`：东方财富行业板块实时行情，`symbol` 为板块名
- `trading_industry_cons_em`：东方财富行业板块成份股，`symbol` 为板块名
- `trading_industry_hist_em`：东方财富行业板块历史行情
  - `period` 枚举：`日k`、`周k`、`月k`
  - `adjust` 枚举：`none`、`qfq`、`hfq`；其中 `none` 表示不复权
- `trading_industry_hist_min_em`：东方财富行业板块分时历史行情
  - `period` 枚举：`1`、`5`、`15`、`30`、`60`
- 行业板块结果统一按原始表格返回：`columns + items`

**响应结构（structuredContent）**

```json
{
  "stock": "TSLA",
  "symbol": "资产负债表",
  "indicator": "年报",
  "columns": ["REPORT_DATE", "ITEM_NAME", "AMOUNT"],
  "items": [],
  "count": 0,
  "total": 0,
  "limit": 200,
  "offset": 0,
  "has_more": false,
  "next_offset": null,
  "start_date": null,
  "end_date": null
}
```
