"""Create an import-ready distribution with the mod data at the archive root."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import hashlib
import re

root = Path(__file__).resolve().parents[1]
source = root / 'Memorial Ledger'
version = (root / 'VERSION').read_text(encoding='utf-8').strip()
if not re.fullmatch(r'\d+\.\d+\.\d+', version):
    raise ValueError('VERSION must contain a semantic version, such as 0.2.5')
target = root / 'dist' / f'MemorialLedger-{version}.zip'
target.parent.mkdir(exist_ok=True)
with ZipFile(target, 'w', compression=ZIP_DEFLATED) as archive:
    for path in sorted(source.rglob('*')):
        if not path.is_file():
            continue
        info = ZipInfo(path.relative_to(source).as_posix(), date_time=(2026, 10, 7, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, path.read_bytes())
with ZipFile(target) as archive:
    assert archive.testzip() is None, 'Archive integrity check failed'
    names = set(archive.namelist())
    assert 'MemorialLedger.omwscripts' in names
    for line in archive.read('MemorialLedger.omwscripts').decode('utf-8').splitlines():
        if line.strip():
            script = line.split(':', 1)[1].strip()
            assert script in names, f'Missing script: {script}'
print(target)
print('Verified: root-level manifest, script paths, and archive integrity')
print('SHA256:', hashlib.sha256(target.read_bytes()).hexdigest())
