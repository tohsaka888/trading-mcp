## Context

项目需要一套明确的工程基础与模块边界，以便后续扩展行情接入、指标计算与策略开发。当前尚无统一的依赖管理、配置校验与数据/指标的基础封装，因此本次设计聚焦在工程结构与关键依赖的落地方式。

## Goals / Non-Goals

**Goals:**
- 以 uv 为唯一依赖与构建入口，统一 pyproject 与锁定方式
- 建立清晰的包结构与模块边界，便于后续扩展
- 使用 pydantic 统一配置与输入校验
- 提供 akshare 数据接入的抽象与实现入口
- 提供 ta-lib 指标计算的封装入口

**Non-Goals:**
- 不实现完整策略/回测/交易执行框架
- 不覆盖多数据源切换与复杂缓存体系
- 不引入分布式服务或微服务拆分

## Decisions

- 依赖管理使用 uv：
  选择 uv 统一依赖解析与锁定，减少 pip/poetry 混用带来的差异。备选方案为 poetry，但 uv 在速度与简化工具链方面更符合当前“基础架构”目标。

- 配置模型使用 pydantic v2 + pydantic-settings：
  采用 `BaseModel` 与 `BaseSettings` 统一配置入口与校验能力。备选方案为 dataclasses + 自定义校验，但 pydantic 能显著降低校验复杂度并提高一致性。

- 数据接入采用接口 + akshare 实现：
  设计 `MarketDataClient` 抽象接口，提供 `AkshareMarketDataClient` 实现。备选方案为直接在业务层调用 akshare，但会耦合外部 API 并增加后续替换成本。

- 指标计算封装在独立模块：
  提供 `IndicatorEngine`/`Indicators` 模块封装 ta-lib 调用与输入输出约束。备选方案为在策略层直接调用 ta-lib，但会导致重复处理与难以统一校验。

- 目录结构以核心能力划分：
  建议包含 `config/`、`data/`、`indicators/`、`utils/` 等模块，避免按脚本类型堆叠。备选方案为平铺文件结构，但可维护性较差。

## Risks / Trade-offs

- [TA-Lib 需要本地依赖支持] → 在 README/安装指南中明确系统依赖与常见平台安装方式，并在运行时提供清晰错误提示
- [akshare API 变更或不稳定] → 通过适配层隔离，集中处理异常与返回格式差异，必要时锁定版本
- [配置模型过度复杂] → 限制配置层级与字段数量，保持“必要即可”

## Migration Plan

- 添加/更新 uv 依赖与锁文件
- 创建核心包结构与空实现骨架
- 引入 pydantic 配置模型与最小可用示例
- 添加 akshare 数据客户端与最小调用示例
- 添加 ta-lib 指标封装与最小调用示例
- 更新 README/说明文件（依赖与运行方式）

回滚：移除新增依赖与模块目录，恢复原有入口文件。

## Open Questions

- 需要支持的 akshare 数据接口范围（行情/财务/宏观等）有哪些？
- 指标计算的输入输出数据结构是否统一使用 pandas DataFrame/Series？
- 是否需要提供最小 CLI 或脚本入口用于验证基础功能？
