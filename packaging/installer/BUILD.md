# Building a Windows installer candidate

Use Python 3.11+ and portable NSIS 3.12. Building does not run FreeCAD, setup,
uninstall, tests or an AxisFlow compiler.

1. Use the checkout intended for the new candidate. Set matching `version`
   values in `package.xml` and `packaging/installer/config.json`. Alpha.12 uses
   `0.1.0-alpha.12` in both files and Windows file version `0.1.0.12`.
2. Obtain NSIS 3.12, for example from https://distfiles.macports.org/nsis/nsis-3.12.zip
   (2,362,938 bytes; SHA-256
   `56581f90db321581c5381193d796fffcf2d24b2f8fed2160a6c6a3baa67f2c4f`).
3. Download the pinned earlier full archive:
   https://github.com/LeonidWiebe/UniStation/releases/download/v0.1.0-alpha.2/UniStation-0.1.0-alpha.2-Windows-FC1.1-candidate.zip
4. Run from the source checkout:

   ```text
   python tools/build-installer.py --makensis C:/projects/ustatic/research/installer-toolchain/nsis-3.12/makensis.exe --payload-archive C:/projects/ustatic/research/installer-inputs/UniStation-0.1.0-alpha.2-Windows-FC1.1-candidate.zip --output-dir C:/projects/ustatic/dist/installer-build-next
   ```

Use an unused output directory. The pinned
archive is available under `C:/projects/ustatic/research/installer-inputs/`. Pass its path with
`--payload-archive`.

Alpha.12 is the published release. Its existing EXE packages the accepted
Line continuation and circular Wire segments. The alpha.11 EXE and manifest
are retained under `C:/projects/ustatic/dist/0.1.0-alpha.11/` with its manual
installer acceptance. Each candidate directory records its own EXE, manifest
and bundled source snapshot.

UniStation comes from the current UniStation/ source tree. Only AxisFlow is
read from the hash-pinned alpha.2 archive, preserving all 34 component files,
the accepted binary and full corresponding sources/licenses. The old archive's
UniStation code is not used. Python/XML are parsed without product imports.
Metadata is adapted from checkout layout to the installed flat module.

Output includes EXE, SHA-256, compile.log, BUILD-MANIFEST.json and staging files.
The native Launch-UniStation.exe is compiled separately; launcher-compile.log
records its build. Support includes it and the startup macro. Installer sources
include both NSIS scripts, FreeCAD.nsh, the macro template and both Windows ICOs.
Each ICO contains 14 sizes from 16 to 256 px. NSIS uses `unistation.ico` for the
launcher and uninstaller. `unistation-setup.ico` adds a download badge from 32 px.
The builder derives the supported FreeCAD range from matching package.xml/config
values and inserts it into setup and the macro. Setup handles FreeCAD detection
and version probing at runtime.
Installed metadata uses the next patch (1.1.5) as an exclusive upper boundary:
FreeCAD appends a revision component before comparing metadata versions, so a
plain upper bound of 1.1.4 would exclude 1.1.4.<revision>. Setup and the startup
macro still enforce the exact allowed range 1.1.1–1.1.4. The manifest records
both bounds. This adaptation only affects generated installed package.xml.
The manifest records per-file runtime and complete payload hashes. Use a fresh
output directory when the inventory changes; no old tree is deleted automatically.
Do not overwrite a published version's artifacts. Compilation timestamps are
not claimed reproducible. Installer-source.zip includes runtime and packaging
source inputs, with the same pinned external AxisFlow input.

For static inspection use 7-Zip to extract the EXE without executing it, compare
all payload files with the manifest, and inspect the asInvoker PE manifest.
This does not replace explicit runtime checks of setup/uninstall/restore.

The uninstaller must retain its initial $INSTDIR as the original state directory.
NSIS runs a temporary copy of the uninstaller; $EXEDIR refers to that copy.
Ownership/root checks still run against the original state.ini before any
component changes. This corrects the alpha.5 startup failure during uninstall.
