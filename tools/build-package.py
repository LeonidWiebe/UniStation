"""Build a deterministic UniStation-only ZIP without importing FreeCAD or the product.

The repository uses UniStation/ as the module subdirectory. The installation
ZIP places InitGui.py directly in UniStation/ and adapts only package metadata.
AxisFlow and FreeCAD are not downloaded or bundled by this public tool.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NS = 'https://wiki.freecad.org/Package_Metadata'
ET.register_namespace('', NS)
EPOCH = (2026, 11, 9, 0, 0, 0)
RUNTIME_SUFFIXES = {'.py', '.svg', '.ts', '.qm'}
PUBLIC_DOCS = ('README.md', 'README.ru.md', 'THIRD_PARTY_NOTICES.md',
               'CHANGELOG.md', 'CONTRIBUTING.md', 'LICENSE')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive_bytes(files):
    import io
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(files.items()):
            path = PurePosixPath(name)
            if path.is_absolute() or '..' in path.parts or '\\' in name:
                raise ValueError('Unsafe archive path: ' + name)
            info = zipfile.ZipInfo(name, EPOCH)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return stream.getvalue()


def prepare(root):
    metadata = ET.parse(root / 'package.xml')
    version = metadata.findtext(f'{{{NS}}}version')
    target = json.loads((root / 'packaging/target.json').read_text(encoding='utf-8'))
    if version != target['version']:
        raise ValueError('Metadata/target version mismatch')
    module = root / 'UniStation'
    files, source_records = {}, []
    runtime = sorted(p for p in module.rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix != '.pyc')
    if not runtime or not (module / 'InitGui.py').is_file():
        raise ValueError('Missing UniStation runtime')
    for path in runtime:
        if path.suffix not in RUNTIME_SUFFIXES:
            raise ValueError('Unexpected runtime file: ' + str(path))
        data = path.read_bytes()
        if path.suffix == '.py':
            ast.parse(data.decode('utf-8-sig'), filename=str(path))
        elif path.suffix in ('.svg', '.ts'):
            ET.fromstring(data)
        relative = path.relative_to(module).as_posix()
        files['UniStation/' + relative] = data
        source_records.append({'source': path.relative_to(root).as_posix(),
                               'archive': 'UniStation/' + relative, 'sha256': sha(data)})
    # Repository metadata points to the inner directory; installed module is flat.
    metadata.find(f'{{{NS}}}content/{{{NS}}}workbench/{{{NS}}}subdirectory').text = './'
    license_file = metadata.find(f'{{{NS}}}license').get('file')
    if license_file != 'LICENSE':
        raise ValueError('Unexpected license path')
    ET.indent(metadata, space='  ')
    files['UniStation/package.xml'] = (b'<?xml version="1.0" encoding="UTF-8"?>\n'
        + ET.tostring(metadata.getroot(), encoding='utf-8') + b'\n')
    for name in PUBLIC_DOCS:
        files['UniStation/' + name] = (root / name).read_bytes()
    for path in sorted((root / 'docs').glob('*.md')):
        files['UniStation/docs/' + path.name] = path.read_bytes()
    files['UniStation/INSTALL.md'] = (root / 'packaging/INSTALL.md').read_bytes()
    files['UniStation/packaging/INSTALL.md'] = (root / 'packaging/INSTALL.md').read_bytes()
    files['UniStation/packaging/target.json'] = (root / 'packaging/target.json').read_bytes()
    files['UniStation/packaging/USER-CHECK.md'] = (root / 'packaging/USER-CHECK.md').read_bytes()
    files['UniStation/USER-CHECK.md'] = (root / 'packaging/USER-CHECK.md').read_bytes()
    manifest = {
        'schema_version': 1, 'version': version,
        'status': 'installation-candidate-user-validation-pending',
        'product_baseline_commit': target['product_baseline_commit'],
        'runtime_files': source_records,
        'files': {name: sha(data) for name, data in sorted(files.items())},
        'freecad_bundled': False, 'axisflow_bundled': False,
        'tests_or_product_imports_performed': False,
    }
    files['UniStation/PACKAGE-MANIFEST.json'] = (json.dumps(manifest, ensure_ascii=False,
        indent=2) + '\n').encode('utf-8')
    return version, files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    version, files = prepare(ROOT)
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    path = output / f'UniStation-{version}-workbench.zip'
    data = archive_bytes(files)
    # Never replace a different artifact under the same version/name.
    if path.exists() and path.read_bytes() != data:
        raise ValueError('Different artifact already exists: ' + str(path))
    if not path.exists():
        with path.open('xb') as handle:
            handle.write(data)
    checksum = path.with_suffix(path.suffix + '.sha256')
    expected = f'{sha(data)}  {path.name}\n'
    if checksum.exists() and checksum.read_text(encoding='ascii') != expected:
        raise ValueError('Different checksum already exists: ' + str(checksum))
    checksum.write_text(expected, encoding='ascii')
    print(json.dumps({'path': str(path), 'sha256': sha(data), 'files': len(files),
                      'bytes': len(data), 'product_execution': False}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Package build failed: {exc}', file=sys.stderr)
        sys.exit(1)
