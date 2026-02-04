# trading-mcp

交易数据与技术指标的 MCP 服务，基于 `uv` + `pydantic` + `akshare` + `TA-Lib` 构建。

**项目内容**
- 提供股票行情数据查询与基础技术指标计算（K 线、RSI、MA、MACD）。
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
- `trading_kline(symbol, limit, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_macd(symbol, limit, fast_period=12, slow_period=26, signal_period=9, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_rsi(symbol, limit, period=14, offset=0, start_date=None, end_date=None, response_format="markdown")`
- `trading_ma(symbol, limit, period=20, ma_type="sma", offset=0, start_date=None, end_date=None, response_format="markdown")`

符号说明：
- A 股示例：`000001`、`300308.SZ`
- 美股示例：`AAPL.US`、`AAPL`、`105.AAPL`

**响应结构（structuredContent）**

```json
{
  "symbol": "000001",
  "items": [],
  "count": 0,
  "total": 0,
  "limit": 20,
  "offset": 0,
  "has_more": false,
  "next_offset": null,
  "start_date": "2024-01-01",
  "end_date": "2024-02-01"
}
```
