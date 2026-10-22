"""Prepare one pinned official SDK artifact for both validation and direct tests."""
from pathlib import Path
import shutil
import subprocess

VERSION = 'v0.3.0-rc7'
archive = f'genvm-universal-{VERSION}.tar.xz'
source = Path.home() / '.cache' / 'genvm-linter' / archive
if not source.is_file():
    subprocess.run(['genvm-lint', 'download', '--version', VERSION], check=True)
if not source.is_file() or source.stat().st_size == 0:
    raise RuntimeError(f'Pinned SDK archive unavailable: {archive}')
destination = Path.home() / '.cache' / 'gltest-direct' / archive
destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(source, destination)
print(f'Official SDK {VERSION} ready for direct-mode tests.')
