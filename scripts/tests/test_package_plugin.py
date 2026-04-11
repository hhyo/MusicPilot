import tempfile
import unittest
from pathlib import Path

from scripts.package_plugin import (
    normalize_remote_entry_asset_paths,
    publish_versioned_remote_bundle,
)


class NormalizeRemoteEntryAssetPathsTests(unittest.TestCase):
    def test_normalizes_broken_federation_asset_paths(self) -> None:
        remote_entry = """const i=o.substring(0,o.lastIndexOf("remoteEntry.js")),a='./';'assets',e.forEach(l=>{});y("./assets/__federation_expose_Page.js");w("./assets/__federation_expose_Dashboard.js");"""

        with tempfile.TemporaryDirectory() as tmpdir:
            remote_entry_path = Path(tmpdir) / "remoteEntry.js"
            remote_entry_path.write_text(remote_entry, encoding="utf-8")

            normalize_remote_entry_asset_paths(remote_entry_path)

            normalized = remote_entry_path.read_text(encoding="utf-8")
            self.assertIn("a='';", normalized)
            self.assertIn('y("./__federation_expose_Page.js")', normalized)
            self.assertIn('w("./__federation_expose_Dashboard.js")', normalized)
            self.assertNotIn("a='./';", normalized)
            self.assertNotIn('y("./assets/', normalized)
            self.assertNotIn('w("./assets/', normalized)

    def test_normalizes_exposed_chunk_loader_paths(self) -> None:
        remote_entry = """const P={},g=new Set(["Module","__esModule","default","_export_sfc"]);let y={"./AppPage":()=>(p(["__federation_expose_AppPage.css","createApp.css"],!1,"./AppPage"),b("./assets/__federation_expose_AppPage.js").then(e=>e)),"./Page":()=>(p(["__federation_expose_Page.css"],!1,"./Page"),b("./assets/__federation_expose_Page.js").then(e=>e))};"""

        with tempfile.TemporaryDirectory() as tmpdir:
            remote_entry_path = Path(tmpdir) / "remoteEntry.js"
            remote_entry_path.write_text(remote_entry, encoding="utf-8")

            normalize_remote_entry_asset_paths(remote_entry_path)

            normalized = remote_entry_path.read_text(encoding="utf-8")
            self.assertIn('b("./__federation_expose_AppPage.js")', normalized)
            self.assertIn('b("./__federation_expose_Page.js")', normalized)
            self.assertNotIn('b("./assets/', normalized)

    def test_missing_remote_entry_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_entry_path = Path(tmpdir) / "missing-remoteEntry.js"
            normalize_remote_entry_asset_paths(remote_entry_path)
            self.assertFalse(remote_entry_path.exists())

    def test_publish_versioned_remote_bundle_copies_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            static_dir = Path(tmpdir) / "static"
            assets_dir = static_dir / "assets"
            assets_dir.mkdir(parents=True)
            remote_entry = assets_dir / "remoteEntry.js"
            remote_entry.write_text("export const ok = true;", encoding="utf-8")
            (assets_dir / "chunk.js").write_text("console.log('chunk');", encoding="utf-8")

            publish_versioned_remote_bundle(static_dir)

            remotes_dir = static_dir / "remotes"
            remote_versions = [path for path in remotes_dir.iterdir() if path.is_dir()]
            self.assertEqual(len(remote_versions), 1)
            version_dir = remote_versions[0]
            self.assertTrue((version_dir / "remoteEntry.js").exists())
            self.assertTrue((version_dir / "chunk.js").exists())


if __name__ == "__main__":
    unittest.main()
