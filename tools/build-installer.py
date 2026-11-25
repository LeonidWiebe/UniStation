"""Build the Windows wizard from current sources; never run the installer.

Only Python's standard library and an explicit portable NSIS compiler are used.
Only AxisFlow is taken byte-for-byte from the pinned earlier release ZIP.
"""
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NS = 'https://wiki.freecad.org/Package_Metadata'
ET.register_namespace('', NS)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_zip(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 11, 9, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--makensis', type=Path, required=True)
    parser.add_argument('--payload-archive', type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('C:/projects/ustatic/dist/installer-build'))
    args = parser.parse_args()
    config = json.loads((ROOT / 'packaging/installer/config.json').read_text(encoding='utf-8'))
    archive_path = args.payload_archive or ROOT / config['input_archive']
    data = archive_path.read_bytes()
    if sha(data) != config['input_archive_sha256']:
        raise ValueError('Input release archive SHA-256 mismatch')
    compiler = args.makensis.resolve(strict=True)
    version = subprocess.check_output([str(compiler), '/VERSION'], text=True).strip()
    if version != 'v' + config['compiler']['version']:
        raise ValueError('Wrong compiler version: ' + version)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        original = {n: archive.read(n) for n in archive.namelist()}
    runtime, axisflow = {}, {}
    for path in sorted((ROOT / 'UniStation').rglob('*')):
        if not path.is_file() or '__pycache__' in path.parts or path.suffix == '.pyc':
            continue
        if path.suffix not in {'.py', '.svg', '.ts', '.qm'}:
            raise ValueError('Unexpected runtime source: ' + str(path))
        name = path.relative_to(ROOT / 'UniStation').as_posix()
        payload = path.read_bytes()
        if name.endswith('.py'):
            ast.parse(payload.decode('utf-8-sig'), feature_version=(3, 11))
        elif name.endswith(('.svg', '.ts')):
            ET.fromstring(payload)
        runtime[name] = payload
    if 'InitGui.py' not in runtime or 'unistation/__init__.py' not in runtime:
        raise ValueError('Missing workbench entry points')
    runtime_count = len(runtime)
    source_hashes = {n: sha(b) for n, b in sorted(runtime.items())}
    for name in ['LICENSE', 'THIRD_PARTY_NOTICES.md']:
        runtime[name] = (ROOT / name).read_bytes()
    metadata = ET.parse(ROOT / 'package.xml').getroot()
    if metadata.findtext(f'{{{NS}}}version') != config['version']:
        raise ValueError('Metadata/config version mismatch')
    for key, element in [('freecad_min', 'freecadmin'), ('freecad_max', 'freecadmax')]:
        if config[key] != metadata.findtext(f'{{{NS}}}{element}'):
            raise ValueError('Metadata/config FreeCAD range mismatch: ' + key)
    if config['python_version'] != '3.11':
        raise ValueError('The pinned AxisFlow payload requires Python 3.11')
    # FreeCAD compares major.minor.patch + "." + BuildRevision. A plain
    # freecadmax=1.1.4 would exclude 1.1.4.<revision>. Use the next patch as
    # the exclusive metadata boundary; setup and startup enforce the exact max.
    max_parts = [int(part) for part in config['freecad_max'].split('.')]
    if len(max_parts) != 3:
        raise ValueError('Expected a three-component FreeCAD maximum')
    metadata_max_exclusive = '.'.join(map(str, [*max_parts[:2], max_parts[2] + 1]))
    metadata.find(f'{{{NS}}}freecadmax').text = metadata_max_exclusive
    metadata.find(f'{{{NS}}}content/{{{NS}}}workbench/{{{NS}}}subdirectory').text = './'
    runtime['package.xml'] = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(metadata, encoding='utf-8') + b'\n'
    runtime['PACKAGE-MANIFEST.json'] = (json.dumps({
        'version': config['version'], 'kind': 'Windows installer runtime',
        'input_release_archive_sha256': config['input_archive_sha256'],
        'source_kind': 'current UniStation source tree',
        'runtime_sources': source_hashes,
        'files': {n: sha(b) for n, b in sorted(runtime.items())}}, indent=2) + '\n').encode()
    for name, payload in original.items():
        if name.startswith('Mod/AxisFlow/'):
            axisflow[name.removeprefix('Mod/AxisFlow/')] = payload
    assert len(axisflow) == 34
    assert sha(axisflow['AxisFlow.pyd']) == config['axisflow_binary_sha256']
    assert 'LICENSE' in axisflow and any(n.startswith('sources/') for n in axisflow)
    docs = {'INSTALL.md': (ROOT / 'packaging/installer/USER-GUIDE.md').read_bytes()}
    for path in sorted((ROOT / 'docs').iterdir()):
        if path.is_file() and path.suffix in {'.md', '.json'}:
            docs[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for path in sorted((ROOT / 'packaging').rglob('*.md')):
        docs[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    for path in [ROOT / 'packaging/installer/UniStation.nsi', ROOT / 'tools/build-installer.py']:
        ast.parse(path.read_text(encoding='utf-8-sig')) if path.suffix == '.py' else None
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    launcher = output / 'Launch-UniStation.exe'
    if launcher.exists():
        raise ValueError('Refusing to overwrite an existing launcher: ' + str(launcher))
    launcher_result = subprocess.run([
        str(compiler), '/V3', '/NOCD', '/INPUTCHARSET', 'UTF8',
        '/DFILEVERSION=' + config['file_version'], '/DOUTFILE=' + str(launcher),
        str(ROOT / 'packaging/installer/Launch-UniStation.nsi'),
    ], capture_output=True, text=True, encoding='utf-8', errors='replace')
    (output / 'launcher-compile.log').write_text(
        launcher_result.stdout + launcher_result.stderr, encoding='utf-8')
    if launcher_result.returncode:
        raise RuntimeError('Launcher compiler failed; see launcher-compile.log')
    macro = (ROOT / 'packaging/installer/Start-UniStation.FCMacro').read_text(encoding='utf-8')
    macro = macro.replace('@FREECAD_MIN@', config['freecad_min']).replace(
        '@FREECAD_MAX@', config['freecad_max'])
    ast.parse(macro, feature_version=(3, 11))
    nsis_license = (compiler.parent / 'COPYING').read_bytes()
    own_sources = {name: (ROOT / name).read_bytes() for name in [
        'packaging/installer/UniStation.nsi', 'packaging/installer/FreeCAD.nsh',
        'packaging/installer/Launch-UniStation.nsi', 'packaging/installer/Start-UniStation.FCMacro',
        'packaging/installer/unistation.ico', 'packaging/installer/unistation-setup.ico',
        'packaging/installer/config.json',
        'packaging/installer/USER-GUIDE.md', 'packaging/installer/USER-CHECK.md',
        'packaging/installer/BUILD.md', 'tools/build-installer.py', 'LICENSE',
        'package.xml', 'THIRD_PARTY_NOTICES.md']}
    own_sources.update({'UniStation/' + n: b for n, b in runtime.items()
                        if n in source_hashes})
    own_sources.update({n: (ROOT / n).read_bytes() for n in docs if n != 'INSTALL.md'})
    support = {
        'Launch-UniStation.exe': launcher.read_bytes(),
        'Start-UniStation.FCMacro': macro.encode('utf-8'),
        'USER-GUIDE.txt': b'\xef\xbb\xbf' + docs['INSTALL.md'],
        'USER-CHECK.txt': b'\xef\xbb\xbf' + (ROOT / 'packaging/installer/USER-CHECK.md').read_bytes(),
        'LICENSE-UniStation.txt': runtime['LICENSE'], 'LICENSE-AxisFlow.txt': axisflow['LICENSE'],
        'NSIS-COPYING.txt': nsis_license,
        'Installer-source.zip': source_zip(own_sources),
        'LICENSES.txt': b'UniStation: GPL-3.0-only\r\n\r\n' + runtime['LICENSE']
            + b'\r\n\r\nAxisFlow: LGPL-2.1-or-later\r\n\r\n' + axisflow['LICENSE'],
    }
    stage = output / 'stage'
    generated = output / 'payload.nsh'
    groups = {'UniRuntime': runtime, 'UniDocs': docs, 'AxisFlow': axisflow, 'Support': support}
    expected = {f'{group}/{name}' for group, files in groups.items() for name in files}
    if stage.exists():
        unexpected = {p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()} - expected
        if unexpected:
            raise ValueError('Unexpected staging files: ' + ', '.join(sorted(unexpected)))
    for group, files in groups.items():
        for name, payload in files.items():
            if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                raise ValueError('Unsafe payload path')
            path = stage / group / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    # Explicit per-file copy tables: no recursive deletion or arbitrary user-tree copy.
    lines = ['; Generated from the exact payload inventory. Do not edit.']
    for group, files in groups.items():
        lines.append(f'!macro Copy{group} SOURCE DEST')
        for name in sorted(files):
            relative = name.replace('/', '\\')
            parent = str(PurePosixPath(name).parent).replace('/', '\\')
            dest_parent = '${DEST}' if parent == '.' else '${DEST}\\' + parent
            lines += [f'  CreateDirectory "{dest_parent}"', '  ClearErrors',
                      f'  CopyFiles /SILENT "${{SOURCE}}\\{relative}" "{dest_parent}"',
                      '  IfErrors install_failed']
        lines.append('!macroend')
    generated.write_text('\n'.join(lines) + '\n', encoding='utf-8-sig')
    exe = output / f"UniStation-{config['version']}-win64-setup.exe"
    if exe.exists():
        raise ValueError('Refusing to overwrite an existing installer: ' + str(exe))
    command = [str(compiler), '/V3', '/NOCD', '/INPUTCHARSET', 'UTF8',
               '/DVERSION=' + config['version'], '/DFILEVERSION=' + config['file_version'],
               '/DFREECAD_MIN=' + config['freecad_min'], '/DFREECAD_MAX=' + config['freecad_max'],
               '/DPAYLOAD=' + str(stage), '/DTABLES=' + str(generated),
               '/DOUTFILE=' + str(exe), str(ROOT / 'packaging/installer/UniStation.nsi')]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
    (output / 'compile.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    if result.returncode:
        print(result.stdout + result.stderr)
        raise RuntimeError('NSIS compiler failed; see compile.log')
    manifest = {'version': config['version'], 'input_archive_sha256': sha(data),
                'exe': str(exe), 'exe_sha256': sha(exe.read_bytes()), 'exe_bytes': exe.stat().st_size,
                'compiler_version': version, 'payload_files': {
                    group + '/' + n: sha(b) for group, files in groups.items() for n, b in sorted(files.items())},
                'product_runtime_files': runtime_count, 'runtime_source_hashes': source_hashes,
                'axisflow_runtime_unchanged': 34,
                'freecad_min': config['freecad_min'], 'freecad_max': config['freecad_max'],
                'metadata_freecad_max_exclusive': metadata_max_exclusive,
                'launcher_sha256': sha(launcher.read_bytes()),
                'installer_executed': False, 'freecad_gui_or_tests_run': False}
    (output / 'BUILD-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    exe.with_suffix('.exe.sha256').write_text(f"{manifest['exe_sha256']}  {exe.name}\n", encoding='ascii')
    print(json.dumps({k: manifest[k] for k in ['version', 'exe', 'exe_bytes', 'exe_sha256',
                                             'product_runtime_files', 'axisflow_runtime_unchanged']}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Installer build failed: {exc}', file=sys.stderr)
        sys.exit(1)
