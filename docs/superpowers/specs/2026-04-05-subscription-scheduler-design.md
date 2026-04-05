# Subscription Scheduler Design

## Goal

把 MusicPilot 的订阅执行从“只支持手动 run”推进到“支持最小自动调度”，同时不改变现有搜索、下载、整理主链语义。

## Scope

本轮只做应用内最小 scheduler：

- 应用启动后在 FastAPI lifespan 中启动后台轮询任务
- 自动扫描 `active + scheduled` 订阅
- 命中 due 条件时调用现有 `SubscriptionExecutionService.execute(...)`
- 保留现有 `/subscriptions/{id}/run` 手动入口

本轮不做：

- 分布式任务系统
- 外部消息队列
- cron 表达式
- 多进程协调
- 自动增量 chart refresh

## Scheduling model

### Subscription mode

新增正式模式：

- `manual`
- `scheduled`

兼容旧值：

- `scheduled_placeholder`

兼容策略：

- API 继续接受 `scheduled_placeholder`
- 落库与运行时统一归一到 `scheduled`

### Interval source

调度周期先放在 `preference_json.schedule_interval_minutes`。

如果没有显式值，使用默认值：

- `settings.subscription_scheduler_default_interval_minutes`

### Due rule

一个订阅会被 scheduler 执行，当且仅当：

- `status == active`
- `mode == scheduled`
- 当前没有 `running` 状态的 run
- 满足 `now >= baseline + interval`

`baseline` 计算：

- 优先 `last_run_at`
- 否则 `updated_at`
- 否则 `created_at`

## Runtime design

新增 `SubscriptionSchedulerService`，职责只包含：

- 扫描 due subscriptions
- 逐个触发执行
- 记录本轮调度结果统计
- 保护后台循环不因单个订阅异常退出

FastAPI lifespan 中：

- 启动 scheduler task
- shutdown 时优雅取消

## Config

新增配置：

- `MUSICPILOT_SUBSCRIPTION_SCHEDULER_ENABLED=true`
- `MUSICPILOT_SUBSCRIPTION_SCHEDULER_POLL_SECONDS=30`
- `MUSICPILOT_SUBSCRIPTION_SCHEDULER_DEFAULT_INTERVAL_MINUTES=360`

默认目标：

- 本地开发可开即用
- 默认六小时一次，避免开发时疯狂触发

## Data model

本轮不新增数据库列。

复用现有字段：

- `subscriptions.mode`
- `subscriptions.preference_json`
- `subscriptions.last_run_at`
- `subscription_runs.execution_status`

## API boundary

现有 API 路径不变：

- `POST /subscriptions`
- `PATCH /subscriptions/{id}`
- `POST /subscriptions/{id}/run`
- `GET /subscriptions/*`

只增强：

- `mode=scheduled` 正式可用
- 响应文案从“scheduled_placeholder”改成真实 scheduler 语义

本轮不新增 scheduler 管理 API。

## Testing

至少覆盖：

- `scheduled` 订阅满足 due 时会触发一次执行
- `manual` 订阅不会被自动触发
- 仍有 `running` run 的订阅不会重复触发
- `scheduled_placeholder` 输入会被归一到 `scheduled`
- lifespan 不影响现有 `/subscriptions/{id}/run`

## Success criteria

- 应用内可以自动触发 scheduled 订阅
- 现有手动 run 不受影响
- 现有 run 记录、search job、organize preview 语义不变
- 不引入新的调度框架或分布式依赖
