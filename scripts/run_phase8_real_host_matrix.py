#!/usr/bin/env python3
"""Manually run the Phase 8 real-host validation matrix and export a JSON report."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.adapters.download_dispatch import RealDownloadDispatchAdapter
from app.adapters.host_http import HostHttpClient, HostHttpClientConfig
from app.adapters.organize import RealOrganizeAdapter
from app.core.config import Settings
from app.schemas.acquisition import PathHandoffInfo, SearchCandidateDetail
from app.schemas.integration import VerificationState
from app.schemas.orchestration import (
    OrganizeConflictPolicy,
    OrganizePlan,
    OrganizeStrategySnapshot,
)
from app.schemas.validation import (
    HostValidationMatrixEntry,
    HostValidationMatrixReport,
    HostValidationMatrixSummary,
)
from app.services.host_path_handoff import HostPathHandoffService


@dataclass(slots=True)
class ValidationSample:
    sample_id: str
    sample_name: str
    search_input_type: str
    search_query: str
    dispatch_endpoint_type: str
    tmdbid: int | None = None
    candidate_index: int = 0


DEFAULT_SAMPLES = [
    ValidationSample(
        sample_id="ordinary_accident_media",
        sample_name="普通事故 media/download 闭环",
        search_input_type="search/media",
        search_query="tmdb:1456349",
        dispatch_endpoint_type="download_media",
        tmdbid=1456349,
    ),
    ValidationSample(
        sample_id="snow_white_media",
        sample_name="白雪公主 media/download 闭环",
        search_input_type="search/media",
        search_query="tmdb:447273",
        dispatch_endpoint_type="download_media",
        tmdbid=447273,
    ),
    ValidationSample(
        sample_id="argentina_1985_media",
        sample_name="阿根廷1985 media/download 闭环",
        search_input_type="search/media",
        search_query="tmdb:714888",
        dispatch_endpoint_type="download_media",
        tmdbid=714888,
    ),
    ValidationSample(
        sample_id="ordinary_accident_title_add",
        sample_name="普通事故 title/download_add 闭环",
        search_input_type="search/title",
        search_query="普通事故 2025",
        dispatch_endpoint_type="download_add",
        tmdbid=1456349,
    ),
    ValidationSample(
        sample_id="snow_white_title_add",
        sample_name="白雪公主 title/download_add 闭环",
        search_input_type="search/title",
        search_query="白雪公主 2025",
        dispatch_endpoint_type="download_add",
        tmdbid=447273,
    ),
    ValidationSample(
        sample_id="argentina_1985_title_add",
        sample_name="阿根廷1985 title/download_add 闭环",
        search_input_type="search/title",
        search_query="阿根廷1985 2022",
        dispatch_endpoint_type="download_add",
        tmdbid=714888,
    ),
]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def load_token(token_file: Path) -> str:
    env_token = os.getenv("MUSICPILOT_REAL_HOST_API_TOKEN") or os.getenv("MUSICPILOT_HOST_AUTH_TOKEN")
    if env_token:
        return env_token

    for line in token_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip().replace("export ", "").strip() == "TOKEN":
            return value.strip().strip('"')

    raise RuntimeError(f"Could not locate TOKEN inside {token_file}.")


def build_settings(args: argparse.Namespace, token: str) -> Settings:
    return Settings(
        host_integration_enabled=True,
        host_base_url=args.host_base_url,
        host_auth_token=token,
        host_auth_mode="x_api_key",
        host_api_key_header_name="X-API-KEY",
        host_search_mode="prefer_host",
        host_dispatch_mode="prefer_host",
        host_organize_mode="prefer_host",
        host_verification_state="verified",
        host_history_sync_retry_attempts=args.handoff_attempts,
        host_history_sync_retry_interval_seconds=args.handoff_interval,
        host_validation_matrix_path=str(args.output),
        organize_root_path=args.organize_root_path,
    )


def build_http_client(settings: Settings) -> HostHttpClient:
    return HostHttpClient(
        HostHttpClientConfig(
            base_url=settings.host_base_url,
            timeout_seconds=45.0,
            verify_tls=settings.host_verify_tls,
            auth_token=settings.host_auth_token,
            auth_mode=settings.host_auth_mode,
            api_key_header_name=settings.host_api_key_header_name,
        )
    )


def slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-") or "sample"


def to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_candidate(sample: ValidationSample, context: dict[str, Any]) -> SearchCandidateDetail:
    torrent = context.get("torrent_info") if isinstance(context.get("torrent_info"), dict) else {}
    host_context = dict(context)
    if sample.dispatch_endpoint_type == "download_add":
        host_context["media_info"] = {}

    title = str(torrent.get("title") or f"{sample.sample_name} candidate")
    raw_payload = {
        "host_context": host_context,
        "host_media_reference": {"tmdbid": sample.tmdbid} if sample.tmdbid else {},
        "sample_id": sample.sample_id,
        "sample_name": sample.sample_name,
        "search_input_type": sample.search_input_type,
    }
    return SearchCandidateDetail(
        id=f"phase8-{sample.sample_id}",
        job_id=f"phase8-job-{sample.sample_id}",
        site_id=str(torrent.get("site") or torrent.get("site_id") or "0"),
        site_name=str(torrent.get("site_name") or "MoviePilot Site"),
        title=title,
        normalized_title=" ".join(title.lower().replace("-", " ").split()),
        size_bytes=to_int(torrent.get("size"), 0),
        seeders=to_int(torrent.get("seeders"), 0),
        peers=to_int(torrent.get("peers") or torrent.get("leechers"), 0),
        format_tag=None,
        bitrate_kbps=None,
        source_tags=[str(label) for label in (torrent.get("labels") or []) if label],
        raw_score=100.0,
        score_total=100.0,
        score_breakdown={},
        decision="auto_download",
        reason_codes=["phase8_real_host_validation"],
        dispatchable=True,
        dispatch_status="pending",
        mock=False,
        note=f"Phase 8 real-host validation sample: {sample.sample_name}",
        created_at=now_utc(),
        raw_payload=raw_payload,
    )


def merge_handoff_payload(candidate: SearchCandidateDetail, handoff: PathHandoffInfo | None) -> SearchCandidateDetail:
    if handoff is None:
        return candidate
    payload = dict(candidate.raw_payload or {})
    serialized = handoff.model_dump(mode="json")
    payload["path_handoff"] = serialized
    if handoff.source_path:
        payload["host_transfer_source_path"] = handoff.source_path
        payload["host_transfer_filetype"] = handoff.source_filetype or "file"
        payload["host_transfer_source"] = {
            "storage": "local",
            "path": handoff.source_path,
            "type": handoff.source_filetype or "file",
            "name": handoff.source_name,
            "basename": handoff.source_basename,
            "extension": handoff.source_extension,
        }
    return candidate.model_copy(update={"path_handoff": handoff, "raw_payload": payload})


def build_plan(sample: ValidationSample, args: argparse.Namespace, candidate: SearchCandidateDetail) -> OrganizePlan:
    folder = slugify(sample.sample_id)
    target_root = f"{args.organize_root_path.rstrip('/')}/phase8-validation/{folder}"
    source_name = (
        candidate.path_handoff.source_name
        if candidate.path_handoff and candidate.path_handoff.source_name
        else candidate.title
    )
    relative_name = source_name or f"{folder}.mkv"
    return OrganizePlan(
        strategy="phase8_real_host_validation",
        strategy_snapshot=OrganizeStrategySnapshot(
            strategy_name="phase8_real_host_validation",
            library_type="music",
            root_path=args.organize_root_path,
            artist_dir_template="{artist_name}",
            album_dir_template="{artist_name}/{year} - {album_title}",
            track_file_template="{track_title}.{format_ext}",
            conflict_policy=OrganizeConflictPolicy.SKIP_EXISTING,
            template_note="Phase 8 uses a dedicated validation folder to minimize side effects while exercising host transfer semantics.",
        ),
        target_library_path=target_root,
        target_relative_path=f"phase8-validation/{folder}/{relative_name}",
        strategy_note="Phase 8 dedicated validation folder under host media root.",
    )


def fetch_search_context(
    client: HostHttpClient,
    settings: Settings,
    sample: ValidationSample,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if sample.search_input_type == "search/media":
        payload = client.get_json(
            f"{(settings.host_search_media_path or '/api/v1/search/media').rstrip('/')}/{sample.search_query}",
            params={"area": "title"},
            auth_mode="x_api_key",
        )
        endpoint_type = "search_media"
    else:
        payload = client.get_json(
            settings.host_search_title_path,
            params={"keyword": sample.search_query, "page": 0},
            auth_mode="x_api_key",
        )
        endpoint_type = "search_title"

    items = payload.get("data") if isinstance(payload.get("data"), list) else payload.get("items")
    if not isinstance(items, list) or not items:
        raise RuntimeError(f"{endpoint_type} returned no candidates")

    index = min(sample.candidate_index, len(items) - 1)
    item = items[index]
    if not isinstance(item, dict):
        raise RuntimeError(f"{endpoint_type} returned unsupported candidate payload")
    return item, {
        "endpoint_type": endpoint_type,
        "candidate_count": len(items),
        "message": payload.get("message"),
    }


def build_transfer_history_fallback_sample(
    client: HostHttpClient,
    settings: Settings,
    handoff_service: HostPathHandoffService,
) -> HostValidationMatrixEntry | None:
    download_hashes: set[str] = set()
    for page in range(1, settings.host_history_download_max_pages + 1):
        download_payload = client.get_json(
            settings.host_history_download_path,
            params={"page": page, "count": settings.host_history_download_page_size},
            auth_mode="x_api_key",
        )
        download_items = (
            download_payload.get("items")
            if isinstance(download_payload.get("items"), list)
            else download_payload
        )
        if not isinstance(download_items, list):
            break
        for item in download_items:
            if isinstance(item, dict) and item.get("download_hash"):
                download_hashes.add(str(item.get("download_hash")))
        if len(download_items) < settings.host_history_download_page_size:
            break

    transfer_items: list[dict[str, Any]] = []
    for page in range(1, settings.host_history_transfer_max_pages + 1):
        transfer_payload = client.get_json(
            settings.host_history_transfer_path,
            params={"page": page, "count": settings.host_history_transfer_page_size},
            auth_mode="x_api_key",
        )
        data = transfer_payload.get("data") if isinstance(transfer_payload.get("data"), dict) else {}
        items = data.get("list") if isinstance(data.get("list"), list) else []
        transfer_items.extend([item for item in items if isinstance(item, dict)])
        if len(items) < settings.host_history_transfer_page_size:
            break

    for item in transfer_items:
        if not isinstance(item, dict):
            continue
        download_hash = str(item.get("download_hash") or "")
        if not download_hash or download_hash in download_hashes or not item.get("src") or item.get("status") is False:
            continue
        handoff = handoff_service.resolve(download_hash)
        if handoff is None:
            continue
        return HostValidationMatrixEntry(
            sample_id="transfer_history_fallback",
            sample_name="history/transfer fallback handoff",
            search_input_type="history/transfer",
            dispatch_endpoint_type=None,
            path_handoff_source=handoff.handoff_source,
            path_handoff_status=handoff.handoff_status,
            transfer_name_result=None,
            transfer_manual_result=None,
            organize_result=None,
            verification_state=VerificationState.VERIFIED,
            stability_state="stable",
            attempt_count=1,
            success_count=1,
            blocker=None,
            note="history/download 未命中时，真实 MoviePilot history/transfer 仍可回灌 source path。",
            last_verified_at=now_utc(),
            raw_summary={
                "download_hash": download_hash,
                "title": item.get("title"),
                "src": item.get("src"),
                "dest": item.get("dest"),
            },
        )
    return None


def build_transfer_replay_entries(
    client: HostHttpClient,
    settings: Settings,
    handoff_service: HostPathHandoffService,
    organize_adapter: RealOrganizeAdapter,
    args: argparse.Namespace,
    *,
    limit: int = 2,
) -> list[HostValidationMatrixEntry]:
    payload = client.get_json(
        settings.host_history_transfer_path,
        params={"page": 1, "count": max(10, limit * 3)},
        auth_mode="x_api_key",
    )
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    items = data.get("list") if isinstance(data.get("list"), list) else []
    entries: list[HostValidationMatrixEntry] = []

    for item in items:
        if len(entries) >= limit:
            break
        if not isinstance(item, dict) or item.get("status") is False or not item.get("src"):
            continue
        download_hash = str(item.get("download_hash") or "")
        handoff = handoff_service.resolve_from_transfer(download_hash)
        if handoff is None:
            continue
        candidate = SearchCandidateDetail(
            id=f"phase8-transfer-replay-{len(entries)+1}",
            job_id="phase8-transfer-replay",
            site_id="moviepilot-transfer-history",
            site_name="MoviePilot Transfer History",
            title=str(item.get("title") or handoff.source_name or "transfer-history"),
            normalized_title=str(item.get("title") or handoff.source_name or "transfer-history").lower(),
            size_bytes=0,
            seeders=0,
            peers=0,
            format_tag=handoff.source_extension.lstrip(".") if handoff.source_extension else None,
            bitrate_kbps=None,
            source_tags=["history", "transfer", "phase8"],
            raw_score=100.0,
            score_total=100.0,
            score_breakdown={},
            decision="manual_confirm",
            reason_codes=["phase8_transfer_replay"],
            dispatchable=False,
            dispatch_status="history_replay",
            mock=False,
            note="Phase 8 replay from real MoviePilot transfer history.",
            created_at=now_utc(),
            path_handoff=handoff,
            raw_payload={
                "path_handoff": handoff.model_dump(mode="json"),
                "host_transfer_source_path": handoff.source_path,
                "host_transfer_filetype": handoff.source_filetype,
                "host_transfer_source": {
                    "storage": "local",
                    "path": handoff.source_path,
                    "type": handoff.source_filetype,
                    "name": handoff.source_name,
                    "basename": handoff.source_basename,
                    "extension": handoff.source_extension,
                },
            },
        )
        sample = ValidationSample(
            sample_id=f"transfer_replay_{len(entries)+1}",
            sample_name=f"transfer replay {item.get('title') or len(entries)+1}",
            search_input_type="history/transfer-replay",
            search_query=download_hash,
            dispatch_endpoint_type="history_replay",
        )
        plan = build_plan(sample, args, candidate)
        try:
            preview = organize_adapter.preview(
                candidate=candidate,
                metadata_detail=None,
                binding_id=None,
                plan=plan,
            )
            apply = organize_adapter.apply(
                organize_job_id=f"phase8-transfer-replay-{len(entries)+1}",
                candidate=candidate,
                metadata_detail=None,
                binding_id=None,
                plan=plan,
            )
            verification_state = (
                VerificationState.VERIFIED if apply.organize_status.value == "applied" else VerificationState.UNVERIFIED
            )
            blocker = apply.failure_reason if verification_state != VerificationState.VERIFIED else None
        except Exception as exc:  # noqa: BLE001
            preview = None
            apply = None
            verification_state = VerificationState.UNVERIFIED
            blocker = str(exc)

        entries.append(
            HostValidationMatrixEntry(
                sample_id=sample.sample_id,
                sample_name=sample.sample_name,
                search_input_type=sample.search_input_type,
                dispatch_endpoint_type=None,
                path_handoff_source=handoff.handoff_source,
                path_handoff_status=handoff.handoff_status,
                transfer_name_result=preview.organize_status.value if preview else None,
                transfer_manual_result=apply.organize_status.value if apply else None,
                organize_result=apply.organize_status.value if apply else None,
                verification_state=verification_state,
                stability_state="single_sample",
                attempt_count=1,
                success_count=1 if verification_state == VerificationState.VERIFIED else 0,
                blocker=blocker,
                note="Phase 8 replayed a real transfer history source path through MoviePilot transfer/name + transfer/manual.",
                last_verified_at=now_utc(),
                raw_summary={
                    "download_hash": download_hash,
                    "src": item.get("src"),
                    "dest": item.get("dest"),
                    "preview": preview.model_dump(mode="json") if preview else None,
                    "apply": apply.model_dump(mode="json") if apply else None,
                },
            )
        )

    return entries


def summarize(entries: list[HostValidationMatrixEntry]) -> HostValidationMatrixSummary:
    counts = Counter(entry.stability_state for entry in entries)
    verification = Counter(entry.verification_state for entry in entries)
    return HostValidationMatrixSummary(
        generated_at=now_utc(),
        sample_count=len(entries),
        stable_count=counts.get("stable", 0),
        single_sample_count=counts.get("single_sample", 0),
        blocked_count=counts.get("blocked", 0),
        flaky_count=counts.get("flaky", 0),
        verified_count=verification.get(VerificationState.VERIFIED, 0),
        unverified_count=verification.get(VerificationState.UNVERIFIED, 0),
        placeholder_count=verification.get(VerificationState.PLACEHOLDER, 0),
        note="Counts reflect the latest manual Phase 8 real-host validation run.",
    )


def apply_stability(entries: list[HostValidationMatrixEntry]) -> list[HostValidationMatrixEntry]:
    success_combo_counts: Counter[tuple[str, str | None, str | None, str | None]] = Counter()
    for entry in entries:
        if entry.verification_state == VerificationState.VERIFIED and entry.organize_result == "applied":
            success_combo_counts[
                (
                    entry.search_input_type,
                    entry.dispatch_endpoint_type,
                    entry.path_handoff_status,
                    entry.organize_result,
                )
            ] += 1

    updated: list[HostValidationMatrixEntry] = []
    for entry in entries:
        combo = (
            entry.search_input_type,
            entry.dispatch_endpoint_type,
            entry.path_handoff_status,
            entry.organize_result,
        )
        if entry.blocker:
            state = "blocked"
        elif entry.verification_state != VerificationState.VERIFIED:
            state = "flaky"
        elif success_combo_counts.get(combo, 0) >= 2 or entry.sample_id == "transfer_history_fallback":
            state = "stable"
        else:
            state = "single_sample"
        updated.append(entry.model_copy(update={"stability_state": state}))
    return updated


def run_sample(
    sample: ValidationSample,
    *,
    args: argparse.Namespace,
    dispatch_adapter: RealDownloadDispatchAdapter,
    organize_adapter: RealOrganizeAdapter,
    client: HostHttpClient,
    settings: Settings,
) -> HostValidationMatrixEntry:
    context, search_summary = fetch_search_context(client, settings, sample)
    candidate = build_candidate(sample, context)
    dispatch_result = dispatch_adapter.dispatch(candidate=candidate, downloader_id=args.downloader_id, manual_confirm=True)
    candidate = merge_handoff_payload(candidate, dispatch_result.path_handoff)

    preview_result = None
    apply_result = None
    blocker = None
    verification_state = dispatch_result.verification_state

    if not dispatch_result.dispatchable:
        blocker = dispatch_result.failure_reason or dispatch_result.note
        verification_state = VerificationState.UNVERIFIED
    elif not args.allow_side_effects:
        blocker = "side_effects_disabled"
        verification_state = VerificationState.UNVERIFIED
    elif dispatch_result.path_handoff is None or not dispatch_result.path_handoff.source_path:
        blocker = dispatch_result.path_handoff.handoff_status if dispatch_result.path_handoff else "handoff_missing"
        verification_state = VerificationState.UNVERIFIED
    else:
        plan = build_plan(sample, args, candidate)
        preview_result = organize_adapter.preview(
            candidate=candidate,
            metadata_detail=None,
            binding_id=None,
            plan=plan,
        )
        apply_result = organize_adapter.apply(
            organize_job_id=f"phase8-{sample.sample_id}",
            candidate=candidate,
            metadata_detail=None,
            binding_id=None,
            plan=plan,
        )
        if apply_result.organize_status.value != "applied":
            blocker = apply_result.failure_reason or apply_result.note
            verification_state = VerificationState.UNVERIFIED

    return HostValidationMatrixEntry(
        sample_id=sample.sample_id,
        sample_name=sample.sample_name,
        search_input_type=sample.search_input_type,
        dispatch_endpoint_type=dispatch_result.host_response_summary.get("endpoint_type"),
        path_handoff_source=dispatch_result.path_handoff.handoff_source if dispatch_result.path_handoff else None,
        path_handoff_status=dispatch_result.path_handoff.handoff_status if dispatch_result.path_handoff else None,
        transfer_name_result=preview_result.organize_status.value if preview_result else None,
        transfer_manual_result=apply_result.organize_status.value if apply_result else None,
        organize_result=apply_result.organize_status.value if apply_result else None,
        verification_state=verification_state,
        attempt_count=1,
        success_count=1 if verification_state == VerificationState.VERIFIED else 0,
        blocker=blocker,
        note=(
            "Phase 8 real-host validation sample executed through MusicPilot real adapters."
            if verification_state == VerificationState.VERIFIED
            else "Phase 8 sample hit a real-host blocker and should be treated as non-stable."
        ),
        last_verified_at=now_utc(),
        raw_summary={
            "search": search_summary,
            "dispatch": dispatch_result.model_dump(mode="json"),
            "preview": preview_result.model_dump(mode="json") if preview_result else None,
            "apply": apply_result.model_dump(mode="json") if apply_result else None,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Phase 8 real-host validation matrix.")
    parser.add_argument("--host-base-url", default=os.getenv("MUSICPILOT_REAL_HOST_BASE_URL") or "http://192.168.31.210:3000")
    parser.add_argument("--token-file", default="/Users/lihuanhuan/.env")
    parser.add_argument("--output", default=str(BACKEND_ROOT / "data" / "host_validation_matrix.latest.json"))
    parser.add_argument("--organize-root-path", default=os.getenv("MUSICPILOT_PHASE8_ORGANIZE_TARGET_ROOT") or "/downloads/media/movie")
    parser.add_argument("--downloader-id", default="QB")
    parser.add_argument("--handoff-attempts", type=int, default=4)
    parser.add_argument("--handoff-interval", type=float, default=1.5)
    parser.add_argument("--samples", default="all", help="Comma-separated sample ids or `all`.")
    parser.add_argument(
        "--allow-side-effects",
        action="store_true",
        help="Required to actually call host download/transfer endpoints with real side effects.",
    )
    args = parser.parse_args()

    selected_ids = None if args.samples == "all" else {item.strip() for item in args.samples.split(",") if item.strip()}
    token = load_token(Path(args.token_file))
    settings = build_settings(args, token)
    client = build_http_client(settings)
    handoff_service = HostPathHandoffService(settings=settings, client=client)
    dispatch_adapter = RealDownloadDispatchAdapter(settings=settings, client=client, path_handoff_service=handoff_service)
    organize_adapter = RealOrganizeAdapter(settings=settings, client=client)

    selected_samples = [sample for sample in DEFAULT_SAMPLES if selected_ids is None or sample.sample_id in selected_ids]
    if not selected_samples:
        raise SystemExit("No matching samples were selected.")

    entries: list[HostValidationMatrixEntry] = []
    for sample in selected_samples:
        print(f"Running sample: {sample.sample_id}", flush=True)
        try:
            entry = run_sample(
                sample,
                args=args,
                dispatch_adapter=dispatch_adapter,
                organize_adapter=organize_adapter,
                client=client,
                settings=settings,
            )
        except Exception as exc:  # noqa: BLE001
            entry = HostValidationMatrixEntry(
                sample_id=sample.sample_id,
                sample_name=sample.sample_name,
                search_input_type=sample.search_input_type,
                dispatch_endpoint_type=sample.dispatch_endpoint_type,
                verification_state=VerificationState.UNVERIFIED,
                stability_state="blocked",
                attempt_count=1,
                success_count=0,
                blocker=str(exc),
                note="Phase 8 validation runner captured a real-host failure or timeout.",
                last_verified_at=now_utc(),
                raw_summary={"search_query": sample.search_query},
            )
        entries.append(entry)
        print(
            f"  -> verification={entry.verification_state.value} stability={entry.stability_state} blocker={entry.blocker}",
            flush=True,
        )

    fallback_entry = build_transfer_history_fallback_sample(client, settings, handoff_service)
    if fallback_entry is not None:
        entries.append(fallback_entry)

    if args.allow_side_effects:
        replay_entries = build_transfer_replay_entries(
            client,
            settings,
            handoff_service,
            organize_adapter,
            args,
            limit=2,
        )
        entries.extend(replay_entries)

    entries = apply_stability(entries)
    report = HostValidationMatrixReport(
        generated_at=now_utc(),
        samples=entries,
        summary=summarize(entries),
        note=(
            "This report is generated manually in Phase 8 and is intended for real-host regression only. "
            "It should not be treated as a default CI artifact."
        ),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(entries)} validation entries to {output_path}")


if __name__ == "__main__":
    main()
