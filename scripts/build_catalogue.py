#!/usr/bin/env python3
"""Write catalogue.json from the declarations in declarations/; --check refuses drift.

    python3 scripts/build_catalogue.py           # rewrite catalogue.json
    python3 scripts/build_catalogue.py --check   # exit 1 if catalogue.json is not what the files say

The catalogue is DERIVED. Every value in it is read from a declaration file except two
constants below (where the repository lives, where MiCyte lives), so the catalogue and the
files cannot disagree once this has run, and `--check` is what says they do.

Standard library only: a reader of this repository must be able to check it without
installing MiCyte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECLARATIONS = ROOT / "declarations"
CATALOGUE = ROOT / "catalogue.json"

SCHEMA = "micyte.gadgets.catalogue.v1"
DECLARATION_SCHEMA = "micyte.gadget.declaration.v1"
REPOSITORY = "https://github.com/MiCyte/Gadgets"
MICYTE_SOURCE = "https://github.com/MiCyte/MiCyte"


def _version_key(v: str) -> tuple:
    return tuple(int(p) if p.isdigit() else 0 for p in str(v).split("."))


def _unique(items) -> list[str]:
    out: list[str] = []
    for item in items:
        if item and item not in out:
            out.append(item)
    return out


def entry(path: Path) -> dict:
    raw = path.read_bytes()
    doc = json.loads(raw)
    if doc.get("schema") != DECLARATION_SCHEMA:
        raise SystemExit(f"REFUSED: {path.name} is not a {DECLARATION_SCHEMA} declaration")
    pkg = doc.get("package") or {}
    want = f"{pkg.get('package_id')}-{pkg.get('version')}.micytepkg.json"
    if path.name != want:
        raise SystemExit(f"REFUSED: {path.name} declares {want}; a file is named by id and version")
    if doc.get("digest") != pkg.get("digest"):
        raise SystemExit(f"REFUSED: {path.name} states two different digests")
    req = pkg.get("requires") or {}
    sandbox = pkg.get("app_sandbox") or None
    documents = list(req.get("documents") or []) + list((sandbox or {}).get("documents") or [])
    declares = pkg.get("port_declarations") or []
    fills = pkg.get("port_fills") or []
    tools = list(pkg.get("tools") or [])
    return {
        "id": pkg["package_id"],
        "kind": "app" if tools else "extension",
        "label": pkg.get("label") or pkg["package_id"],
        "version": pkg["version"],
        "summary": pkg.get("summary") or "",
        "icon": pkg.get("icon") or "",
        "micyte_version": doc.get("micyte_version") or "",
        "tools": tools,
        "hub_tool": pkg.get("hub_tool") or "",
        "requires": {
            "sandbox": {"needed": sandbox is not None,
                        "namespace": str((sandbox or {}).get("namespace") or "")},
            "documents": _unique(d.get("name") for d in documents),
            "archetypes": _unique([d.get("archetype") for d in documents]
                                  + list(req.get("archetypes") or [])),
            "sources": _unique(f"{s.get('sandbox')}/{s.get('document')}"
                               for s in req.get("sources") or []),
            "fields": list(req.get("fields") or []),
        },
        "ports": {
            "declares": _unique(p.get("port_id") for p in declares),
            "fills": _unique(p.get("port_id") for p in fills),
            "services": _unique([c.get("service") for p in declares for c in p.get("calls") or []]
                                + [p.get("service") for p in fills]),
        },
        "declaration": {
            "path": f"declarations/{path.name}",
            "schema": DECLARATION_SCHEMA,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "digest": doc["digest"],
        },
        "package": None,
    }


def catalogue() -> dict:
    files = sorted(DECLARATIONS.glob("*.micytepkg.json"))
    if not files:
        raise SystemExit(f"REFUSED: no declarations under {DECLARATIONS}")
    gadgets = [entry(p) for p in files]
    ids = [g["id"] for g in gadgets]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit(f"REFUSED: more than one version declared for {', '.join(dupes)}; "
                         "the catalogue lists one version per gadget")
    gadgets.sort(key=lambda g: (g["kind"] != "app", g["id"]))
    built = max((g["micyte_version"] for g in gadgets), key=_version_key)
    return {
        "schema": SCHEMA,
        "repository": REPOSITORY,
        "micyte": {"version": built, "source": MICYTE_SOURCE},
        "gadgets": gadgets,
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    doc = catalogue()
    count = len(doc["gadgets"])
    wanted = render(doc)
    have = CATALOGUE.read_text(encoding="utf-8") if CATALOGUE.is_file() else ""
    if args.check:
        if have != wanted:
            print("REFUSED: catalogue.json is not what declarations/ says; "
                  "run scripts/build_catalogue.py", file=sys.stderr)
            return 1
        print(f"current: catalogue.json lists {count} gadget(s), sha256 and digest per file")
        return 0
    CATALOGUE.write_text(wanted, encoding="utf-8")
    print(f"wrote catalogue.json ({count} gadget(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
