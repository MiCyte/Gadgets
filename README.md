# MiCyte gadgets

The catalogue of gadgets for [MiCyte](https://github.com/MiCyte/MiCyte): one declaration
per gadget, and `catalogue.json` listing them with their digests. micyte.com's
[Gadgets page](https://micyte.com/gadgets) is built from this repository, and so is the
portal's marketplace.

A gadget is a decision about what ships together: an **app** (a hub over its own tools,
usually with a sandbox of its own) or an **extension** (it fills a port an app employs,
and ships no tools and no screen).

## What a declaration is, and what it can do to you

A declaration **enables tools; it never adds code.** Every tool it names is already in the
MiCyte package your instance runs. Installing from a declaration makes the instance show
those tools and creates the blank documents they need. It cannot introduce a tool your
build does not have, and it grants nothing: what a tool may write is decided by your
instance's own grants, which deny by default.

There is no package archive here, deliberately. A file an instance unpacks and runs is a
way to ship code, and shipping code without a signing story is the half that cannot be
made safe on its own. The catalogue keeps a `package` slot for the day there is one; today
it is `null` for every gadget.

## Layout

```
catalogue.json                 the list; derived from declarations/, never edited by hand
declarations/<id>-<version>.micytepkg.json
scripts/build_catalogue.py     writes catalogue.json; --check refuses drift (stdlib only)
```

## The catalogue format: `micyte.gadgets.catalogue.v1`

```json
{
  "schema": "micyte.gadgets.catalogue.v1",
  "repository": "https://github.com/MiCyte/Gadgets",
  "micyte": { "version": "0.6.0", "source": "https://github.com/MiCyte/MiCyte" },
  "gadgets": [
    {
      "id": "quiar",
      "kind": "app",
      "label": "Quiar – Freelancer",
      "version": "2.4.0",
      "summary": "…",
      "icon": "quiar",
      "micyte_version": "0.6.0",
      "tools": ["quiar", "job_manager", "…"],
      "hub_tool": "quiar",
      "requires": {
        "sandbox": { "needed": true, "namespace": "registrar" },
        "documents": ["job_log", "contacts", "…"],
        "archetypes": ["job_event", "…"],
        "sources": ["registrar/legal_entity"],
        "fields": ["msn_id", "…"]
      },
      "ports": { "declares": [], "fills": [], "services": [] },
      "declaration": {
        "path": "declarations/quiar-2.4.0.micytepkg.json",
        "schema": "micyte.gadget.declaration.v1",
        "bytes": 4971,
        "sha256": "<hex: sha256 of the file's bytes>",
        "digest": "sha256:<the declaration digest an instance compares>"
      },
      "package": null
    }
  ]
}
```

| field | meaning |
|---|---|
| `schema` | the format's name and version. A reader refuses a schema it does not know; a change that removes or renames a field is a new version (`…v2`), a new optional field is not. |
| `repository` | where this catalogue lives. A declaration's source is `<repository>/blob/main/<declaration.path>`. |
| `micyte.version` | the newest MiCyte release any listed declaration was published from. |
| `gadgets[]` | one entry per gadget, apps first, then by `id`. One version per gadget. |
| `kind` | `app` (it names tools) or `extension` (it names none, and fills ports). |
| `micyte_version` | the MiCyte release this declaration was published from; its tools are in that build. |
| `requires.sandbox` | `needed`: whether the gadget keeps its records in a sandbox of its own. `namespace`: the numbering that sandbox uses; empty means inherited from the instance's own anchor. |
| `requires.documents` | the documents an install creates (blank). |
| `requires.archetypes` | the shapes those documents take. |
| `requires.sources` | documents the gadget reads from elsewhere, as `sandbox/document`. |
| `requires.fields` | the fields its tools resolve. |
| `ports` | ports it `declares` (seams its tools call through), ports it `fills` (as an extension), and the outside `services` either may reach once an operator binds and grants them. Installing binds nothing. |
| `declaration.sha256` | sha256 over the file's exact bytes. Check a download with `sha256sum`. |
| `declaration.digest` | the declaration digest (`micyte.tools._packages_manifest.declaration_digest`): sha256 over the canonical declaration, excluding version, label, summary, icon and publishable. It is what an instance compares when it pulls the same declaration over `GET /__mss/public/packages`. |
| `package` | `null`. Reserved for a signed archive: `{ "path", "sha256", "signature" }`. |

Everything in an entry except `declaration.path`, `bytes` and `sha256` is read from the
declaration itself, so the full record is always the file.

## Checking what you downloaded

```sh
sha256sum quiar-2.4.0.micytepkg.json      # equals declaration.sha256
python3 scripts/build_catalogue.py --check # every file, every digest, in this checkout
```

## Publishing a new version

Declarations are written by MiCyte's own build, never by hand:

```sh
# in a MiCyte checkout
python3 fnd_app/scripts/export_micyte_gadget_declarations.py --write --dir <this repo>/declarations
# here
python3 scripts/build_catalogue.py
python3 scripts/build_catalogue.py --check
git add -A && git commit -m "Gadgets for MiCyte <version>"
```

The exporter removes the declaration of a version it no longer ships, so a withdrawn
version leaves the catalogue in the same commit.

## Licence

AGPL-3.0, as MiCyte.
