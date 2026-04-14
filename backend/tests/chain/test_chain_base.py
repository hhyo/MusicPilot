from pathlib import Path
from unittest import TestCase


class MusicChainBaseLayoutTest(TestCase):
    def test_chain_base_exists_in_chain_package(self) -> None:
        chain_init = Path("app/chain/__init__.py")
        self.assertTrue(chain_init.exists())
        content = chain_init.read_text(encoding="utf-8")
        self.assertIn("class MusicChainBase", content)
