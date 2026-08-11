# -*- coding: utf-8 -*-
"""Check an add-in without starting Fusion.

    python tools/test_addin.py                  # the template itself
    python tools/test_addin.py --addin MyAddIn  # a scaffolded add-in
    python tools/test_addin.py --path "C:/.../AddIns/MyAddIn"

Stubs the adsk modules, imports the add-in and verifies the things that are
tedious to notice inside Fusion: a manifest that parses, a real GUID, a command
id that was actually changed, language files that agree with the reference, and
placeholders that survived translation.

Keep this runnable. It is the only feedback loop that does not need a restart.
"""
import os
import re
import sys
import json
import types
import argparse
import xml.etree.ElementTree as ElementTree

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(_HERE)

failures = []
warnings = []


def check(condition, message):
    if condition:
        print('  ok   ', message)
    else:
        print('  FAIL ', message)
        failures.append(message)


def warn(condition, message):
    if condition:
        print('  ok   ', message)
    else:
        print('  warn ', message)
        warnings.append(message)


def install_adsk_stubs():
    """Make `import adsk.core` work outside Fusion.

    Only the handler base classes have to be real classes; everything else is
    touched at call time, not at import time.
    """
    adsk = types.ModuleType('adsk')
    core = types.ModuleType('adsk.core')
    fusion = types.ModuleType('adsk.fusion')
    for name in ('CommandEventHandler', 'ValidateInputsEventHandler',
                 'InputChangedEventHandler', 'CommandCreatedEventHandler',
                 'SelectionEventHandler', 'CommandTerminationHandler'):
        setattr(core, name, type(name, (object,), {}))
    adsk.core = core
    adsk.fusion = fusion
    sys.modules['adsk'] = adsk
    sys.modules['adsk.core'] = core
    sys.modules['adsk.fusion'] = fusion


def main():
    parser = argparse.ArgumentParser(description='Check a Fusion 360 add-in offline.')
    parser.add_argument('--addin', default='AddInTemplate',
                        help='add-in folder name inside the repository')
    parser.add_argument('--path', help='full path to an add-in folder, wins over --addin')
    args = parser.parse_args()

    addin_dir = os.path.abspath(args.path or os.path.join(REPO, args.addin))
    name = os.path.basename(addin_dir.rstrip(os.sep))
    print('checking %s' % addin_dir)
    print()

    print('1) Layout')
    check(os.path.isdir(addin_dir), 'the add-in folder exists')
    if not os.path.isdir(addin_dir):
        sys.exit(1)
    entry = os.path.join(addin_dir, '%s.py' % name)
    manifest_path = os.path.join(addin_dir, '%s.manifest' % name)
    check(os.path.isfile(entry), '%s.py matches the folder name' % name)
    check(os.path.isfile(manifest_path), '%s.manifest matches the folder name' % name)
    lang_dir = os.path.join(addin_dir, 'lang')
    check(os.path.isdir(lang_dir), 'lang/ exists')

    print('2) Manifest')
    manifest = {}
    try:
        with open(manifest_path, 'r', encoding='utf-8') as handle:
            manifest = json.load(handle)
        check(True, 'manifest is valid JSON')
    except Exception as err:
        check(False, 'manifest is valid JSON - %s' % err)
    check(manifest.get('type') == 'addin', 'type is "addin"')
    check(manifest.get('autodeskProduct') == 'Fusion360', 'autodeskProduct is "Fusion360"')
    guid = manifest.get('id', '')
    check(bool(re.match(r'^[0-9a-fA-F-]{36}$', guid)), 'id looks like a GUID')
    warn(guid != '00000000-0000-0000-0000-000000000000',
         'id is not the placeholder GUID')
    warn(manifest.get('author') != 'Your Name', 'author has been filled in')

    print('3) Import')
    install_adsk_stubs()
    sys.path.insert(0, addin_dir)
    module = None
    try:
        module = __import__(name)
        check(True, 'the add-in imports cleanly')
    except Exception as err:
        check(False, 'the add-in imports cleanly - %r' % err)
    if module is None:
        sys.exit(1)

    check(callable(getattr(module, 'run', None)), 'run(context) is defined')
    check(callable(getattr(module, 'stop', None)), 'stop(context) is defined')
    command_id = getattr(module, 'CMD_ID', '')
    check(bool(command_id), 'CMD_ID is set')
    warn(command_id != 'thwAddInTemplateCmd', 'CMD_ID is no longer the template default')

    core_module = getattr(module, '_CORE_MODULE', None)
    if core_module:
        check(os.path.isfile(os.path.join(addin_dir, '%s.py' % core_module)),
              '_CORE_MODULE "%s" has a matching file' % core_module)
        warn(core_module != 'addin_core' or name == 'AddInTemplate',
             'the core module was renamed, so it cannot clash with another add-in')

    print('4) Language files')
    strings = getattr(module, 'S', None)
    supported = ()
    if strings is not None:
        core = sys.modules.get(core_module) if core_module else None
        supported = getattr(core, 'SUPPORTED_LANGUAGES', ())
    check(bool(supported), 'SUPPORTED_LANGUAGES is available (%s)' % (', '.join(supported) or '-'))

    reference_path = os.path.join(lang_dir, 'en.xml')
    check(os.path.isfile(reference_path), 'en.xml exists as the reference')
    reference = {}
    if os.path.isfile(reference_path):
        for node in ElementTree.parse(reference_path).getroot().findall('string'):
            reference[node.get('key')] = node.text or ''
    check(bool(reference), 'en.xml holds %d keys' % len(reference))

    for code in supported:
        path = os.path.join(lang_dir, '%s.xml' % code)
        check(os.path.isfile(path), '%s.xml exists' % code)
        if not os.path.isfile(path):
            continue
        root = ElementTree.parse(path).getroot()
        check(root.get('language') == code, '%s.xml declares language="%s"' % (code, code))
        values = {}
        for node in root.findall('string'):
            values[node.get('key')] = node.text or ''
        missing = sorted(set(reference) - set(values))
        unknown = sorted(set(values) - set(reference))
        check(not missing, '%s.xml complete%s'
              % (code, '' if not missing else ' - missing: %s' % missing))
        check(not unknown, '%s.xml has no unknown keys%s'
              % (code, '' if not unknown else ' - unknown: %s' % unknown))
        mismatched = [key for key in reference
                      if set(re.findall(r'\{\d+\}', reference[key]))
                      != set(re.findall(r'\{\d+\}', values.get(key, '')))]
        check(not mismatched, '%s.xml keeps every placeholder%s'
              % (code, '' if not mismatched else ' - differing: %s' % mismatched))
        check(all(value.strip() for value in values.values()),
              '%s.xml has no empty texts' % code)

    print('5) Text catalogue')
    if strings is not None and supported:
        for code in supported:
            strings.load(code)
            check(strings.code == code and module.T('cmd.name') != 'cmd.name',
                  '%s: cmd.name = "%s"' % (code, module.T('cmd.name')))
        check(strings.load('klingon') == 'en', 'an unknown language falls back to English')
        check(module.T('does.not.exist') == 'does.not.exist',
              'a missing key returns the key itself')
        strings.load('en')
        warn('TODO' not in module.T('cmd.tooltip'), 'cmd.tooltip no longer says TODO')

    print('6) Icons')
    icon_dir = os.path.join(addin_dir, 'resources', name)
    check(os.path.isdir(icon_dir), 'resources/%s/ exists' % name)
    for size in (16, 32, 64):
        icon = os.path.join(icon_dir, '%dx%d.png' % (size, size))
        check(os.path.isfile(icon), '%dx%d.png present' % (size, size))
        if os.path.isfile(icon):
            with open(icon, 'rb') as handle:
                check(handle.read(8) == b'\x89PNG\r\n\x1a\n',
                      '%dx%d.png is a real PNG' % (size, size))

    print()
    if warnings:
        print('%d warning(s) - fine for the template, worth fixing in a real add-in'
              % len(warnings))
    if failures:
        print('%d FAILURES' % len(failures))
        sys.exit(1)
    print('all checks passed')


if __name__ == '__main__':
    main()
