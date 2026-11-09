"""Run the axisflow-core unit classes listed in tests/current_scope.json.

The catalog is an allowlist. Deferred classes are never added after a load
error, and a class that is absent from the catalog is a failure rather than
an automatic addition. This is not unittest discover.
"""
import argparse
import ast
import hashlib
import importlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "tests" / "current_scope.json"


def select_axisflow_cases(registered_names, catalog, requested):
    """Return registered Qt names allowed for this run, in registration order."""
    if not isinstance(catalog, dict):
        raise ValueError("current_scope.json must contain an object")
    if catalog.get("schema_version") != 1:
        raise ValueError("Unsupported current_scope schema_version")
    if catalog.get("scope") != "axisflow-core":
        raise ValueError("current_scope scope must be axisflow-core")
    reason = catalog.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("current_scope reason is missing")
    included = catalog.get("included_qt")
    deferred_items = catalog.get("deferred_qt")
    if not isinstance(included, list) or not included:
        raise ValueError("included_qt must be a non-empty list")
    if not all(isinstance(name, str) and name for name in included):
        raise ValueError("included_qt names must be non-empty strings")
    if len(included) != len(set(included)):
        raise ValueError("included_qt contains duplicate names")
    if not isinstance(deferred_items, list):
        raise ValueError("deferred_qt must be a list")
    deferred = []
    for item in deferred_items:
        if not isinstance(item, dict):
            raise ValueError("deferred_qt entries must be objects")
        name = item.get("name")
        item_reason = item.get("reason")
        if not isinstance(name, str) or not name:
            raise ValueError("deferred_qt name is missing")
        if not isinstance(item_reason, str) or "deferred_by_scope" not in item_reason:
            raise ValueError("deferred_qt reason must state deferred_by_scope")
        if name in deferred:
            raise ValueError("deferred_qt contains duplicate names")
        deferred.append(name)
    if set(included) & set(deferred):
        raise ValueError("A Qt case is both included and deferred")
    registered = list(registered_names)
    if not registered or len(registered) != len(set(registered)):
        raise ValueError("Registered Qt cases are missing or duplicated")
    covered = set(included) | set(deferred)
    if covered != set(registered) or len(included) + len(deferred) != len(registered):
        raise ValueError("current_scope.json does not cover the registered Qt cases")
    _require_unit_lists(catalog)
    if requested:
        wanted = requested.split(",")
        registered_set = set(registered)
        deferred_set = set(deferred)
        unknown = sorted({name for name in wanted if name not in registered_set})
        blocked = sorted({name for name in wanted if name in deferred_set})
        if unknown or blocked:
            parts = []
            if unknown:
                parts.append("Unknown GUI cases: " + repr(unknown))
            if blocked:
                parts.append(
                    "Deferred GUI cases are outside axisflow-core: " + repr(blocked))
            raise ValueError("; ".join(parts))
        wanted_set = set(wanted)
        return [name for name in registered if name in wanted_set]
    included_set = set(included)
    return [name for name in registered if name in included_set]


def _class_name(value, label):
    if not isinstance(value, str) or value.count(".") != 1:
        raise ValueError(label + " must be module.Class")
    module_name, class_name = value.split(".")
    if not module_name or not class_name:
        raise ValueError(label + " must be module.Class")
    return value


def _require_unit_lists(catalog):
    included = catalog.get("included_unit")
    deferred_items = catalog.get("deferred_unit")
    if not isinstance(included, list) or not included:
        raise ValueError("included_unit must be a non-empty list")
    names = [_class_name(value, "included_unit") for value in included]
    if len(names) != len(set(names)):
        raise ValueError("included_unit contains duplicate classes")
    if not isinstance(deferred_items, list) or not deferred_items:
        raise ValueError("deferred_unit must be a non-empty list")
    deferred = []
    for item in deferred_items:
        if not isinstance(item, dict):
            raise ValueError("deferred_unit entries must be objects")
        class_name = _class_name(item.get("class"), "deferred_unit")
        item_reason = item.get("reason")
        if not isinstance(item_reason, str) or "deferred_by_scope" not in item_reason:
            raise ValueError("deferred_unit reason must state deferred_by_scope")
        if class_name in deferred:
            raise ValueError("deferred_unit contains duplicate classes")
        deferred.append(class_name)
    if set(names) & set(deferred):
        raise ValueError("A unit class is both included and deferred")


def source_testcase_classes():
    """TestCase classes declared in tests/test_*.py, without importing them."""
    found = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(base.attr)
            if "TestCase" in bases:
                found.append(path.stem + "." + node.name)
    if len(found) != len(set(found)):
        raise ValueError("Duplicate TestCase class names in tests/test_*.py")
    return found


def registered_qt_names():
    """Case names from the macro registration, without importing FreeCAD."""
    path = ROOT / "tests" / "qt_input.FCMacro"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    run = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "run")
    names = []
    for node in ast.walk(run):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id in {"cases", "settings_cases"}
                   for target in node.targets):
            continue
        source = node.value
        if isinstance(source, ast.BinOp) and isinstance(source.right, ast.List):
            elements = source.right.elts
        elif isinstance(source, ast.List):
            elements = source.elts
        else:
            continue
        for element in elements:
            names.append(element.elts[0].value)
    return names


def load_catalog():
    try:
        payload = CATALOG_PATH.read_bytes()
        catalog = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "current_scope.json is required and could not be read: " + str(exc)
        ) from exc
    select_axisflow_cases(registered_qt_names(), catalog, "")
    declared = set(catalog["included_unit"]) | {
        item["class"] for item in catalog["deferred_unit"]
    }
    actual = set(source_testcase_classes())
    if declared != actual:
        missing = sorted(actual - declared)
        extra = sorted(declared - actual)
        raise ValueError(
            "current_scope.json unit classes do not match the sources: "
            + repr({"missing": missing, "extra": extra})
        )
    return catalog, hashlib.sha256(payload).hexdigest()


def _iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_tests(item)
        else:
            yield item


def load_included_suite(catalog):
    for entry in (ROOT / "UniStation", ROOT / "tests"):
        entry_text = str(entry)
        if entry_text not in sys.path:
            sys.path.insert(0, entry_text)
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for qualified in catalog["included_unit"]:
        module_name, class_name = qualified.split(".")
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        if not isinstance(cls, type) or not issubclass(cls, unittest.TestCase):
            raise ValueError(qualified + " is not a unittest.TestCase")
        suite.addTest(loader.loadTestsFromTestCase(cls))
    tests = list(_iter_tests(suite))
    if not tests:
        raise ValueError("included_unit produced no tests")
    identifiers = [test.id() for test in tests]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("included_unit produced duplicate test ids")
    deferred_prefix = tuple(item["class"] + "." for item in catalog["deferred_unit"])
    leaked = [identifier for identifier in identifiers if identifier.startswith(deferred_prefix)]
    if leaked:
        raise ValueError("Deferred tests were loaded: " + repr(leaked))
    return suite, identifiers


def _write_report(output, payload):
    if output is None:
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with path.open("xb") as handle:
        handle.write(text.encode("utf-8"))


def _base_report(catalog, digest, status):
    return {
        "schema_version": 1,
        "scope": catalog.get("scope") if isinstance(catalog, dict) else None,
        "catalog_sha256": digest,
        "status": status,
        "counts": {"tests": 0, "failures": 0, "errors": 0, "skipped": 0},
        "executed_ids": [],
        "included_unit": catalog.get("included_unit") if isinstance(catalog, dict) else [],
        "deferred_unit": catalog.get("deferred_unit") if isinstance(catalog, dict) else [],
    }


def run(argv):
    parser = argparse.ArgumentParser(description="Run axisflow-core unit tests from current_scope.json")
    parser.add_argument("--list", action="store_true", help="print included test ids without running them")
    parser.add_argument("--output", help="write a new JSON report; an existing file is left untouched")
    args = parser.parse_args(argv)
    if args.list and args.output:
        print("--list does not write a run report", file=sys.stderr)
        return 1
    if args.output and Path(args.output).exists():
        print("Refusing to overwrite " + str(args.output), file=sys.stderr)
        return 1
    catalog = None
    digest = None
    try:
        catalog, digest = load_catalog()
        suite, identifiers = load_included_suite(catalog)
        if args.list:
            for identifier in identifiers:
                print(identifier)
            return 0
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        skipped = len(getattr(result, "skipped", []))
        status = "passed" if (
            result.wasSuccessful()
            and not result.failures
            and not result.errors
            and skipped == 0
            and result.testsRun == len(identifiers)
        ) else "failed"
        report = _base_report(catalog, digest, status)
        report["counts"] = {
            "tests": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": skipped,
        }
        report["executed_ids"] = identifiers
        _write_report(args.output, report)
        return 0 if status == "passed" else 1
    except Exception as exc:
        if args.list:
            print(type(exc).__name__ + ": " + str(exc), file=sys.stderr)
            return 1
        report = _base_report(catalog if isinstance(catalog, dict) else {}, digest, "failed")
        report["error"] = type(exc).__name__ + ": " + str(exc)
        try:
            _write_report(args.output, report)
        except Exception as write_error:
            print(type(write_error).__name__ + ": " + str(write_error), file=sys.stderr)
        print(report["error"], file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
