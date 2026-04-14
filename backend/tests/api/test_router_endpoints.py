from pathlib import Path
from unittest import TestCase


class RouterEndpointsLayoutTest(TestCase):
    def test_router_imports_endpoints_package(self) -> None:
        router_path = Path("app/api/router.py")
        content = router_path.read_text(encoding="utf-8")
        self.assertIn(".endpoints.", content)
        self.assertNotIn(".routes.", content)

    def test_endpoint_modules_do_not_import_routes(self) -> None:
        endpoints_dir = Path("app/api/endpoints")
        for path in endpoints_dir.glob("*.py"):
            if path.name == "__init__.py":
                continue
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("..routes", content, msg=f"{path} still imports api.routes")


class ActiveBackendImportsLayoutTest(TestCase):
    def test_active_backend_paths_do_not_import_legacy_structure(self) -> None:
        base = Path("app")
        targets = [
            base / "api" / "endpoints",
            base / "chain",
            base / "core",
            base / "startup",
        ]
        legacy_markers = (
            ".services.",
            ".adapters.",
            ".repositories.",
            ".routes.",
            ".tasks.",
            "..services",
            "..adapters",
            "..repositories",
            "..routes",
            "..tasks",
            "app.services",
            "app.adapters",
            "app.repositories",
            "app.models",
            "app.tasks",
        )

        for target in targets:
            for path in target.rglob("*.py"):
                content = path.read_text(encoding="utf-8")
                for marker in legacy_markers:
                    self.assertNotIn(marker, content, msg=f"{path} still imports legacy path marker {marker}")

        for path in (base / "main.py", base / "__init__.py", base / "api" / "health.py"):
            content = path.read_text(encoding="utf-8")
            for marker in legacy_markers:
                self.assertNotIn(marker, content, msg=f"{path} still imports legacy path marker {marker}")


class RuntimeMirrorLayoutTest(TestCase):
    def test_plugin_runtime_uses_same_backend_layout(self) -> None:
        runtime_root = Path("../plugin_runtime/plugins/musicpilot")
        expected_dirs = [
            runtime_root / "api" / "endpoints",
            runtime_root / "chain",
            runtime_root / "core",
            runtime_root / "db" / "models",
            runtime_root / "helper",
            runtime_root / "modules",
            runtime_root / "schemas",
            runtime_root / "startup",
            runtime_root / "utils",
        ]
        removed_dirs = [
            runtime_root / "api" / "routes",
            runtime_root / "services",
            runtime_root / "models",
            runtime_root / "repositories",
            runtime_root / "adapters",
            runtime_root / "tasks",
        ]

        for path in expected_dirs:
            self.assertTrue(path.exists(), msg=f"{path} should exist in runtime mirror")
        for path in removed_dirs:
            self.assertFalse(path.exists(), msg=f"{path} should be removed from runtime mirror")
