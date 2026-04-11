# RSS Family Hints Quality Implementation Plan

**Goal:** Improve RSS discovery family lookup quality by adding family-specific candidate hints and letting metadata lookup consume them without changing the external API.

**Architecture:** Keep the existing `rss_feed -> discovery -> search_lookup -> metadata` flow intact. Add candidate hint enrichment in the RSS parser, preserve the discovery bridge contract, and extend metadata lookup to consume optional candidate arrays deterministically.

**Tech Stack:** FastAPI, unittest, existing RSS parser / discovery assembler / metadata service.

---

### Task 1: Add failing tests for family-specific hint enrichment

**Files:**
- Modify: `backend/tests/test_rss_feed_parser.py`
- Modify: `backend/tests/test_discovery_service.py`
- Modify: `backend/tests/test_metadata_provider.py`

- [ ] Add failing parser tests for family-specific candidate hints.
- [ ] Add failing discovery tests asserting RSS `resolution_hints` include the new candidate arrays.
- [ ] Add failing metadata lookup tests showing candidate arrays improve lookup attempts.
- [ ] Run targeted tests and verify they fail for the expected reason.

### Task 2: Implement parser and discovery hint enrichment

**Files:**
- Modify: `backend/app/adapters/rss_feed_parser.py`
- Modify: `backend/app/services/discovery.py`
- Modify: `plugin_runtime/plugins/musicpilot/adapters/rss_feed_parser.py`
- Modify: `plugin_runtime/plugins/musicpilot/services/discovery.py`

- [ ] Add family-specific candidate hint extraction in RSS parser output.
- [ ] Pass candidate hints through the discovery bridge into `resolution_hints`.
- [ ] Keep readiness rules and existing scalar hints unchanged.
- [ ] Re-run targeted parser/discovery tests until green.

### Task 3: Extend metadata lookup to consume candidate arrays

**Files:**
- Modify: `backend/app/services/metadata.py`
- Modify: `plugin_runtime/plugins/musicpilot/services/metadata.py`
- Modify: `backend/tests/test_metadata_provider.py`

- [ ] Extend lookup keyword building to consume optional candidate arrays in deterministic order.
- [ ] Preserve current strict winner selection and response semantics.
- [ ] Re-run targeted metadata tests until green.

### Task 4: Runtime verification and docs

**Files:**
- Modify: `README.md`
- Modify: `backend/README.md`
- Add: `docs/38_RSS_family_hints_运行态验证.md`

- [ ] Document the new RSS family hint enrichment behavior.
- [ ] Run backend full tests.
- [ ] Run frontend build.
- [ ] Run packaging.
- [ ] Do one real runtime RSS discovery verification and record results.
