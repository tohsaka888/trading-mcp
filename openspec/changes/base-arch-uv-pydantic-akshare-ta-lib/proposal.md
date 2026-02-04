## Why

当前项目缺少清晰的基础架构与统一的依赖/配置规范，导致后续功能扩展（行情数据接入、指标计算、策略开发）成本高且容易产生实现分歧。现在先建立以 uv 为核心的工程基础，并引入 pydantic、akshare、ta-lib 作为统一的配置校验、数据源与指标计算基座。

## What Changes

- 建立 uv 驱动的项目基础结构与依赖管理规范
- 引入 pydantic 作为配置与输入数据的统一校验模型
- 增加 akshare 数据接入的统一适配层
- 增加 ta-lib 指标计算的基础封装与调用入口
- 明确模块边界与目录布局，便于后续扩展与测试

## Capabilities

### New Capabilities
- `project-foundation`: 以 uv 为核心的工程结构、依赖管理与基础目录布局
- `config-validation`: 基于 pydantic 的配置与输入校验模型
- `market-data-access`: 通过 akshare 的行情/数据接入能力与统一适配接口
- `indicator-engine`: 基于 ta-lib 的指标计算封装与调用入口

### Modified Capabilities

## Impact

- 依赖管理与构建方式（uv、pyproject）
- 核心包结构与模块组织
- 新增外部依赖：pydantic、akshare、ta-lib
- 后续 spec/design/tasks 将围绕上述能力展开
