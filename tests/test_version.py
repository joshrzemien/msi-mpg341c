"""Keep source and development-install release versions aligned."""
from pathlib import Path
import tomllib
from msi_monitor import __version__

ROOT = Path(__file__).resolve().parents[1]

def test_package_version_matches_module():
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text())
    assert project['project']['version'] == __version__

def test_lockfile_version_matches_package():
    lock = tomllib.loads((ROOT / 'uv.lock').read_text())
    package = next(p for p in lock['package'] if p['name'] == 'msi-mpg341c')
    assert package['version'] == __version__
