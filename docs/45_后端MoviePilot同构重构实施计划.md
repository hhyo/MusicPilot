# MusicPilot 后端 MoviePilot 同构重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 MusicPilot 后端与 `plugin_runtime` 后端镜像激进重构为与 MoviePilot 同构的结构，只保留音乐领域语义差异，彻底删除旧 `routes/services/models/repositories/adapters/tasks` 主结构。

**Architecture:** 重构后后端只保留 `api/endpoints + chain + db + helper + modules + core + schemas + startup + utils`。API、调度和本地运行入口只直接调用 8 条 `Music*Chain`，数据访问统一进入 `db/*_oper.py`，旧目录物理删除，不保留 wrapper、alias import 或 facade。

**Tech Stack:** Python 3、FastAPI、Pydantic、SQLAlchemy、unittest、plugin runtime mirror、MoviePilot 风格 `ChainBase`

---

## 预期文件结构

### 新结构

- `backend/app/api/endpoints/__init__.py`
- `backend/app/api/endpoints/media.py`
- `backend/app/api/endpoints/search.py`
- `backend/app/api/endpoints/download.py`
- `backend/app/api/endpoints/transfer.py`
- `backend/app/api/endpoints/subscribe.py`
- `backend/app/api/endpoints/chart.py`
- `backend/app/api/endpoints/dashboard.py`
- `backend/app/api/endpoints/settings.py`
- `backend/app/api/endpoints/probe.py`
- `backend/app/chain/__init__.py`
- `backend/app/chain/media.py`
- `backend/app/chain/search.py`
- `backend/app/chain/download.py`
- `backend/app/chain/transfer.py`
- `backend/app/chain/subscribe.py`
- `backend/app/chain/chart.py`
- `backend/app/chain/dashboard.py`
- `backend/app/db/models/*.py`
- `backend/app/db/acquisition_oper.py`
- `backend/app/db/orchestration_oper.py`
- `backend/app/db/charts_oper.py`
- `backend/app/db/settings_oper.py`
- `backend/app/db/metadata_oper.py`
- `backend/app/helper/*.py`
- `backend/app/modules/*.py`
- `backend/app/startup/*.py`
- `backend/app/utils/*.py`
- `backend/tests/api/*.py`
- `backend/tests/chain/*.py`
- `backend/tests/db/*.py`

### 旧结构清理目标

- 删除 `backend/app/api/routes/`
- 删除 `backend/app/services/`
- 删除 `backend/app/models/`
- 删除 `backend/app/repositories/`
- 删除 `backend/app/adapters/`
- 删除 `backend/app/tasks/`
- `plugin_runtime/plugins/musicpilot/` 同步删除以上旧目录

---

### Task 1: 落位新目录骨架与统一入口

**Files:**
- Create: `backend/app/api/endpoints/__init__.py`
- Create: `backend/app/chain/__init__.py`
- Create: `backend/app/startup/__init__.py`
- Create: `backend/app/utils/__init__.py`
- Modify: `backend/app/api/router.py`
- Modify: `backend/app/core/dependencies.py`
- Test: `backend/tests/api/test_router_endpoints.py`
- Test: `backend/tests/chain/test_chain_base.py`

- [ ] **Step 1: 写路由与 ChainBase 的失败测试**

```python
from pathlib import Path
from unittest import TestCase


class RouterEndpointsLayoutTest(TestCase):
    def test_router_imports_endpoints_package(self) -> None:
        router_path = Path("backend/app/api/router.py")
        content = router_path.read_text(encoding="utf-8")
        self.assertIn("api.endpoints", content)
        self.assertNotIn("api.routes", content)


class MusicChainBaseLayoutTest(TestCase):
    def test_chain_base_exists_in_chain_package(self) -> None:
        chain_init = Path("backend/app/chain/__init__.py")
        content = chain_init.read_text(encoding="utf-8")
        self.assertIn("class MusicChainBase", content)
```

- [ ] **Step 2: 运行测试，确认当前结构失败**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.api.test_router_endpoints tests.chain.test_chain_base
```

Expected:

```text
FAIL: test_router_imports_endpoints_package
FAIL: test_chain_base_exists_in_chain_package
```

- [ ] **Step 3: 建立新骨架并切换 router/dependencies 到新入口**

```python
# backend/app/chain/__init__.py
from app.core.cache import RuntimeTTLCache
from app.log import logger


class MusicChainBase:
    def __init__(self) -> None:
        self.logger = logger
        self.cache = RuntimeTTLCache()
```

```python
# backend/app/api/router.py
from app.api.endpoints import (
    media,
    search,
    download,
    transfer,
    subscribe,
    chart,
    dashboard,
    settings,
    probe,
)
```

```python
# backend/app/core/dependencies.py
from app.chain.media import MusicMediaChain
from app.chain.search import MusicSearchChain
from app.chain.download import MusicDownloadChain
from app.chain.transfer import MusicTransferChain
from app.chain.subscribe import MusicSubscribeChain
from app.chain.chart import MusicChartChain
from app.chain.dashboard import MusicDashboardChain
```

- [ ] **Step 4: 重新运行测试**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.api.test_router_endpoints tests.chain.test_chain_base
```

Expected:

```text
OK
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/router.py backend/app/chain/__init__.py backend/app/startup/__init__.py backend/app/utils/__init__.py backend/app/core/dependencies.py backend/tests/api/test_router_endpoints.py backend/tests/chain/test_chain_base.py
git commit -m "refactor: create moviepilot-aligned backend skeleton"
```

### Task 2: 重排数据层为 `db/models + *_oper.py`

**Files:**
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/models/__init__.py`
- Create: `backend/app/db/acquisition_oper.py`
- Create: `backend/app/db/orchestration_oper.py`
- Create: `backend/app/db/charts_oper.py`
- Create: `backend/app/db/settings_oper.py`
- Create: `backend/app/db/metadata_oper.py`
- Modify: `backend/app/db_init.py`
- Modify: `backend/app/core/dependencies.py`
- Modify: `backend/app/__init__.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/db/test_acquisition_oper.py`
- Test: `backend/tests/db/test_orchestration_oper.py`
- Test: `backend/tests/db/test_charts_oper.py`

- [ ] **Step 1: 写 `*_oper.py` 数据访问测试**

```python
from unittest import TestCase

from app.db.acquisition_oper import AcquisitionOper


class AcquisitionOperTest(TestCase):
    def test_acquisition_oper_exposes_search_job_crud(self) -> None:
        oper = AcquisitionOper()
        self.assertTrue(hasattr(oper, "get_search_job"))
        self.assertTrue(hasattr(oper, "save_search_job"))
        self.assertTrue(hasattr(oper, "delete_search_job"))
```

- [ ] **Step 2: 运行测试，确认 `db/*_oper.py` 尚未建立**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.db.test_acquisition_oper tests.db.test_orchestration_oper tests.db.test_charts_oper
```

Expected:

```text
ModuleNotFoundError: No module named 'app.db.acquisition_oper'
```

- [ ] **Step 3: 迁移模型与 repository 语义**

```python
# backend/app/db/acquisition_oper.py
from app.db.models.acquisition import SearchJobModel, SearchCandidateModel


class AcquisitionOper:
    def get_search_job(self, job_id: str) -> SearchJobModel | None:
        return self.session.get(SearchJobModel, job_id)

    def save_search_job(self, model: SearchJobModel) -> SearchJobModel:
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model

    def delete_search_job(self, job_id: str) -> None:
        model = self.get_search_job(job_id)
        if model is not None:
            self.session.delete(model)
            self.session.commit()
```

```python
# backend/app/db/orchestration_oper.py
class OrchestrationOper:
    def get_download_binding(self, binding_id: str):
        return self.session.get(DownloadBindingModel, binding_id)

    def list_transfer_pending_bindings(self):
        return (
            self.session.query(DownloadBindingModel)
            .filter(DownloadBindingModel.status.in_(["host_submitted", "pending_history_sync", "handoff_unresolved"]))
            .all()
        )
```

- [ ] **Step 4: 全量替换旧 import**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot && rg -n "app\\.(models|repositories)" backend/app plugin_runtime/plugins/musicpilot
```

Expected:

```text
0 matches
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/db backend/tests/db
git commit -m "refactor: move persistence layer to db opers"
```

### Task 3: 重建 `MusicMediaChain`

**Files:**
- Create: `backend/app/chain/media.py`
- Create: `backend/app/helper/music_media_input.py`
- Create: `backend/app/helper/music_meta_base.py`
- Create: `backend/app/modules/music_media_recognizer.py`
- Modify: `backend/app/api/endpoints/media.py`
- Modify: `backend/app/api/endpoints/search.py`
- Test: `backend/tests/chain/test_media_chain.py`
- Test: `backend/tests/api/test_media_endpoint.py`

- [ ] **Step 1: 写媒体链顶层行为测试**

```python
from unittest import TestCase

from app.chain.media import MusicMediaChain
from app.schemas.music_media import MusicMediaInput


class MusicMediaChainTest(TestCase):
    def test_prepare_returns_input_and_meta_base(self) -> None:
        chain = MusicMediaChain()
        result = chain.prepare(MusicMediaInput(entity_hint="track", title="Song"))
        self.assertIsNotNone(result.media_input)
        self.assertIsNotNone(result.meta_base)

    def test_resolve_returns_music_media_info(self) -> None:
        chain = MusicMediaChain()
        result = chain.resolve(MusicMediaInput(entity_hint="artist", title="Artist"))
        self.assertIsNotNone(result.music_media_info)
```

- [ ] **Step 2: 运行测试，确认新链文件不存在**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.chain.test_media_chain tests.api.test_media_endpoint
```

Expected:

```text
ModuleNotFoundError: No module named 'app.chain.media'
```

- [ ] **Step 3: 实现媒体链与支撑 helper/module**

```python
# backend/app/chain/media.py
from app.chain import MusicChainBase
from app.helper.music_media_input import MusicMediaInputHelper
from app.helper.music_meta_base import MusicMetaBaseHelper
from app.modules.music_media_recognizer import MusicMediaRecognizerModule


class MusicMediaChain(MusicChainBase):
    def __init__(self) -> None:
        super().__init__()
        self.input_helper = MusicMediaInputHelper()
        self.meta_helper = MusicMetaBaseHelper()
        self.recognizer = MusicMediaRecognizerModule()

    def prepare(self, media_input):
        normalized_input = self.input_helper.normalize(media_input)
        meta_base = self.meta_helper.build(normalized_input)
        return self._build_prepare_result(normalized_input, meta_base)

    def resolve(self, media_input):
        prepared = self.prepare(media_input)
        media_info = self.recognizer.resolve(prepared.meta_base)
        return self._build_resolve_result(prepared, media_info)
```

- [ ] **Step 4: endpoint 改为直接调用 `MusicMediaChain`**

```python
# backend/app/api/endpoints/media.py
@router.post("/resolve")
def resolve(payload: MediaResolveRequest, chain: MusicMediaChain = Depends(get_music_media_chain)):
    return chain.resolve(payload.media_input)
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/chain/media.py backend/app/helper/music_media_input.py backend/app/helper/music_meta_base.py backend/app/modules/music_media_recognizer.py backend/app/api/endpoints/media.py backend/app/api/endpoints/search.py backend/tests/chain/test_media_chain.py backend/tests/api/test_media_endpoint.py
git commit -m "refactor: rebuild music media chain"
```

### Task 4: 重建 `MusicChartChain`

**Files:**
- Create: `backend/app/chain/chart.py`
- Create: `backend/app/api/endpoints/chart.py`
- Modify: `backend/app/modules/chart_provider.py`
- Modify: `backend/app/db/charts_oper.py`
- Modify: `backend/app/startup/chart_refresh.py`
- Test: `backend/tests/chain/test_chart_chain.py`
- Test: `backend/tests/api/test_chart_endpoint.py`

- [ ] **Step 1: 写榜单链测试**

```python
from unittest import TestCase

from app.chain.chart import MusicChartChain


class MusicChartChainTest(TestCase):
    def test_refresh_enabled_refreshes_all_enabled_charts(self) -> None:
        result = MusicChartChain().refresh_enabled()
        self.assertTrue(hasattr(result, "refreshed_chart_ids"))
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.chain.test_chart_chain tests.api.test_chart_endpoint
```

Expected:

```text
ModuleNotFoundError: No module named 'app.chain.chart'
```

- [ ] **Step 3: 实现 `MusicChartChain` 与 endpoint**

```python
class MusicChartChain(MusicChainBase):
    def list_providers(self):
        return self.provider_module.list_providers()

    def list_charts(self):
        return self.charts_oper.list_charts()

    def get_chart(self, chart_id: str):
        chart = self.charts_oper.get_chart(chart_id)
        return self._build_chart_view(chart)

    def refresh_chart(self, chart_id: str):
        payload = self.provider_module.fetch_chart(chart_id)
        stored = self.charts_oper.replace_chart(chart_id, payload)
        return self._build_refresh_result(stored)

    def refresh_enabled(self):
        refreshed_chart_ids = []
        for chart in self.charts_oper.list_enabled_charts():
            self.refresh_chart(chart.chart_id)
            refreshed_chart_ids.append(chart.chart_id)
        return self._build_refresh_all_result(refreshed_chart_ids)
```

- [ ] **Step 4: 将 discovery 组装与 chart entry -> subscription 收口到链**

```python
class MusicChartChain(MusicChainBase):
    def build_discovery_entry(self, chart_item):
        media_input = self.media_chain.input_from_chart_item(chart_item)
        prepared = self.media_chain.prepare(media_input)
        return DiscoveryEntryView.model_validate(
            {
                "entry": chart_item,
                "media_input": prepared.media_input,
                "meta_base": prepared.meta_base,
                "recognition_assessment": prepared.recognition_assessment,
            }
        )

    def subscribe_entry(self, chart_id: str, entry_id: str, payload):
        chart = self.get_chart(chart_id)
        entry = next(item for item in chart.items if item.id == entry_id)
        return self.subscribe_chain.create_from_chart_entry(entry, payload)
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/chain/chart.py backend/app/api/endpoints/chart.py backend/app/modules/chart_provider.py backend/app/db/charts_oper.py backend/app/startup/chart_refresh.py backend/tests/chain/test_chart_chain.py backend/tests/api/test_chart_endpoint.py
git commit -m "refactor: rebuild music chart chain"
```

### Task 5: 重建 `MusicSearchChain`

**Files:**
- Create: `backend/app/chain/search.py`
- Create: `backend/app/api/endpoints/search.py`
- Create: `backend/app/helper/query_builder.py`
- Create: `backend/app/helper/search_scoring.py`
- Modify: `backend/app/db/acquisition_oper.py`
- Test: `backend/tests/chain/test_search_chain.py`
- Test: `backend/tests/api/test_search_endpoint.py`

- [ ] **Step 1: 写搜索链与 job 生命周期测试**

```python
from unittest import TestCase

from app.chain.search import MusicSearchChain


class MusicSearchChainTest(TestCase):
    def test_create_and_run_job(self) -> None:
        chain = MusicSearchChain()
        job = chain.create_job({"title": "Song", "entity_type": "track", "artist_names": ["Artist"]})
        result = chain.run_job(job.id)
        self.assertEqual(result.state, "completed")
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.chain.test_search_chain tests.api.test_search_endpoint
```

Expected:

```text
ModuleNotFoundError: No module named 'app.chain.search'
```

- [ ] **Step 3: 实现 `MusicSearchChain`**

```python
class MusicSearchChain(MusicChainBase):
    def preview_query(self, request):
        query = self.query_helper.build(request)
        return self._build_query_preview(query)

    def create_job(self, request):
        query = self.query_helper.build(request)
        job = self.acquisition_oper.create_search_job(query)
        return self._build_job_view(job)

    def run_job(self, job_id: str):
        job = self.acquisition_oper.get_search_job(job_id)
        candidates = self.search_module.search(job.query_payload)
        scored = self.scoring_helper.score_candidates(candidates, job.query_payload)
        stored = self.acquisition_oper.replace_candidates(job_id, scored)
        return self._build_run_result(job, stored)

    def retry_job(self, job_id: str):
        self.acquisition_oper.mark_job_retrying(job_id)
        return self.run_job(job_id)

    def cancel_job(self, job_id: str):
        job = self.acquisition_oper.mark_job_cancelled(job_id)
        return self._build_job_view(job)

    def confirm_candidate(self, job_id: str, candidate_id: str):
        candidate = self.acquisition_oper.confirm_candidate(job_id, candidate_id)
        return self._build_candidate_view(candidate)
```

- [ ] **Step 4: endpoint 语义收进 `api/endpoints/search.py`**

```python
@router.post("/jobs")
def create_job(payload: SearchJobCreateRequest, chain: MusicSearchChain = Depends(get_music_search_chain)):
    return chain.create_job(payload)
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/chain/search.py backend/app/api/endpoints/search.py backend/app/helper/query_builder.py backend/app/helper/search_scoring.py backend/app/db/acquisition_oper.py backend/tests/chain/test_search_chain.py backend/tests/api/test_search_endpoint.py
git commit -m "refactor: rebuild music search chain"
```

### Task 6: 重建 `MusicDownloadChain`

**Files:**
- Create: `backend/app/chain/download.py`
- Create: `backend/app/api/endpoints/download.py`
- Create: `backend/app/modules/host_download.py`
- Modify: `backend/app/db/orchestration_oper.py`
- Test: `backend/tests/chain/test_download_chain.py`
- Test: `backend/tests/api/test_download_endpoint.py`

- [ ] **Step 1: 写 dispatch 与 binding/task 测试**

```python
from unittest import TestCase

from app.chain.download import MusicDownloadChain


class MusicDownloadChainTest(TestCase):
    def test_dispatch_candidate_creates_binding(self) -> None:
        result = MusicDownloadChain().dispatch_candidate({"job_id": "job-1", "candidate_id": "candidate-1"})
        self.assertIsNotNone(result.binding_id)
        self.assertIsNotNone(result.download_task_id)
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.chain.test_download_chain tests.api.test_download_endpoint
```

Expected:

```text
ModuleNotFoundError: No module named 'app.chain.download'
```

- [ ] **Step 3: 实现下载链**

```python
class MusicDownloadChain(MusicChainBase):
    def dispatch_candidate(self, payload):
        candidate = self.acquisition_oper.get_candidate(payload["job_id"], payload["candidate_id"])
        dispatch_result = self.host_download_module.dispatch(candidate)
        binding = self.orchestration_oper.create_binding(candidate, dispatch_result)
        return self._build_dispatch_result(binding, dispatch_result)

    def list_bindings(self, filters=None):
        filters = filters or {}
        bindings = self.orchestration_oper.list_bindings(filters)
        return self._build_bindings_result(bindings)

    def get_binding(self, binding_id: str):
        binding = self.orchestration_oper.get_download_binding(binding_id)
        task = self.orchestration_oper.get_download_task_by_binding_id(binding_id)
        return self._build_binding_detail(binding, task)

    def retry_dispatch(self, binding_id: str):
        binding = self.orchestration_oper.get_download_binding(binding_id)
        return self.dispatch_candidate({"job_id": binding.job_id, "candidate_id": binding.candidate_id})
```

- [ ] **Step 4: 将下载工作台 endpoint 统一收进 `download.py`**

```python
@router.post("/dispatch")
def dispatch(payload: DispatchRequest, chain: MusicDownloadChain = Depends(get_music_download_chain)):
    return chain.dispatch_candidate(payload)
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/chain/download.py backend/app/api/endpoints/download.py backend/app/modules/host_download.py backend/app/db/orchestration_oper.py backend/tests/chain/test_download_chain.py backend/tests/api/test_download_endpoint.py
git commit -m "refactor: rebuild music download chain"
```

### Task 7: 重建 `MusicTransferChain`

**Files:**
- Create: `backend/app/chain/transfer.py`
- Create: `backend/app/api/endpoints/transfer.py`
- Create: `backend/app/helper/organize_layout.py`
- Create: `backend/app/modules/host_handoff.py`
- Modify: `backend/app/db/orchestration_oper.py`
- Modify: `backend/app/startup/transfer_runner.py`
- Test: `backend/tests/chain/test_transfer_chain.py`
- Test: `backend/tests/api/test_transfer_endpoint.py`

- [ ] **Step 1: 写下载后整理闭环测试**

```python
from unittest import TestCase

from app.chain.transfer import MusicTransferChain


class MusicTransferChainTest(TestCase):
    def test_process_advances_pending_binding_to_applied(self) -> None:
        result = MusicTransferChain().process()
        self.assertTrue(hasattr(result, "applied_record_ids"))

    def test_repair_source_path_rebuilds_failed_record(self) -> None:
        result = MusicTransferChain().repair_source_path("record-id", "/tmp/source.flac")
        self.assertEqual(result.record_id, "record-id")
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.chain.test_transfer_chain tests.api.test_transfer_endpoint
```

Expected:

```text
ModuleNotFoundError: No module named 'app.chain.transfer'
```

- [ ] **Step 3: 实现音乐版 `TransferChain`**

```python
class MusicTransferChain(MusicChainBase):
    def process(self):
        scanned = self._scan_pending_bindings()
        reconciled = self._reconcile_pending_records()
        return self._build_process_result(scanned, reconciled)

    def preview(self, payload):
        record = self.orchestration_oper.create_organize_preview(payload)
        return self._build_record_view(record)

    def apply(self, record_id: str):
        record = self.orchestration_oper.get_organize_record(record_id)
        applied = self.host_handoff_module.apply_transfer(record)
        return self._build_apply_result(applied)

    def rebuild_preview(self, record_id: str):
        record = self.orchestration_oper.get_organize_record(record_id)
        rebuilt = self.orchestration_oper.rebuild_organize_preview(record)
        return self._build_record_view(rebuilt)

    def repair_source_path(self, record_id: str, source_path: str):
        record = self.orchestration_oper.repair_organize_source(record_id, source_path)
        return self._build_record_view(record)
```

- [ ] **Step 4: 将 organize 主语义收进 `transfer.py`**

```python
@router.post("/preview")
def preview(payload: OrganizePreviewRequest, chain: MusicTransferChain = Depends(get_music_transfer_chain)):
    return chain.preview(payload)

@router.post("/apply")
def apply(payload: OrganizeApplyRequest, chain: MusicTransferChain = Depends(get_music_transfer_chain)):
    return chain.apply(payload.record_id)
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/chain/transfer.py backend/app/api/endpoints/transfer.py backend/app/helper/organize_layout.py backend/app/modules/host_handoff.py backend/app/startup/transfer_runner.py backend/tests/chain/test_transfer_chain.py backend/tests/api/test_transfer_endpoint.py
git commit -m "refactor: rebuild music transfer chain"
```

### Task 8: 重建 `MusicSubscribeChain`

**Files:**
- Create: `backend/app/chain/subscribe.py`
- Create: `backend/app/api/endpoints/subscribe.py`
- Create: `backend/app/startup/subscribe_runner.py`
- Modify: `backend/app/db/orchestration_oper.py`
- Test: `backend/tests/chain/test_subscribe_chain.py`
- Test: `backend/tests/api/test_subscribe_endpoint.py`

- [ ] **Step 1: 写订阅链测试**

```python
from unittest import TestCase

from app.chain.subscribe import MusicSubscribeChain


class MusicSubscribeChainTest(TestCase):
    def test_create_and_run_subscription(self) -> None:
        chain = MusicSubscribeChain()
        subscription = chain.create({"title": "Song", "entity_type": "track", "artist_names": ["Artist"]})
        run = chain.run(subscription.id)
        self.assertEqual(run.subscription_id, subscription.id)
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.chain.test_subscribe_chain tests.api.test_subscribe_endpoint
```

Expected:

```text
ModuleNotFoundError: No module named 'app.chain.subscribe'
```

- [ ] **Step 3: 实现订阅链**

```python
class MusicSubscribeChain(MusicChainBase):
    def create(self, payload):
        media = self.media_chain.resolve(payload)
        subscription = self.orchestration_oper.create_subscription(media, payload)
        return self._build_subscription_view(subscription)

    def update(self, subscription_id: str, payload):
        subscription = self.orchestration_oper.update_subscription(subscription_id, payload)
        return self._build_subscription_view(subscription)

    def archive(self, subscription_id: str):
        subscription = self.orchestration_oper.archive_subscription(subscription_id)
        return self._build_subscription_view(subscription)

    def run(self, subscription_id: str, preview_only: bool = False):
        subscription = self.orchestration_oper.get_subscription(subscription_id)
        run = self.orchestration_oper.create_subscription_run(subscription, preview_only=preview_only)
        execution = self.search_chain.run_subscription(subscription, run, preview_only=preview_only)
        return self._build_run_view(execution)

    def run_scheduled(self):
        due_subscriptions = self.orchestration_oper.list_due_subscriptions()
        return [self.run(subscription.id) for subscription in due_subscriptions]
```

- [ ] **Step 4: 调度注册改为直接调 `MusicSubscribeChain`**

```python
# backend/app/startup/subscribe_runner.py
def run_subscribe_scheduler() -> None:
    MusicSubscribeChain().run_scheduled()
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/chain/subscribe.py backend/app/api/endpoints/subscribe.py backend/app/startup/subscribe_runner.py backend/tests/chain/test_subscribe_chain.py backend/tests/api/test_subscribe_endpoint.py
git commit -m "refactor: rebuild music subscribe chain"
```

### Task 9: 重建 `MusicDashboardChain` 与启动装配

**Files:**
- Create: `backend/app/chain/dashboard.py`
- Create: `backend/app/api/endpoints/dashboard.py`
- Create: `backend/app/startup/__init__.py`
- Create: `backend/app/startup/runtime.py`
- Modify: `backend/app/__init__.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/api/endpoints/settings.py`
- Modify: `backend/app/api/endpoints/probe.py`
- Test: `backend/tests/chain/test_dashboard_chain.py`
- Test: `backend/tests/api/test_dashboard_endpoint.py`
- Test: `backend/tests/api/test_startup_runtime.py`

- [ ] **Step 1: 写 dashboard 与 startup 测试**

```python
from unittest import TestCase

from app.chain.dashboard import MusicDashboardChain


class MusicDashboardChainTest(TestCase):
    def test_summary_aggregates_chart_search_download_transfer_subscription(self) -> None:
        result = MusicDashboardChain().summary()
        self.assertTrue(hasattr(result, "charts"))
        self.assertTrue(hasattr(result, "downloads"))
```

- [ ] **Step 2: 运行失败测试**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.chain.test_dashboard_chain tests.api.test_dashboard_endpoint tests.api.test_startup_runtime
```

Expected:

```text
ModuleNotFoundError: No module named 'app.chain.dashboard'
```

- [ ] **Step 3: 实现 dashboard chain 与 startup 入口**

```python
class MusicDashboardChain(MusicChainBase):
    def summary(self):
        return DashboardSummary.model_validate(
            {
                "charts": self.chart_chain.runtime_summary(),
                "search": self.search_chain.runtime_summary(),
                "downloads": self.download_chain.runtime_summary(),
                "transfer": self.transfer_chain.runtime_summary(),
                "subscriptions": self.subscribe_chain.runtime_summary(),
            }
        )
```

```python
# backend/app/startup/runtime.py
def register_host_services():
    return [
        ("music-subscription-scheduler", run_subscribe_scheduler),
        ("music-chart-refresh", run_chart_refresh),
        ("music-transfer", run_transfer_loop),
    ]
```

- [ ] **Step 4: `__init__.py` 和 `main.py` 只接 `startup/`**

```python
# backend/app/main.py
from app.startup.runtime import bootstrap_backend_runtime

app = bootstrap_backend_runtime()
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/chain/dashboard.py backend/app/api/endpoints/dashboard.py backend/app/startup backend/app/__init__.py backend/app/main.py backend/tests/chain/test_dashboard_chain.py backend/tests/api/test_dashboard_endpoint.py backend/tests/api/test_startup_runtime.py
git commit -m "refactor: rebuild dashboard chain and startup entry"
```

### Task 10: `plugin_runtime` 同构镜像与旧目录删除

**Files:**
- Modify: `plugin_runtime/plugins/musicpilot/**`
- Delete: `backend/app/api/routes/`
- Delete: `backend/app/services/`
- Delete: `backend/app/models/`
- Delete: `backend/app/repositories/`
- Delete: `backend/app/adapters/`
- Delete: `backend/app/tasks/`
- Delete: `plugin_runtime/plugins/musicpilot/api/routes/`
- Delete: `plugin_runtime/plugins/musicpilot/services/`
- Delete: `plugin_runtime/plugins/musicpilot/models/`
- Delete: `plugin_runtime/plugins/musicpilot/repositories/`
- Delete: `plugin_runtime/plugins/musicpilot/adapters/`
- Delete: `plugin_runtime/plugins/musicpilot/tasks/`
- Test: `backend/tests/api/test_runtime_mirror_layout.py`

- [ ] **Step 1: 写结构同构测试**

```python
from pathlib import Path
from unittest import TestCase


class RuntimeMirrorLayoutTest(TestCase):
    def test_runtime_mirror_matches_backend_layout(self) -> None:
        backend_dirs = {"api/endpoints", "chain", "db/models", "helper", "modules", "startup", "utils"}
        runtime_root = Path("plugin_runtime/plugins/musicpilot")
        for rel in backend_dirs:
            self.assertTrue((runtime_root / rel).exists(), rel)
```

- [ ] **Step 2: 运行测试，确认当前镜像未对齐**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest tests.api.test_runtime_mirror_layout
```

Expected:

```text
FAIL: test_runtime_mirror_matches_backend_layout
```

- [ ] **Step 3: 同步镜像并物理删除旧目录**

```bash
rm -rf backend/app/api/routes backend/app/services backend/app/models backend/app/repositories backend/app/adapters backend/app/tasks
rm -rf plugin_runtime/plugins/musicpilot/api/routes plugin_runtime/plugins/musicpilot/services plugin_runtime/plugins/musicpilot/models plugin_runtime/plugins/musicpilot/repositories plugin_runtime/plugins/musicpilot/adapters plugin_runtime/plugins/musicpilot/tasks
```

- [ ] **Step 4: 验证活跃代码已无旧目录 import**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot && rg -n "api\\.routes|app\\.services|app\\.repositories|app\\.adapters|app\\.models|app\\.tasks" backend plugin_runtime/plugins/musicpilot
```

Expected:

```text
0 matches
```

- [ ] **Step 5: Commit**

```bash
git add backend plugin_runtime/plugins/musicpilot
git commit -m "refactor: remove legacy backend directories"
```

### Task 11: 测试、文档与最终验收

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `docs/architecture/2026-04-13_后端MoviePilot同构重构设计.md`
- Modify: `docs/architecture/2026-04-13_MoviePilot后端结构对齐分析.md`
- Modify: `scripts/package_plugin.py` if needed
- Test: `backend/tests/**`

- [ ] **Step 1: 写最终结构与入口验收测试**

```python
from pathlib import Path
from unittest import TestCase


class BackendRefactorAcceptanceTest(TestCase):
    def test_legacy_directories_removed(self) -> None:
        legacy = [
            "backend/app/api/routes",
            "backend/app/services",
            "backend/app/models",
            "backend/app/repositories",
            "backend/app/adapters",
            "backend/app/tasks",
        ]
        for path in legacy:
            self.assertFalse(Path(path).exists(), path)
```

- [ ] **Step 2: 运行全量后端测试**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend && .venv/bin/python -m unittest discover -s tests
```

Expected:

```text
OK
```

- [ ] **Step 3: 运行打包验证**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot && python3 scripts/package_plugin.py
```

Expected:

```text
package complete
```

- [ ] **Step 4: 更新 README 与架构文档到新结构真相**

```markdown
- 后端主结构已切换为 `api/endpoints + chain + db + helper + modules + startup + utils`
- 旧 `routes/services/models/repositories/adapters/tasks` 已删除
- plugin runtime 后端镜像已与主仓同构
```

- [ ] **Step 5: Commit**

```bash
git add README.md backend/README.md docs/architecture/2026-04-13_后端MoviePilot同构重构设计.md docs/architecture/2026-04-13_MoviePilot后端结构对齐分析.md backend/tests
git commit -m "docs: finalize moviepilot-aligned backend refactor"
```

## 自检

### Spec coverage

- 目录同构：Task 1、Task 2、Task 9、Task 10
- 7 条主链：Task 3 到 Task 9
- 旧目录物理删除：Task 10、Task 11
- runtime mirror 同构：Task 10
- API / 调度只调 chain：Task 1、Task 3 到 Task 9
- 文档真相同步：Task 11

### Placeholder scan

- 无 `TODO/TBD/implement later`
- 每个任务都给了目标文件、测试文件、命令和关键代码骨架
- 无“类似 Task N”引用

### Type consistency

- 统一链名称固定为：
  - `MusicMediaChain`
  - `MusicSearchChain`
  - `MusicDownloadChain`
  - `MusicTransferChain`
  - `MusicSubscribeChain`
  - `MusicChartChain`
  - `MusicDashboardChain`
- 统一目标目录固定为：
  - `api/endpoints`
  - `chain`
  - `db/models`
  - `db/*_oper.py`
  - `helper`
  - `modules`
  - `startup`
  - `utils`

## 执行说明

计划完成并保存到：

- [docs/45_后端MoviePilot同构重构实施计划.md](/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/45_%E5%90%8E%E7%AB%AFMoviePilot%E5%90%8C%E6%9E%84%E9%87%8D%E6%9E%84%E5%AE%9E%E6%96%BD%E8%AE%A1%E5%88%92.md)

当前默认执行方式：

1. 直接按本计划推进
2. 每完成一条主链就做最小验证
3. 不回退到旧目录或旧主流程入口
