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

可用工具：
- `trading_kline(symbol, limit=30, offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_macd(symbol, limit, fast_period=12, slow_period=26, signal_period=9, offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_rsi(symbol, limit, period=14, offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_ma(symbol, limit, period=20, ma_type="sma", offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_volume(symbol, limit, offset=0, period_type="1d", start_date=None, end_date=None, response_format="markdown")`
- `trading_fundamental_cn_indicators(symbol, indicator="按报告期", limit=200, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_fundamental_us_report(stock, symbol="资产负债表", indicator="年报", limit=200, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_fundamental_us_indicators(symbol, indicator="年报", limit=200, offset=0, start_date=None, end_date=None, response_format="markdown")`

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

符号说明：
- A 股示例：`000001`、`300308.SZ`
- 美股示例：`AAPL.US`、`AAPL`、`105.AAPL`、`BRK.B`

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
