"""Build the Windows wizard from the pinned release ZIP; never run the installer.

Only Python's standard library and an explicit portable NSIS compiler are used.
The accepted UniStation runtime/AxisFlow bytes are verified before packaging.
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
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist/installer-build')
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
    previous = json.loads(original['Mod/UniStation/PACKAGE-MANIFEST.json'])
    runtime, axisflow = {}, {}
    for item in previous['runtime_files']:
        name = item['archive'].removeprefix('UniStation/')
        payload = original['Mod/UniStation/' + name]
        if sha(payload) != item['sha256']:
            raise ValueError('Runtime mismatch: ' + name)
        if (ROOT / item['source']).is_file() and (ROOT / item['source']).read_bytes() != payload:
            raise ValueError('Working product differs from accepted payload: ' + name)
        if name.endswith('.py'):
            ast.parse(payload.decode('utf-8-sig'), feature_version=(3, 11))
        elif name.endswith(('.svg', '.ts')):
            ET.fromstring(payload)
        runtime[name] = payload
    assert len(runtime) == 45
    for name in ['LICENSE', 'THIRD_PARTY_NOTICES.md']:
        runtime[name] = original['Mod/UniStation/' + name]
    metadata = ET.fromstring(original['Mod/UniStation/package.xml'])
    metadata.find(f'{{{NS}}}version').text = config['version']
    metadata.find(f'{{{NS}}}description').text = 'Experimental drafting workbench with AxisFlow point input.'
    metadata.find(f'{{{NS}}}url[@type="repository"]').set('branch', 'installer/' + config['version'])
    runtime['package.xml'] = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(metadata, encoding='utf-8') + b'\n'
    runtime['PACKAGE-MANIFEST.json'] = (json.dumps({
        'version': config['version'], 'kind': 'Windows installer runtime',
        'input_release_archive_sha256': config['input_archive_sha256'],
        'product_baseline_commit': config['product_baseline_commit'],
        'runtime_files_unchanged': 45,
        'files': {n: sha(b) for n, b in sorted(runtime.items())}}, indent=2) + '\n').encode()
    for name, payload in original.items():
        if name.startswith('Mod/AxisFlow/'):
            axisflow[name.removeprefix('Mod/AxisFlow/')] = payload
    assert len(axisflow) == 34
    assert sha(axisflow['AxisFlow.pyd']) == config['axisflow_binary_sha256']
    assert 'LICENSE' in axisflow and any(n.startswith('sources/') for n in axisflow)
    docs = {'INSTALL.md': (ROOT / 'packaging/installer/USER-GUIDE.md').read_bytes()}
    public = ROOT / 'publication/package-candidate'
    doc_root = public if (public / 'docs/usage.md').is_file() else ROOT
    for name in ['docs/usage.md', 'docs/status.md', 'docs/compatibility-1.1.1.md']:
        path = doc_root / name
        # The installed Installer-source.zip is rebuildable with the pinned
        # input ZIP even without the rest of the repository checkout.
        docs[name] = path.read_bytes() if path.is_file() else original['Mod/UniStation/' + name]
    for path in [ROOT / 'packaging/installer/UniStation.nsi', ROOT / 'tools/build-installer.py']:
        ast.parse(path.read_text(encoding='utf-8-sig')) if path.suffix == '.py' else None
    nsis_license = (compiler.parent / 'COPYING').read_bytes()
    own_sources = {name: (ROOT / name).read_bytes() for name in [
        'packaging/installer/UniStation.nsi', 'packaging/installer/config.json',
        'packaging/installer/USER-GUIDE.md', 'packaging/installer/USER-CHECK.md',
        'packaging/installer/BUILD.md', 'tools/build-installer.py', 'LICENSE']}
    support = {
        'USER-GUIDE.txt': b'\xef\xbb\xbf' + docs['INSTALL.md'],
        'USER-CHECK.txt': b'\xef\xbb\xbf' + (ROOT / 'packaging/installer/USER-CHECK.md').read_bytes(),
        'LICENSE-UniStation.txt': runtime['LICENSE'], 'LICENSE-AxisFlow.txt': axisflow['LICENSE'],
        'NSIS-COPYING.txt': nsis_license,
        'Installer-source.zip': source_zip(own_sources),
        'LICENSES.txt': b'UniStation: GPL-3.0-only\r\n\r\n' + runtime['LICENSE']
            + b'\r\n\r\nAxisFlow: LGPL-2.1-or-later\r\n\r\n' + axisflow['LICENSE'],
    }
    output = args.output_dir.resolve()
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
    command = [str(compiler), '/V3', '/NOCD', '/INPUTCHARSET', 'UTF8',
               '/DVERSION=' + config['version'], '/DFILEVERSION=' + config['file_version'],
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
                'product_runtime_unchanged': 45, 'axisflow_runtime_unchanged': 34,
                'installer_executed': False, 'freecad_gui_or_tests_run': False}
    (output / 'BUILD-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    exe.with_suffix('.exe.sha256').write_text(f"{manifest['exe_sha256']}  {exe.name}\n", encoding='ascii')
    print(json.dumps({k: manifest[k] for k in ['version', 'exe', 'exe_bytes', 'exe_sha256',
                                             'product_runtime_unchanged', 'axisflow_runtime_unchanged']}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Installer build failed: {exc}', file=sys.stderr)
        sys.exit(1)
