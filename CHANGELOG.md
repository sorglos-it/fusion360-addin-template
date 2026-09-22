# Changelog

## Unreleased – 2026-09-22

- Layout after the project standard: the template add-in lives in `apps/desktop/AddInTemplate/`, unchanged inside
  (Fusion needs folder, `.py` and `.manifest` under one name). Its version is also in `apps/desktop/VERSION`.
- The offline check moved to `apps/desktop/tests/test_addin.py`; `--addin` looks in `apps/desktop/`.
- `tools/new_addin.py` and `tools/make_icon.py` stay in `tools/` and find the template in its new place. New add-ins
  and icons come out exactly as before.
- Compatibility: `tools/test_addin.py` still works and forwards to the moved check, so projects built from the
  template keep their commands.
- README rewritten: start in 3 steps. The check and icon commands for your own add-in now name its folder (`--path`,
  `--root`) — `--addin` only ever looked inside this repository.
- README and a code comment no longer claim the dialog says why OK is greyed out — it does not. The translated reason
  only shows as a message box when `execute` runs into it.
- New `CHANGELOG.md`; `.gitignore` after the project standard.

Earlier versions: [Releases](https://github.com/sorglos-it/fusion360-addin-template/releases).
