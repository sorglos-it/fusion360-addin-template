# fusion360-addin-template

[![Fusion 360](https://img.shields.io/badge/Autodesk-Fusion%20360-F60?logo=autodesk&logoColor=white)](#start-in-3-steps)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-0078D6?logo=windows&logoColor=white)](#start-in-3-steps)
[![Languages](https://img.shields.io/badge/UI-DE%20%7C%20EN%20%7C%20ES%20%7C%20FR%20%7C%20IT-4c1.svg)](#language-files)
[![Dependencies](https://img.shields.io/badge/dependencies-none-4c1.svg)](#start-in-3-steps)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Donate](https://img.shields.io/badge/Donate-PayPal-00457C.svg?logo=paypal)](https://www.paypal.com/donate/?hosted_button_id=6CDEVZGJWTNQQ)

A starting point for your own **Fusion 360 add-in**. One command creates a working add-in with a translated
interface, live preview, input checks and an offline test — so the first thing you write is your own geometry, not
boilerplate.

| Folder | Purpose | Language | Start | Build |
|---|---|---|---|---|
| `apps/desktop/AddInTemplate` | the template: a demo command plus the shared machinery every new add-in gets | Python 3 (the one inside Fusion) | `python tools/new_addin.py MyAddIn --install`, then *Run* in Fusion | – (runs as is) |

## Start in 3 steps

1. You need Autodesk Fusion 360 (Windows or macOS) and, for the tools, Python 3 — the add-in itself only uses what
   Fusion brings. Download or clone this repository.
2. In the repository folder run `python tools/new_addin.py MyAddIn --install` — it creates the add-in *MyAddIn* straight
   in Fusion's add-ins folder.
3. In Fusion: **Utilities → ADD-INS → Add-Ins**, select *MyAddIn*, tick *Run on Startup*, press **Run**. The button
   sits on the **SKETCH** tab: click a sketch line, press it — a small tick at the line's midpoint proves that
   selection, preview, validation and translation all work.

Just want to see it run? Download the latest `AddInTemplate-*.zip` from
**[Releases](https://github.com/sorglos-it/fusion360-addin-template/releases)** and unpack it into Fusion's add-ins
folder — that is the template itself, installable. The tools are only in the repository.

Extracted from [fusion360-dovetail](https://github.com/sorglos-it/fusion360-dovetail) and used to build
[fusion360-sketch-grid](https://github.com/sorglos-it/fusion360-sketch-grid).

## Create an add-in

```bash
python tools/new_addin.py MyAddIn --install
```

It copies the template, renames the folder, the entry point, the core module, the icon folder and the command id,
and writes a fresh GUID into the manifest. The name may contain letters and digits only.

| Flag | Effect |
|---|---|
| `--install` | create it straight in Fusion's add-ins folder |
| `--out DIR` | create it somewhere else (default: next to this repository) |
| `--author NAME` | fill the manifest's author field |
| `--prefix STR` | prefix for the command id, default `thw` — make it yours |
| `--force` | overwrite an existing folder of that name |

Fusion's add-ins folder — copy an add-in made with `--out` there:

| OS | Path |
|---|---|
| Windows | `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\` |
| macOS | `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/` |

What you get:

```
MyAddIn/
  MyAddIn.py            entry point - your code goes here
  myaddin_core.py       the shared machinery, renamed so it cannot clash
  MyAddIn.manifest      what Fusion reads, with a fresh GUID
  lang/
    en.xml              the reference: every key exists here
    de.xml es.xml fr.xml it.xml
  resources/
    MyAddIn/            16x16.png 32x32.png 64x64.png
```

## Your code

`MyAddIn.py` is split by two markers. Above `CONFIGURE` is module loading you can ignore. Between `CONFIGURE` and
`END OF TEMPLATE` is yours:

| Piece | What it is for |
|---|---|
| `CMD_ID` | Unique across every installed add-in. A collision silently hijacks the other one's button. |
| `WORKSPACE_ID`, `PANEL_IDS` | Where the button goes. Panels are tried in order, the first existing one wins. |
| `read_inputs()` | Reads every value from the dialog once, so execute, preview and validate see the same numbers. |
| `validate()` | Raise `fail('err.key')` for anything the user has to fix — OK is disabled and the dialog says why, in the user's language. |
| `build_result()` | Does the work. Everything is validated by the time it runs. |
| `build_inputs()` | Lays out the dialog. |
| `remember()` | Keeps settings for the next use in this session. |
| `on_input_changed()` | Enables, disables or adjusts one field from another. |
| `core.display_name()` | Puts the manifest version in brackets after the command name — one place to raise it. |

Below `END OF TEMPLATE` sit the four event handlers and `run`/`stop`. They call the functions above and normally need
no editing. The demo command only proves the wiring — replace it as soon as it has done its job.

## Language files

The interface language follows **Preferences → General → User Language** in Fusion, then the system language, then
English. The texts live in `lang/<code>.xml`:

```xml
<string key="in.length">Length</string>
```

`en.xml` is the reference: every key exists there, and a key missing from another file falls back to it. To add a
language, copy `en.xml`, translate the values, name it after the two-letter code and add the code to
`SUPPORTED_LANGUAGES` and `FUSION_LANGUAGE_MAP` in the core module. Placeholders like `{0}` must survive translation —
the check below tests that for every file. Identifiers, comments and keys stay English, so a translator never has to
open a `.py` file.

## Check and icons

Check an add-in without starting Fusion — manifest, GUID, command id, language files, icons:

```bash
python apps/desktop/tests/test_addin.py                    # the template itself
python apps/desktop/tests/test_addin.py --path ../MyAddIn  # an add-in next to this repository
```

For one made with `--install`, give its folder in Fusion's add-ins folder to `--path`.

Draw the toolbar icons (16, 32 and 64 px) from the polygons in the `SHAPES` list of `tools/make_icon.py`:

```bash
python tools/make_icon.py                            # the template's placeholder
python tools/make_icon.py --root .. --addin MyAddIn  # an add-in next to this repository
```

The shipped glyph — corner brackets and a diagonal — is an obvious placeholder on purpose, so an unreplaced icon is
easy to spot. Everything uses the Python standard library only.

## Notes & caveats

- **Fusion caches modules.** An edited helper keeps its old version until Fusion restarts. The entry point drops the
  core module from `sys.modules` before importing it, so *stop, run* is enough. Give every further module you add the
  same treatment.
- **Keep the renamed core module.** `sys.modules` is shared by all add-ins. Two add-ins importing `addin_core` would
  share whichever loaded first. The scaffolder renames it to `<name>_core.py` — keep it that way.
- **Fusion holds handlers weakly.** A handler Python no longer references is collected and its event stops firing,
  without an error. Register every handler through `HandlerRegistry`.
- **`executePreview` runs on every keystroke** and sees half-typed values, so it swallows errors on purpose.
  `validateInputs` tells the user what is wrong — do not move that logic into the preview.
- **Deleting the selected entity during the preview can invalidate the selection.** If your command replaces what it
  was given, do that in `execute`.
- **Panel ids move between Fusion versions.** That is why `PANEL_IDS` is a list and `find_panel` falls back to a
  global lookup.
- **Lengths are in centimetres**, Fusion's internal unit, whatever a value input shows: `createByReal(1.0)` shown in
  `mm` reads 10 mm.
- **Reset `isComputeDeferred` in a `finally`.** An error while it is set leaves a sketch that no longer updates.

## License

MIT — see [LICENSE](LICENSE). © 2026 Thomas Weirich.

## Donate via PayPal

If this template saved you an afternoon, a donation supports further development. Thank you!

**[➡️ Donate via PayPal](https://www.paypal.com/donate/?hosted_button_id=6CDEVZGJWTNQQ)**
