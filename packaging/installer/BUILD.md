# Building the alpha.4 Windows installer

Use Python 3.11+ and portable NSIS 3.12. Building does not run FreeCAD, setup,
uninstall, tests or an AxisFlow compiler.

1. Check out this release's complete source snapshot.
2. Obtain NSIS 3.12, for example from https://distfiles.macports.org/nsis/nsis-3.12.zip
   (2,362,938 bytes; SHA-256
   `56581f90db321581c5381193d796fffcf2d24b2f8fed2160a6c6a3baa67f2c4f`).
3. Download the pinned earlier full archive:
   https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.2/UniStation-0.1.0-alpha.2-Windows-FC1.1-candidate.zip
4. Run from the source checkout:

   ```text
   python tools/build-installer.py --makensis C:/tools/nsis-3.12/makensis.exe --payload-archive C:/downloads/UniStation-0.1.0-alpha.2-Windows-FC1.1-candidate.zip --output-dir dist/alpha4-build
   ```

UniStation comes from the current UniStation/ source tree. Only AxisFlow is
read from the hash-pinned alpha.2 archive, preserving all 34 component files,
the accepted binary and full corresponding sources/licenses. The old archive's
UniStation code is not used. Python/XML are parsed without product imports.
Metadata is adapted from checkout layout to the installed flat module.

Output includes EXE, SHA-256, compile.log, BUILD-MANIFEST.json and staging files.
The manifest records per-file runtime and complete payload hashes. Use a fresh
output directory when the inventory changes; no old tree is deleted automatically.
Do not overwrite a published version's artifacts. Compilation timestamps are
not claimed reproducible. Installer-source.zip includes runtime and packaging
source inputs, with the same pinned external AxisFlow input.

For static inspection use 7-Zip to extract the EXE without executing it, compare
all payload files with the manifest, and inspect the asInvoker PE manifest.
This does not replace explicit runtime checks of setup/uninstall/restore.
