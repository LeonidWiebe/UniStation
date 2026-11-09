"""Extract UniStation Qt strings without importing the workbench; optionally run lrelease."""

import argparse
import ast
from collections import defaultdict
from pathlib import Path
import os
import subprocess
import xml.etree.ElementTree as ET


def extract(root):
    messages = defaultdict(list)
    directory = root / "UniStation" / "unistation" / "translations"
    for file in sorted((root / "UniStation").rglob("*.py")):
        tree = ast.parse(file.read_text(encoding="utf-8-sig"), filename=str(file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            name, args, context, source = node.func.id, node.args, "UniStation", None
            if name == "QT_TRANSLATE_NOOP" and len(args) >= 2:
                if isinstance(args[0], ast.Constant) and isinstance(args[0].value, str):
                    context, source = args[0].value, args[1]
            elif name in ("tr", "translated_label", "translated_button") and args:
                source = args[0]
            elif name == "bind" and len(args) >= 3:
                source = args[2]
            elif name == "translated_dialog_button" and len(args) >= 2:
                source = args[1]
            if isinstance(source, ast.Constant) and isinstance(source.value, str) and source.value:
                relative = Path(os.path.relpath(file, directory)).as_posix()
                location = (relative, str(node.lineno))
                if location not in messages[(context, source.value)]:
                    messages[(context, source.value)].append(location)
    return messages


def update(path, language, messages):
    previous = {}
    if path.exists():
        for context in ET.parse(path).getroot().findall("context"):
            for message in context.findall("message"):
                translation = message.find("translation")
                previous[(context.findtext("name"), message.findtext("source"))] = (
                    translation.text or "", translation.get("type"))
    document = ET.Element("TS", version="2.1", language=language, sourcelanguage="en")
    contexts = {}
    for (context, source), locations in sorted(messages.items()):
        if context not in contexts:
            contexts[context] = ET.SubElement(document, "context")
            ET.SubElement(contexts[context], "name").text = context
        message = ET.SubElement(contexts[context], "message")
        for file, line in locations:
            ET.SubElement(message, "location", filename=file, line=line)
        ET.SubElement(message, "source").text = source
        target = ET.SubElement(message, "translation")
        text, status = previous.get((context, source), ("", "unfinished"))
        if language == "en":
            target.text = source
        else:
            target.text = text
            if status:
                target.set("type", status)
    ET.indent(document, space="  ")
    path.write_bytes(b'<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n'
                     + ET.tostring(document, encoding="utf-8") + b"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lrelease", type=Path, help="Qt lrelease executable; omit to update TS only")
    parser.add_argument("--dll-directory", type=Path, help="Optional Qt dependency directory (portable FreeCAD bin)")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    messages = extract(root)
    directory = root / "UniStation" / "unistation" / "translations"
    directory.mkdir(exist_ok=True)
    environment = os.environ.copy()
    if args.dll_directory:
        environment["PATH"] = str(args.dll_directory.resolve()) + os.pathsep + environment.get("PATH", "")
    for language in ("en", "ru"):
        path = directory / ("UniStation_" + language + ".ts")
        update(path, language, messages)
        if args.lrelease:
            subprocess.run([str(args.lrelease.resolve()), str(path), "-qm", str(path.with_suffix(".qm"))],
                           check=True, env=environment)
    print(f"Updated en/ru catalogs: {len(messages)} messages; no product imports or tests.")


if __name__ == "__main__":
    main()
