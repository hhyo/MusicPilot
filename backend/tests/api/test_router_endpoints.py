from pathlib import Path
from unittest import TestCase


class RouterEndpointsLayoutTest(TestCase):
    def test_router_imports_endpoints_package(self) -> None:
        router_path = Path("app/api/router.py")
        content = router_path.read_text(encoding="utf-8")
        self.assertIn(".endpoints.", content)
        self.assertNotIn(".routes.", content)
