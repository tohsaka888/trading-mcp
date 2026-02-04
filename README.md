# trading-mcp

Foundational trading utilities powered by uv, pydantic, akshare, and TA-Lib.

## Setup

1. Install dependencies with uv:

```bash
uv sync --extra dev
```

2. TA-Lib requires a native system library. Install it before syncing:

- macOS: `brew install ta-lib`
- Debian/Ubuntu: `sudo apt-get install libta-lib0 libta-lib0-dev`
- Windows: use a prebuilt wheel for your Python version

## Configuration

Settings are validated with pydantic and can be overridden via environment variables
using the `TRADING_MCP_` prefix:

```bash
export TRADING_MCP_ENVIRONMENT=dev
export TRADING_MCP_DATA_DIR=./data
export TRADING_MCP_DEFAULT_SYMBOL=000001
```

## Usage

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

## MCP Server

Start the MCP server with streamable HTTP transport:

```bash
export TRADING_MCP_HOST=0.0.0.0
export TRADING_MCP_PORT=8000
python main.py
```

Available tools:
- `kline(symbol, limit)` → OHLCV bar list
- `macd(symbol, limit, fast_period=12, slow_period=26, signal_period=9)` → MACD series
- `rsi(symbol, limit, period=14)` → RSI series
- `ma(symbol, limit, period=20, ma_type="sma")` → moving average series
