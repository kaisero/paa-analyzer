"""Generate the mechanical sections of .agents/context/ docs.

Each registered block is rendered from the live code (AST) into marker-delimited
regions of a doc, so it cannot rot. ``--check`` regenerates to a buffer and exits
1 if any doc is out of date — the freshness gate runs this. Pure stdlib: the
generator never imports or executes repo code, so `nox -s context` needs no venv.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONTEXT = REPO / ".agents" / "context"

# (doc filename, block kind, list of repo-root-relative glob patterns).
# One owner per source file: paa_analyzer/ (parsing library + CLI) belongs to
# parsers.md; backend/ (FastAPI app) belongs to backend.md. backend/*.py is
# non-recursive on purpose — api/ is inventoried by the route-table block and
# tests/ and models/ are covered by narrative, not generated blocks.
BLOCKS: list[tuple[str, str, list[str]]] = [
    ("parsers.md", "module-map", ["paa_analyzer/*.py"]),
    ("parsers.md", "api", ["paa_analyzer/parsers.py", "paa_analyzer/parsers_win.py"]),
    ("parsers.md", "taxonomy-table", ["paa_analyzer/taxonomy.py"]),
    ("backend.md", "module-map", ["backend/*.py"]),
    ("backend.md", "api", ["backend/store.py", "backend/pipeline.py", "backend/config.py"]),
    ("backend.md", "route-table", ["backend/api/*.py"]),
]


def expand(patterns: list[str]) -> list[Path]:
    """Expand glob patterns (repo-root-relative) to a sorted, deduped .py file list."""
    found: set[Path] = set()
    for pat in patterns:
        found.update(p for p in REPO.glob(pat) if p.suffix == ".py" and p.is_file())
    return sorted(found)


def _first_doc_line(node: ast.AST) -> str:
    doc = (
        ast.get_docstring(node)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        else None
    )
    return doc.splitlines()[0].strip() if doc else ""


def module_map(files: list[Path]) -> str:
    rows = []
    for path in files:
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text())
        doc = _first_doc_line(tree)
        rows.append(f"- `{path.name}` — {doc}" if doc else f"- `{path.name}`")
    return "\n".join(rows)


def _signature(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    a = fn.args
    names = [arg.arg for arg in (*a.posonlyargs, *a.args, *a.kwonlyargs)]
    return f"{fn.name}({', '.join(names)})"


def public_api(files: list[Path]) -> str:
    out: list[str] = []
    for path in files:
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text())
        items: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                doc = _first_doc_line(node)
                name = node.name
                line = f"  - class `{name}` — {doc}" if doc else f"  - class `{name}`"
                items.append(line)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                doc = _first_doc_line(node)
                sig = _signature(node)
                line = f"  - `{sig}` — {doc}" if doc else f"  - `{sig}`"
                items.append(line)
        if items:
            out.append(f"- `{path.name}`")
            out.extend(items)
    return "\n".join(out)


# Field order of paa_analyzer/taxonomy.py::FileMeta — read via AST, never imported.
_FILEMETA_FIELDS = ("data_type", "module", "component", "parser")


def _filemeta_fields(value: ast.expr) -> list[str] | None:
    """Extract the four FileMeta field values from a ``FileMeta(...)`` call node.

    Returns None (skip the row) for anything that is not a FileMeta call with
    four literal string fields — e.g. taxonomy dicts holding tuples or strings.
    """
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
    if name != "FileMeta":
        return None
    fields: dict[str, str] = {}
    try:
        for field, arg in zip(_FILEMETA_FIELDS, value.args, strict=False):
            fields[field] = str(ast.literal_eval(arg))
        for kw in value.keywords:
            if kw.arg in _FILEMETA_FIELDS:
                fields[kw.arg] = str(ast.literal_eval(kw.value))
    except ValueError:
        return None
    if set(fields) != set(_FILEMETA_FIELDS):
        return None
    return [fields[f] for f in _FILEMETA_FIELDS]


def taxonomy_table(files: list[Path]) -> str:
    """Render the FileMeta routing dicts of taxonomy.py as markdown tables.

    One table per module-level dict whose values are ``FileMeta(...)`` calls;
    the dict's variable name is the group heading. Non-FileMeta dicts
    (LOG_SOURCES, PACLI_COMMAND_MAP, ...) contribute no rows and are omitted.
    """
    out: list[str] = []
    for path in files:
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                group, value = node.targets[0].id, node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                group, value = node.target.id, node.value
            else:
                continue
            if not isinstance(value, ast.Dict):
                continue
            rows: list[str] = []
            for key, val in zip(value.keys, value.values, strict=False):
                if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                    continue
                fields = _filemeta_fields(val)
                if fields is None:
                    continue
                rows.append("| `{}` | {} |".format(key.value, " | ".join(fields)))
            if rows:
                if out:
                    out.append("")
                out.append(f"**`{group}`**")
                out.append("")
                out.append("| File | data_type | module | component | parser |")
                out.append("| --- | --- | --- | --- | --- |")
                out.extend(rows)
    return "\n".join(out)


_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete"})


def _router_prefix(tree: ast.Module) -> str:
    """Return the literal ``prefix=`` kwarg of the module's APIRouter(...) call, or ""."""
    for node in tree.body:
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == "APIRouter":
            for kw in value.keywords:
                if kw.arg == "prefix":
                    try:
                        return str(ast.literal_eval(kw.value))
                    except ValueError:
                        return ""
    return ""


def route_table(files: list[Path]) -> str:
    """Render FastAPI ``@router.<method>("<path>")`` handlers as a markdown table.

    Paths are the router's own ``prefix`` + the decorator path; any app-level
    ``include_router(..., prefix=...)`` mount (e.g. ``/api/v1``) is NOT included.
    Rows are sorted by path, then method.
    """
    rows: list[tuple[str, str, str, str]] = []
    for path in files:
        tree = ast.parse(path.read_text())
        prefix = _router_prefix(tree)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)):
                    continue
                if not (isinstance(dec.func.value, ast.Name) and dec.func.value.id == "router"):
                    continue
                method = dec.func.attr
                if method not in _HTTP_METHODS or not dec.args:
                    continue
                first = dec.args[0]
                if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
                    continue
                rows.append((prefix + first.value, method.upper(), node.name, _first_doc_line(node)))
    if not rows:
        return ""
    lines = ["| Method | Path | Handler | Summary |", "| --- | --- | --- | --- |"]
    lines.extend(f"| {method} | `{route}` | `{handler}` | {doc} |" for route, method, handler, doc in sorted(rows))
    return "\n".join(lines)


RENDERERS = {
    "module-map": module_map,
    "api": public_api,
    "taxonomy-table": taxonomy_table,
    "route-table": route_table,
}


def render(kind: str, files: list[Path]) -> str:
    if kind not in RENDERERS:
        raise ValueError(f"unknown block kind {kind!r}; known: {sorted(RENDERERS)}")
    return RENDERERS[kind](files)


def inject(text: str, kind: str, content: str) -> str:
    start, end = f"<!-- GENERATED:{kind} -->", f"<!-- /GENERATED:{kind} -->"
    i, j = text.find(start), text.find(end)
    if i == -1 or j == -1 or j < i + len(start):
        raise ValueError(f"markers for {kind!r} out of order or not found")
    return text[: i + len(start)] + "\n" + content + "\n" + text[j:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail if any block is stale")
    ns = ap.parse_args(argv)
    stale: list[str] = []
    for doc_name, kind, patterns in BLOCKS:
        doc = CONTEXT / doc_name
        try:
            files = expand(patterns)
            text = doc.read_text()
            updated = inject(text, kind, render(kind, files))
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if ns.check:
            if updated != text:
                stale.append(f"{doc_name}:{kind}")
        else:
            doc.write_text(updated)
    if ns.check and stale:
        print("stale generated blocks: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
