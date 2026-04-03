"""Backend service package.

The package intentionally avoids eager re-exports so host-aware adapters can import
individual service modules without triggering circular imports during startup.
"""

