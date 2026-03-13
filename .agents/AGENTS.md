# Trading MCP AGENT Guide

本指南用于帮助 AGENT 快速理解 Trading MCP 项目的目标、架构与关键入口。

## 项目目标
- 提供交易场景的基础能力：行情数据抓取与技术指标计算。
- 以 MCP Server 形式对外提供工具：`trading_kline`、`trading_rsi`、`trading_ma`、`trading_macd`。
- 关键依赖：`uv`、`pydantic`、`akshare`、`TA-Lib`、`mcp`。

## 技术架构（模块视角 + 调用链）
- 入口：`main.py` 调用 `mcp_app.create_server()`，并以 `streamable-http` 运行服务。
- 服务层：`services/market_service.py` 负责业务编排与输出结构化结果。
- 数据层：`data/akshare_client.py` 通过 Akshare 拉取行情数据。
- 指标层：`indicators/engine.py` 封装 TA‑Lib 指标计算。
- 模型层：`models/mcp_tools.py` 使用 Pydantic 定义请求/响应模型与校验规则。
- 配置层：`config/mcp_settings.py` 与 `config/settings.py` 读取配置，环境变量前缀为 `TRADING_MCP_`。

## 文件目录结构说明
- `main.py` / `mcp_app.py`：程序入口与 MCP Server 创建。
- `config/`：配置与环境变量读取。
- `data/`：行情数据客户端与接口协议。
- `indicators/`：技术指标引擎封装。
- `models/`：MCP 工具请求/响应模型定义。
- `services/`：业务逻辑与数据/指标拼装。
- `utils/`：通用工具函数。
- `tests/`：单元测试（模型与服务层）。
- `openspec/`：历史规范与变更记录（背景参考）。

## 必要入口说明
- 运行 MCP Server：
  - `python main.py`
- MCP 工具概览：
  - `trading_kline` / `trading_rsi` / `trading_ma` / `trading_macd`（支持 offset 与日期范围分页，响应带结构化元数据）

## 编码说明

每次编写完成代码之后需要执行 `ruff` 进行代码格式化和检查。需要执行 `ty` 进行lint检查。
