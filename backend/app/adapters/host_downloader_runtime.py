"""Thin in-process host-runtime bridge for MusicPilot music downloader dispatch."""

from __future__ import annotations

from importlib import import_module
import re
from typing import Any, Callable
from urllib.parse import urljoin
from uuid import uuid4

from .host_http import HostTransportError


class HostDownloaderRuntimeBridge:
    """Submit torrents directly to the host downloader module inside the plugin process."""

    def __init__(
        self,
        *,
        helper_factory: Callable[[], Any] | None = None,
        tag_generator: Callable[[], str] | None = None,
        torrent_content_fetcher: Callable[..., str | bytes | None] | None = None,
        detail_download_url_resolver: Callable[..., str | None] | None = None,
        torrent_signature_resolver: Callable[[str | bytes], tuple[str, int] | None] | None = None,
    ) -> None:
        self._helper_factory = helper_factory or self._default_helper_factory
        self._tag_generator = tag_generator or self._default_tag_generator
        self._torrent_content_fetcher = torrent_content_fetcher or self._default_torrent_content_fetcher
        self._detail_download_url_resolver = detail_download_url_resolver or self._default_detail_download_url_resolver
        self._torrent_signature_resolver = torrent_signature_resolver or self._default_torrent_signature_resolver

    def submit_torrent(
        self,
        *,
        downloader: str,
        content: str | bytes,
        page_url: str | None = None,
        title: str,
        site_name: str,
        download_dir: str | None = None,
        label: str | None = None,
        cookie: str | None = None,
        site_ua: str | None = None,
        site_proxy: bool | None = None,
    ) -> dict[str, Any]:
        if not content:
            return self._failure("缺少可提交的种子内容")

        prepared_content = self._prepare_content(
            content=content,
            page_url=page_url,
            cookie=cookie,
            site_ua=site_ua,
            site_proxy=site_proxy,
        )
        if not prepared_content:
            return self._failure("下载种子内容为空")

        helper = self._helper_factory()
        service = helper.get_service(name=downloader)
        if not service or not getattr(service, "instance", None):
            raise HostTransportError(
                f"MoviePilot downloader runtime is unavailable for downloader: {downloader}",
                reason_code="moviepilot_downloader_runtime_unavailable",
            )

        instance = service.instance
        service_type = str(getattr(service, "type", "") or getattr(getattr(service, "config", None), "type", "") or "")

        if service_type == "qbittorrent":
            return self._submit_qbittorrent(
                instance=instance,
                downloader=downloader,
                content=prepared_content,
                download_dir=download_dir,
                label=label,
                cookie=cookie,
            )
        if service_type == "transmission":
            return self._submit_transmission(
                instance=instance,
                downloader=downloader,
                content=prepared_content,
                download_dir=download_dir,
                label=label,
                cookie=cookie,
            )
        if service_type == "rtorrent":
            return self._submit_rtorrent(
                instance=instance,
                downloader=downloader,
                content=prepared_content,
                download_dir=download_dir,
                label=label,
                cookie=cookie,
            )

        raise HostTransportError(
            f"MoviePilot downloader runtime does not support service type: {service_type or 'unknown'}",
            reason_code="moviepilot_downloader_service_unsupported",
        )

    def _submit_qbittorrent(
        self,
        *,
        instance: Any,
        downloader: str,
        content: str | bytes,
        download_dir: str | None,
        label: str | None,
        cookie: str | None,
    ) -> dict[str, Any]:
        dispatch_tag = self._tag_generator()
        tags = [dispatch_tag]
        if label:
            tags.extend([item.strip() for item in label.split(",") if item.strip()])
        state = instance.add_torrent(
            content=content,
            is_paused=False,
            download_dir=download_dir,
            tag=tags,
            cookie=cookie or "",
            category=None,
            ignore_category_check=False,
        )
        if not state:
            existing_id = self._find_existing_qbittorrent_task_id(instance=instance, content=content)
            if existing_id:
                return self._success(downloader=downloader, download_id=str(existing_id), message="下载任务已存在")
            return self._failure("添加下载任务失败")
        torrent_id = instance.get_torrent_id_by_tag(tags=dispatch_tag)
        if not torrent_id:
            return self._failure("下载任务添加成功，但获取任务标识失败")
        return self._success(downloader=downloader, download_id=str(torrent_id), message="添加下载任务成功")

    def _submit_transmission(
        self,
        *,
        instance: Any,
        downloader: str,
        content: str | bytes,
        download_dir: str | None,
        label: str | None,
        cookie: str | None,
    ) -> dict[str, Any]:
        labels = [item.strip() for item in label.split(",") if item.strip()] if label else None
        torrent = instance.add_torrent(
            content=content,
            is_paused=False,
            download_dir=download_dir,
            labels=labels,
            cookie=cookie or "",
        )
        torrent_id = getattr(torrent, "hashString", None) if torrent is not None else None
        if not torrent_id:
            return self._failure("添加下载任务失败")
        return self._success(downloader=downloader, download_id=str(torrent_id), message="添加下载任务成功")

    def _submit_rtorrent(
        self,
        *,
        instance: Any,
        downloader: str,
        content: str | bytes,
        download_dir: str | None,
        label: str | None,
        cookie: str | None,
    ) -> dict[str, Any]:
        dispatch_tag = self._tag_generator()
        tags = [dispatch_tag]
        if label:
            tags.extend([item.strip() for item in label.split(",") if item.strip()])
        state = instance.add_torrent(
            content=content,
            is_paused=False,
            download_dir=download_dir,
            tags=tags,
            cookie=cookie or "",
        )
        if not state:
            return self._failure("添加下载任务失败")
        torrent_id = instance.get_torrent_id_by_tag(tags=dispatch_tag)
        if not torrent_id:
            return self._failure("下载任务添加成功，但获取任务标识失败")
        return self._success(downloader=downloader, download_id=str(torrent_id), message="添加下载任务成功")

    def _default_helper_factory(self) -> Any:
        try:
            module = import_module("app.helper.downloader")
        except Exception as exc:  # pragma: no cover - depends on host runtime
            raise HostTransportError(
                f"MoviePilot downloader runtime is only available inside the host plugin process: {exc}",
                reason_code="moviepilot_downloader_runtime_unavailable",
            ) from exc
        helper_cls = getattr(module, "DownloaderHelper")
        return helper_cls()

    def _default_torrent_content_fetcher(
        self,
        *,
        url: str,
        cookie: str | None,
        site_ua: str | None,
        site_proxy: bool | None,
        referer: str | None = None,
    ) -> str | bytes | None:
        if url.startswith("["):
            try:
                download_module = import_module("app.chain.download")
                context_module = import_module("app.core.context")
            except Exception as exc:  # pragma: no cover - depends on host runtime
                raise HostTransportError(
                    f"MoviePilot torrent content runtime is unavailable inside the host plugin process: {exc}",
                    reason_code="moviepilot_torrent_content_runtime_unavailable",
                ) from exc

            download_chain_cls = getattr(download_module, "DownloadChain")
            torrent_info_cls = getattr(context_module, "TorrentInfo")
            torrent_info = torrent_info_cls(
                title="MusicPilot Runtime Dispatch",
                enclosure=url,
                site_cookie=cookie,
                site_ua=site_ua,
                site_proxy=bool(site_proxy),
            )
            content, _folder_name, _files = download_chain_cls().download_torrent(torrent_info)
            return content

        try:
            torrent_module = import_module("app.helper.torrent")
        except Exception as exc:  # pragma: no cover - depends on host runtime
            raise HostTransportError(
                f"MoviePilot torrent helper runtime is unavailable inside the host plugin process: {exc}",
                reason_code="moviepilot_torrent_content_runtime_unavailable",
            ) from exc

        torrent_helper_cls = getattr(torrent_module, "TorrentHelper")
        _cache_path, content, _folder_name, _files, _error = torrent_helper_cls().download_torrent(
            url=url,
            cookie=cookie,
            ua=site_ua,
            referer=referer,
            proxy=bool(site_proxy),
        )
        return content

    def _default_tag_generator(self) -> str:
        return f"musicpilot-{uuid4().hex[:10]}"

    def _prepare_content(
        self,
        *,
        content: str | bytes,
        page_url: str | None,
        cookie: str | None,
        site_ua: str | None,
        site_proxy: bool | None,
    ) -> str | bytes | None:
        if isinstance(content, bytes):
            return content
        if content.startswith("magnet:"):
            return content
        if content.startswith("http://") or content.startswith("https://") or content.startswith("["):
            fetch_url = content
            if page_url and not content.startswith("["):
                direct_url = self._detail_download_url_resolver(
                    page_url=page_url,
                    cookie=cookie,
                    site_ua=site_ua,
                    site_proxy=site_proxy,
                )
                if direct_url:
                    fetch_url = direct_url
            prepared = self._torrent_content_fetcher(
                url=fetch_url,
                cookie=cookie,
                site_ua=site_ua,
                site_proxy=site_proxy,
                referer=page_url,
            )
            if self._looks_like_html(prepared) and page_url and fetch_url == content:
                direct_url = self._detail_download_url_resolver(
                    page_url=page_url,
                    cookie=cookie,
                    site_ua=site_ua,
                    site_proxy=site_proxy,
                )
                if direct_url and direct_url != content:
                    prepared = self._torrent_content_fetcher(
                        url=direct_url,
                        cookie=cookie,
                        site_ua=site_ua,
                        site_proxy=site_proxy,
                        referer=page_url,
                    )
            return prepared
        return content

    def _default_detail_download_url_resolver(
        self,
        *,
        page_url: str,
        cookie: str | None,
        site_ua: str | None,
        site_proxy: bool | None,
    ) -> str | None:
        try:
            request_module = import_module("app.utils.http")
        except Exception as exc:  # pragma: no cover - depends on host runtime
            raise HostTransportError(
                f"MoviePilot detail page runtime is unavailable inside the host plugin process: {exc}",
                reason_code="moviepilot_torrent_content_runtime_unavailable",
            ) from exc

        request_utils_cls = getattr(request_module, "RequestUtils")
        response = request_utils_cls(
            ua=site_ua,
            cookies=cookie,
            referer=page_url,
            proxies=None,
        ).get_res(page_url)
        if not response or not response.text:
            return None
        matches = re.findall(r'href="([^"]*download\.php[^"]*)"', response.text, re.I)
        preferred = None
        fallback = None
        for match in matches:
            resolved = urljoin(page_url, match)
            if "passkey=" in resolved:
                preferred = resolved
                break
            if fallback is None:
                fallback = resolved
        return preferred or fallback

    @staticmethod
    def _looks_like_html(content: str | bytes | None) -> bool:
        if not isinstance(content, bytes):
            return False
        prefix = content.lstrip()[:64].lower()
        return prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html")

    def _find_existing_qbittorrent_task_id(self, *, instance: Any, content: str | bytes) -> str | None:
        signature = self._torrent_signature_resolver(content)
        if not signature:
            return None
        expected_name, expected_size = signature
        torrents, error = instance.get_torrents()
        if error or not torrents:
            return None
        for torrent in torrents:
            if torrent.get("name") == expected_name and int(torrent.get("total_size") or 0) == expected_size:
                return str(torrent.get("hash") or "") or None
        return None

    def _default_torrent_signature_resolver(self, content: str | bytes) -> tuple[str, int] | None:
        if not isinstance(content, bytes):
            return None
        try:
            torrent_module = import_module("torrentool.api")
        except Exception:
            return None
        torrent_cls = getattr(torrent_module, "Torrent")
        try:
            torrent = torrent_cls.from_string(content)
        except Exception:
            return None
        return getattr(torrent, "name", None), int(getattr(torrent, "total_size", 0) or 0)

    def _success(self, *, downloader: str, download_id: str, message: str) -> dict[str, Any]:
        return {
            "success": True,
            "dispatch_status": "host_submitted",
            "target_downloader": downloader,
            "download_id": download_id,
            "message": message,
        }

    def _failure(self, message: str) -> dict[str, Any]:
        return {
            "success": False,
            "dispatch_status": "host_rejected",
            "download_id": None,
            "message": message,
        }
