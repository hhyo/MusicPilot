# Subscription Scheduler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one minimal in-process scheduler so active scheduled subscriptions can automatically execute without changing the existing manual run API.

**Architecture:** Normalize subscription mode to `scheduled`, compute due state from existing subscription fields, run a lightweight background polling loop in FastAPI lifespan, and keep execution delegated to the existing `SubscriptionExecutionService`.

**Tech Stack:** FastAPI lifespan, SQLAlchemy, unittest, SQLite

---

### Task 1: Lock scheduler behavior with failing tests

**Files:**
- Create: `backend/tests/test_subscription_scheduler.py`
- Modify: `backend/tests/test_moviepilot_semantics.py`

- [ ] **Step 1: Write failing scheduler service tests**

```python
def test_due_scheduled_subscription_executes_once():
    ...
    assert executed_ids == ['sub-1']

def test_manual_subscription_is_ignored():
    ...
    assert executed_ids == []

def test_running_subscription_is_ignored():
    ...
    assert executed_ids == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_subscription_scheduler.py'`

Expected: FAIL because scheduler service does not exist yet.

- [ ] **Step 3: Write failing mode normalization test**

```python
def test_create_subscription_normalizes_scheduled_placeholder_to_scheduled():
    ...
    assert result.mode.value == 'scheduled'
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'`

Expected: FAIL because old placeholder mode is still stored directly.

### Task 2: Implement scheduler core and mode normalization

**Files:**
- Create: `backend/app/services/subscription_scheduler.py`
- Modify: `backend/app/schemas/orchestration.py`
- Modify: `backend/app/services/subscriptions.py`
- Modify: `backend/app/repositories/orchestration.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/dependencies.py`

- [ ] **Step 1: Add real scheduled mode and normalize legacy alias**

Implement:

```python
class SubscriptionMode(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    SCHEDULED_PLACEHOLDER = "scheduled_placeholder"
```

and normalize incoming/outgoing values to `scheduled`.

- [ ] **Step 2: Add scheduler config**

Add:

```python
subscription_scheduler_enabled: bool = True
subscription_scheduler_poll_seconds: float = 30.0
subscription_scheduler_default_interval_minutes: int = 360
```

- [ ] **Step 3: Add repository helpers**

Implement helpers for:

- listing `active` subscriptions
- checking whether a subscription currently has a `running` run

- [ ] **Step 4: Implement `SubscriptionSchedulerService`**

Core methods:

- `normalize_mode(value) -> str`
- `schedule_interval_minutes(subscription) -> int`
- `is_due(subscription, now) -> bool`
- `run_pending_once() -> dict`

- [ ] **Step 5: Run targeted tests**

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_subscription_scheduler.py'`

Expected: PASS

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'`

Expected: PASS

### Task 3: Wire scheduler into app runtime and update docs/UI semantics

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/routes/subscriptions.py`
- Modify: `frontend/src/types/orchestration.ts`
- Modify: `frontend/src/views/SubscriptionsView.vue`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/28_项目整体任务盘点与执行路线.md`
- Create: `docs/31_订阅调度运行态说明.md`

- [ ] **Step 1: Start scheduler loop in lifespan**

Create a cancellable background task that:

- sleeps `poll_seconds`
- opens a DB session
- runs `scheduler.run_pending_once()`
- logs and continues on error

- [ ] **Step 2: Update API and frontend wording**

Replace “scheduled_placeholder / manual-only” wording with:

- `manual`
- `scheduled`
- “当前支持最小应用内 scheduler”

- [ ] **Step 3: Document env and runtime behavior**

Add env examples:

```env
MUSICPILOT_SUBSCRIPTION_SCHEDULER_ENABLED=true
MUSICPILOT_SUBSCRIPTION_SCHEDULER_POLL_SECONDS=30
MUSICPILOT_SUBSCRIPTION_SCHEDULER_DEFAULT_INTERVAL_MINUTES=360
```

- [ ] **Step 4: Run full verification**

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests`

Expected: all backend tests pass

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend && PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build`

Expected: build succeeds

Run:

`cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py`

Expected: runtime packaging succeeds
