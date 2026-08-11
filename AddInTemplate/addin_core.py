# -*- coding: utf-8 -*-
"""
Reusable core for Fusion 360 add-ins.

Nothing in here is specific to one add-in. It carries the parts that every
add-in needs and that are easy to get wrong:

* a translated text catalogue backed by lang/<code>.xml
* the language Fusion is actually set to
* finding a toolbar panel that exists in this Fusion version
* keeping event handlers alive so they are not garbage collected
* an exception type that reports a language-independent key

tools/new_addin.py renames this file to <name>_core.py when it scaffolds a new
add-in, so two add-ins built from this template cannot collide in sys.modules.
"""

import os
import traceback
import xml.etree.ElementTree as ElementTree

import adsk.core

FALLBACK_LANGUAGE = 'en'
SUPPORTED_LANGUAGES = ('de', 'en', 'es', 'fr', 'it')

# Fusion language preference -> language code. The enum members are looked up
# with getattr so a value this Fusion version does not know cannot break us.
FUSION_LANGUAGE_MAP = {
    'GermanLanguage': 'de',
    'EnglishLanguage': 'en',
    'SpanishLanguage': 'es',
    'FrenchLanguage': 'fr',
    'ItalianLanguage': 'it',
    # Add more as you translate them, e.g.
    # 'JapaneseLanguage': 'ja',
    # 'PortugueseBrazilianLanguage': 'pt',
}


# ------------------------------------------------------------------ Language --

class Strings(object):
    """Text catalogue read from <lang_dir>/<code>.xml, falling back to English.

    A key missing from the active language is served from the fallback file, so
    a half-finished translation degrades to English instead of showing raw keys.
    """

    def __init__(self, lang_dir):
        self.lang_dir = lang_dir
        self.code = FALLBACK_LANGUAGE
        self._current = {}
        self._fallback = {}

    def _read(self, code):
        path = os.path.join(self.lang_dir, '%s.xml' % code)
        if not os.path.isfile(path):
            return {}
        try:
            root = ElementTree.parse(path).getroot()
        except Exception:
            return {}
        out = {}
        for node in root.findall('string'):
            key = node.get('key')
            if key:
                out[key] = node.text or ''
        return out

    def load(self, code):
        if code not in SUPPORTED_LANGUAGES:
            code = FALLBACK_LANGUAGE
        if not self._fallback:
            self._fallback = self._read(FALLBACK_LANGUAGE)
        self._current = self._fallback if code == FALLBACK_LANGUAGE else self._read(code)
        self.code = code
        return self.code

    def get(self, key, *args):
        text = self._current.get(key) or self._fallback.get(key) or key
        if args:
            try:
                return text.format(*args)
            except (IndexError, KeyError, ValueError):
                return text
        return text


def detect_language():
    """Language code from the Fusion preference, else from the environment.

    Falls back to English rather than raising, so a Fusion build with an
    unexpected enum still starts the add-in.
    """
    try:
        prefs = adsk.core.Application.get().preferences.generalPreferences
        current = prefs.userLanguage
        languages = adsk.core.UserLanguages
        for name, code in FUSION_LANGUAGE_MAP.items():
            value = getattr(languages, name, None)
            if value is not None and current == value:
                return code
    except Exception:
        pass

    for env in ('LANG', 'LANGUAGE', 'LC_ALL'):
        value = os.environ.get(env) or ''
        code = value.replace('-', '_').split('_')[0].lower()
        if code in SUPPORTED_LANGUAGES:
            return code
    try:
        import locale
        value = locale.getdefaultlocale()[0] or ''
        code = value.replace('-', '_').split('_')[0].lower()
        if code in SUPPORTED_LANGUAGES:
            return code
    except Exception:
        pass
    return FALLBACK_LANGUAGE


# -------------------------------------------------------------------- Errors --

class AddInError(Exception):
    """An expected, explainable failure.

    key names the reason in a language-independent way, which lets
    validateInputs decide without parsing text. The message itself is looked up
    in the catalogue at construction time.
    """

    def __init__(self, strings, key, *args):
        self.key = key
        self.params = args
        super(AddInError, self).__init__(strings.get(key, *args))


# ------------------------------------------------------------------ Handlers --

class HandlerRegistry(object):
    """Keeps references to event handlers.

    Fusion holds only a weak reference to a handler. Anything not stored on the
    Python side is collected, and the event silently stops firing - the single
    most common way for an add-in to half-work. Register every handler here.
    """

    def __init__(self):
        self._handlers = []

    def add(self, event, handler):
        event.add(handler)
        self._handlers.append(handler)
        return handler

    def clear(self):
        del self._handlers[:]


# --------------------------------------------------------------------- Panel --

def find_panel(ui, workspace_id, panel_ids):
    """First existing panel out of panel_ids, workspace first, then globally.

    Panel ids move between Fusion versions, so pass a list from most to least
    preferred rather than betting on one.
    """
    workspace = ui.workspaces.itemById(workspace_id)
    for panel_id in panel_ids:
        if workspace:
            panel = workspace.toolbarPanels.itemById(panel_id)
            if panel:
                return panel
        panel = ui.allToolbarPanels.itemById(panel_id)
        if panel:
            return panel
    return None


def add_button(ui, panel, command_definition, promoted=True):
    """Put a command on a panel, replacing a control left over from a reload."""
    existing = panel.controls.itemById(command_definition.id)
    if existing:
        existing.deleteMe()
    control = panel.controls.addCommand(command_definition)
    control.isPromoted = promoted
    control.isPromotedByDefault = promoted
    return control


def remove_button(ui, workspace_id, panel_ids, command_id):
    """Take the control and the command definition back off the toolbar."""
    panel = find_panel(ui, workspace_id, panel_ids)
    if panel:
        control = panel.controls.itemById(command_id)
        if control:
            control.deleteMe()
    definition = ui.commandDefinitions.itemById(command_id)
    if definition:
        definition.deleteMe()


# ---------------------------------------------------------------- Reporting --

def report(ui, strings, key):
    """Show an unexpected exception with its traceback.

    Only for the genuinely unexpected. Anything the user can fix should be an
    AddInError so validateInputs can block OK instead of popping a dialog.
    """
    try:
        ui.messageBox(strings.get(key, traceback.format_exc()),
                      strings.get('cmd.name'))
    except Exception:
        pass
