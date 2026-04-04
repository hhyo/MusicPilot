# Music Organize Preview Localization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace host `transfer/name`-based organize preview with a MusicPilot-local music path preview while keeping `apply`, plugin API paths, and organize record semantics unchanged.

**Architecture:** Keep the existing `OrganizeService.preview()` and `OrganizeStrategyService.build_plan(...)` flow, but change `RealOrganizeAdapter.preview()` so it no longer calls the host HTTP API. Preview will become a local plan projection that only requires existing organize input and metadata context; execution checks remain in `apply`.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, unittest, MoviePilot plugin runtime mirror

---

### Task 1: Lock Preview Localization Behavior with Tests

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py`

- [ ] **Step 1: Write the failing unit test for local preview success**

Add a test near the existing `RealOrganizeAdapter` tests that asserts `preview()` succeeds without calling the host HTTP client when organize input exists:

```python
def test_real_organize_preview_uses_local_music_plan_without_host_transfer_name(self) -> None:
    client = FakeHostClient(
        get_responses={
            "/api/v1/transfer/name": AssertionError("preview should not call host transfer/name")
        }
    )
    adapter = RealOrganizeAdapter(
        settings=build_settings(),
        client=client,  # type: ignore[arg-type]
        storage_runtime=FakeStorageRuntime(),
    )

    candidate = build_candidate(
        raw_payload={
            "host_transfer_source_path": "/downloads/Adele - Hello.flac",
            "host_transfer_filetype": "file",
        },
        format_tag="flac",
    )

    result = adapter.preview(
        candidate=candidate,
        metadata_detail=build_track_detail(),
        binding_id=None,
        plan=build_plan(),
    )

    self.assertEqual(result.organize_status, OrganizeStatus.PREVIEW_READY)
    self.assertTrue(result.organizeable)
    self.assertEqual(result.integration_point, "RealOrganizeAdapter.preview.music_local_plan_preview")
    self.assertEqual(client.calls, [])
```

- [ ] **Step 2: Write the failing unit test for missing source path**

Add a companion test proving preview still fails when there is no organize input:

```python
def test_real_organize_preview_fails_without_source_path(self) -> None:
    adapter = RealOrganizeAdapter(
        settings=build_settings(),
        client=FakeHostClient(),  # type: ignore[arg-type]
        storage_runtime=FakeStorageRuntime(),
    )
    candidate = build_candidate(raw_payload={})

    with self.assertRaises(HostTransportError) as ctx:
        adapter.preview(
            candidate=candidate,
            metadata_detail=build_track_detail(),
            binding_id=None,
            plan=build_plan(),
        )

    self.assertEqual(ctx.exception.reason_code, "moviepilot_transfer_source_path_missing")
```

- [ ] **Step 3: Write the integration test for service-level preview result**

Add a service-level test in `test_organize_integration.py` that seeds a candidate with a music `metadata_snapshot`, calls the preview flow through the resolver/service, and asserts the preview record stores local-plan semantics instead of host `transfer/name` failure.

```python
def test_organize_service_preview_uses_local_music_plan_for_real_host_preview(self) -> None:
    # seed SearchJobModel.metadata_snapshot with build_track_detail().model_dump(mode="json")
    # seed SearchCandidateModel.raw_payload with host_transfer_source_path/filetype
    # use real host adapter with FakeHostClient that would fail if called
    # assert preview result is preview_ready and integration_point matches local preview
```

- [ ] **Step 4: Run tests to verify they fail for the right reason**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- At least one preview-localization test fails
- Failure should show current code still calling `/api/v1/transfer/name` or returning `failed`

- [ ] **Step 5: Commit red-state checkpoint**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py
git commit -m "test: lock local music preview behavior"
```

### Task 2: Implement Local Music Preview in the Adapter

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py`

- [ ] **Step 1: Replace host transfer/name preview path with a local preview result**

In `RealOrganizeAdapter._preview_once(...)`, remove the `self.client.get_json(...)` call and replace it with a local result builder that only checks `source = self._resolve_source(candidate)`.

Use this shape:

```python
def _preview_once(...):
    source = self._resolve_source(candidate)
    if not source:
        raise HostTransportError(
            "Music organize preview requires a downloaded local file path, but the current candidate/binding does not expose one.",
            reason_code="moviepilot_transfer_source_path_missing",
        )

    return OrganizeAdapterResult(
        organizeable=True,
        organize_backend=AdapterMode.HOST,
        adapter_mode=AdapterMode.HOST,
        strategy=plan.strategy,
        strategy_snapshot=plan.strategy_snapshot,
        organize_status=OrganizeStatus.PREVIEW_READY,
        target_library_path=plan.target_library_path,
        target_relative_path=plan.target_relative_path,
        strategy_note=plan.strategy_note,
        integration_point="RealOrganizeAdapter.preview.music_local_plan_preview",
        capability_source="musicpilot.runtime.local_plan_preview",
        verification_state=VerificationState.VERIFIED,
        mock=False,
        note=(
            "当前 organize preview 使用 MusicPilot 本地音乐路径规划预览。"
            "它不再复用 MoviePilot `/api/v1/transfer/name`，也不做宿主可执行预检。"
        ),
        path_handoff=_extract_candidate_path_handoff(candidate),
        adapter_resolution=AdapterResolution(
            adapter_key="real_organize",
            adapter_mode=AdapterMode.HOST,
            selection_mode=AdapterSelectionMode(self.settings.host_organize_mode),
            capability_source="musicpilot.runtime.local_plan_preview",
            verification_state=VerificationState.VERIFIED,
            integration_point="RealOrganizeAdapter.preview.music_local_plan_preview",
            host_integration_enabled=self.settings.host_integration_enabled,
        ),
    )
```

- [ ] **Step 2: Remove preview-only HTTP response parsing that is no longer used**

Delete or stop using preview-only helpers that only existed for `/api/v1/transfer/name`, such as:

```python
self._extract_preview_name(...)
self._merge_preview_name(...)
```

Only remove the pieces that become dead after preview localization. Do not touch apply helpers.

- [ ] **Step 3: Run targeted tests to verify green**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests -p 'test_moviepilot_semantics.py'
.venv/bin/python -m unittest discover -s tests -p 'test_organize_integration.py'
```

Expected:
- Preview localization tests pass
- Existing apply tests still pass

- [ ] **Step 4: Commit adapter implementation**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/adapters/organize.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_moviepilot_semantics.py /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/tests/test_organize_integration.py
git commit -m "feat: localize music organize preview"
```

### Task 3: Update API Text, Runtime Mirror, and Real Host Verification

**Files:**
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/api/routes/organize.py`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/26_真实音乐样本_preview_apply_验证.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md`
- Modify: `/Users/lihuanhuan/PycharmProjects/MusicPilot/docs/25_真实插件加载验证.md`
- Modify via packaging: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/organize.py`
- Modify via packaging: `/Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/api/routes/organize.py`

- [ ] **Step 1: Update API response note for preview**

Change the `/organize/preview` note so it no longer references MoviePilot `/transfer/name`.

Target text:

```python
note="当前 organize preview 使用 MusicPilot 本地音乐路径规划预览。它依赖明确的 source_path，不会自动切换到其他业务语义。"
```

- [ ] **Step 2: Update docs to reflect the new truth**

Update:
- `docs/26_真实音乐样本_preview_apply_验证.md` so the real music sample closure becomes `preview_ready + applied`
- `docs/23_音乐文件整理技术设计与实现方案.md` to state preview localization is now implemented
- `docs/25_真实插件加载验证.md` only if it mentions preview still being host `transfer/name`

- [ ] **Step 3: Repackage runtime mirror**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot
python3 scripts/package_plugin.py
```

Expected:
- `plugin_runtime/plugins/musicpilot` reflects the new local-preview implementation

- [ ] **Step 4: Run full verification**

Run:

```bash
cd /Users/lihuanhuan/PycharmProjects/MusicPilot/backend
.venv/bin/python -m unittest discover -s tests

cd /Users/lihuanhuan/PycharmProjects/MusicPilot/frontend
PATH=/Users/lihuanhuan/.npm-global/bin:$PATH pnpm build
```

Then run the real host plugin API check under MoviePilot `config-dev`:

```bash
cd /Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot
CONFIG_DIR=/Users/lihuanhuan/PycharmProjects/MoviePilotPkg/MoviePilot/config-dev ./.venv/bin/python - <<'PY'
# seed SearchJob/SearchCandidate with music metadata_snapshot
# call POST /api/v1/plugin/musicpilot/organize/preview
# call POST /api/v1/plugin/musicpilot/organize/apply
# assert preview_ready then applied
PY
```

Expected:
- `preview` returns `preview_ready`
- `apply` returns `applied`
- target file exists
- record detail remains queryable

- [ ] **Step 5: Commit verification and docs**

```bash
git add /Users/lihuanhuan/PycharmProjects/MusicPilot/backend/app/api/routes/organize.py /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/23_音乐文件整理技术设计与实现方案.md /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/25_真实插件加载验证.md /Users/lihuanhuan/PycharmProjects/MusicPilot/docs/26_真实音乐样本_preview_apply_验证.md /Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/adapters/organize.py /Users/lihuanhuan/PycharmProjects/MusicPilot/plugin_runtime/plugins/musicpilot/api/routes/organize.py
git commit -m "docs: record local music preview closure"
```

