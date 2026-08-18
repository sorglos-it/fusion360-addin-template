# fusion360-addin-template

[![Fusion 360](https://img.shields.io/badge/Autodesk-Fusion%20360-F60?logo=autodesk&logoColor=white)](#requirements)
[![Type](https://img.shields.io/badge/type-template-0b7285.svg)](#quick-start)
[![Languages](https://img.shields.io/badge/UI-DE%20%7C%20EN%20%7C%20ES%20%7C%20FR%20%7C%20IT-4c1.svg)](#language-files)
[![Dependencies](https://img.shields.io/badge/dependencies-none-4c1.svg)](#requirements)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-0078D6?logo=windows&logoColor=white)](#requirements)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Donate](https://img.shields.io/badge/Donate-PayPal-00457C.svg?logo=paypal)](https://www.paypal.com/donate/?hosted_button_id=6CDEVZGJWTNQQ)

A **starting point for Fusion 360 add-ins**. One command scaffolds a working, installable add-in with a translated interface, live preview, input validation and an offline test harness — so the first thing you write is your own geometry, not another round of boilerplate.

```bash
python tools/new_addin.py MyAddIn --install
```

That produces a folder in Fusion's add-ins directory that runs as-is. Everything you then edit sits between two markers in one file.

Extracted from [fusion360-dovetail](https://github.com/sorglos-it/fusion360-dovetail), and used to build [fusion360-sketch-grid](https://github.com/sorglos-it/fusion360-sketch-grid) — both in production.

## Features

- **Scaffolding in one command** — renames the folder, the entry point, the core module, the icon folder and the command id, and stamps a fresh GUID into the manifest
- **Translated interface out of the box** — German, English, Spanish, French and Italian, picked from the Fusion language setting, in plain XML files
- **No module collisions** — the shared core is renamed per add-in, so two add-ins from this template can be installed side by side
- **Edit-and-reload** — the core module is dropped from `sys.modules` on start, so *stop, run* picks up your changes without restarting Fusion
- **Handlers that stay alive** — a registry holds every handler reference, the single most common reason an add-in half-works
- **Validation that explains itself** — errors carry a language-independent key, so `validateInputs` can disable OK and the dialog says why
- **Offline test harness** — stubs `adsk`, imports the add-in and checks the manifest, the command id, the language files and the icons without starting Fusion
- **Version in the dialog** — read from the manifest and shown small in the bottom right corner, so there is one place to bump
- **Generated icons** — 16/32/64 px PNGs from a polygon list, written with `zlib` and `struct`, no imaging library
- **No dependencies** — pure Python standard library, everything ships with Fusion

## Requirements

- Autodesk Fusion 360 (Windows or macOS)
- Python 3 on your machine for the tools — the add-in itself only uses what Fusion brings

## Quick start

```bash
python tools/new_addin.py MyAddIn --install
```

| Flag | Effect |
|---|---|
| `--install` | Create it straight in Fusion's add-ins directory |
| `--out DIR` | Create it somewhere else (default: next to this repository) |
| `--author NAME` | Fill the manifest author field |
| `--prefix STR` | Prefix for the command id, default `thw` — make it yours |
| `--force` | Overwrite an existing folder of that name |

Then in Fusion: **Utilities → ADD-INS → Add-Ins**, select the entry, tick *Run on Startup*, press **Run**. The button appears on the **SKETCH** tab. Click a line, press the button — the demo command draws a tick at the line's midpoint, which proves selection, preview, validation and translation are all wired up.

Check your work at any point without restarting Fusion:

```bash
python tools/test_addin.py --addin MyAddIn
```

## What you get

```
MyAddIn/
  MyAddIn.py            entry point - your code goes here
  myaddin_core.py       the reusable machinery, renamed so it cannot clash
  MyAddIn.manifest      what Fusion reads, with a fresh GUID
  lang/
    en.xml              the reference: every key exists here
    de.xml es.xml fr.xml it.xml
  resources/
    MyAddIn/            16x16.png 32x32.png 64x64.png
```

## The entry point

`MyAddIn.py` is split by two markers. Above `CONFIGURE` is module loading you can ignore. Between `CONFIGURE` and `END OF TEMPLATE` is yours:

| Piece | What it is for |
|---|---|
| `CMD_ID` | Unique across every installed add-in. A collision silently hijacks the other one's button. |
| `WORKSPACE_ID`, `PANEL_IDS` | Where the button goes. Panels are tried in order, first existing one wins. |
| `read_inputs()` | Pull every value out of the dialog once, so execute, preview and validate see the same numbers. |
| `validate()` | Raise `fail('err.key')` for anything the user has to fix. |
| `build_result()` | Do the work. Everything is validated by the time this runs. |
| `build_inputs()` | Lay out the dialog. |
| `remember()` | Carry settings to the next invocation in this session. |
| `on_input_changed()` | Enable, disable or adjust one field from another. |
| `core.add_version_label()` | Last input in the dialog, so the version lands bottom right. |

Below `END OF TEMPLATE` sit the four event handlers and `run`/`stop`. They call the functions above and normally need no editing.

## Language files

The UI language comes from **Preferences → General → User Language** in Fusion, falling back to the OS locale and then to English.

```xml
<string key="in.length">Length</string>
```

`en.xml` is the reference — every key exists there, and a key missing from another file falls back to it, so a half-finished translation degrades to English instead of showing raw keys. To add a language, copy `en.xml`, translate the values, name it after the two-letter code and add the code to `SUPPORTED_LANGUAGES` and `FUSION_LANGUAGE_MAP` in the core module. Placeholders like `{0}` must survive translation; `tools/test_addin.py` checks that for every file.

Nothing outside `lang/` is translated. Identifiers, comments and keys are English throughout, so a translator never has to open a `.py` file.

## Tools

```bash
python tools/new_addin.py MyAddIn --install
```

```bash
python tools/test_addin.py --addin MyAddIn
```

```bash
python tools/make_icon.py --addin MyAddIn
```

`make_icon.py` renders the polygons in its `SHAPES` list. The shipped glyph is deliberately an obvious placeholder — corner brackets and a diagonal — so an unreplaced icon is easy to spot.

## Notes & caveats

- **Fusion caches modules.** An edited helper keeps serving its old version until Fusion restarts. The entry point drops the core module from `sys.modules` before importing it, which makes *stop, run* enough. Any further module you add needs the same treatment.
- **The core module is renamed per add-in for a reason.** `sys.modules` is global to Fusion. Two add-ins both importing `addin_core` would share whichever loaded first, and the second would silently run the first one's code. The scaffolder renames it to `<name>_core.py`; keep it that way.
- **Fusion holds handlers weakly.** A handler that is not referenced from Python gets collected and its event stops firing — with no error. `HandlerRegistry` exists solely to prevent that. Register every handler through it.
- **`executePreview` runs on every keystroke.** It sees half-typed values, so it swallows exceptions on purpose. `validateInputs` is what tells the user what is wrong; do not move that logic into the preview.
- **Deleting the selected entity during the preview can invalidate the selection.** If your command replaces what it was given, do it in `execute` and leave the preview drawing on top.
- **Panel ids move between Fusion versions.** `PANEL_IDS` is a list from most to least preferred rather than one id, and `find_panel` falls back to a global lookup before giving up.
- **Lengths are in centimetres.** Fusion's internal unit, regardless of what a value input displays. `createByReal(1.0)` shown with `'mm'` reads as 10 mm.
- **`isComputeDeferred` must be reset in a `finally`.** An error thrown while it is set leaves the sketch in a state where nothing updates any more.
- **The demo command is meant to be deleted.** It draws a tick at a line's midpoint purely to prove the wiring. Replace it as soon as it has done its job.

## Support this project ❤️

If this template saved you an afternoon, you can support further development:

[![Donate with PayPal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/donate/?hosted_button_id=6CDEVZGJWTNQQ)

**[➡️ Donate via PayPal](https://www.paypal.com/donate/?hosted_button_id=6CDEVZGJWTNQQ)**

## License

This project is licensed under the [MIT License](LICENSE) — © 2026 Thomas Weirich.
