# -*- coding: utf-8 -*-
"""Scaffold a new Fusion 360 add-in from this template.

    python tools/new_addin.py MyAddIn
    python tools/new_addin.py MyAddIn --install
    python tools/new_addin.py MyAddIn --out ../my-addin --author "Jane Doe"

Copies the template folder, renames every file and identifier that has to be
unique per add-in, and stamps a fresh GUID into the manifest. Standard library
only.
"""
import os
import re
import sys
import uuid
import shutil
import argparse
import platform

TEMPLATE_NAME = 'AddInTemplate'
TEMPLATE_CORE = 'addin_core'
TEMPLATE_CMD_ID = 'thwAddInTemplateCmd'

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(_HERE)
TEMPLATE_DIR = os.path.join(REPO, TEMPLATE_NAME)

NAME_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9]*$')


def addin_directory():
    """Where Fusion looks for add-ins on this machine."""
    if platform.system() == 'Darwin':
        return os.path.expanduser(
            '~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns')
    return os.path.join(os.environ.get('APPDATA', ''), 'Autodesk',
                        'Autodesk Fusion 360', 'API', 'AddIns')


def core_module_name(name):
    """MyAddIn -> myaddin_core, so two add-ins cannot collide in sys.modules."""
    return '%s_core' % re.sub(r'[^a-z0-9]', '', name.lower())


def read(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text)


def replace_string_value(text, key, value):
    """Swap the text of one <string key="..."> without reformatting the file."""
    pattern = re.compile(
        r'(<string key="%s">)(.*?)(</string>)' % re.escape(key), re.DOTALL)
    return pattern.sub(lambda m: m.group(1) + value + m.group(3), text, count=1)


def xml_escape(text):
    return (text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def scaffold(name, out_dir, author, prefix, force):
    if not NAME_PATTERN.match(name):
        raise SystemExit('The name must start with a letter and contain only '
                         'letters and digits - it becomes a Python module name. '
                         'Got: %r' % name)
    if name == TEMPLATE_NAME:
        raise SystemExit('Pick a name other than %s.' % TEMPLATE_NAME)
    if not os.path.isdir(TEMPLATE_DIR):
        raise SystemExit('Template folder not found: %s' % TEMPLATE_DIR)

    target = os.path.join(out_dir, name)
    if os.path.exists(target):
        if not force:
            raise SystemExit('%s already exists. Pass --force to overwrite it.' % target)
        shutil.rmtree(target)

    core_name = core_module_name(name)
    command_id = '%s%sCmd' % (prefix, name)

    shutil.copytree(TEMPLATE_DIR, target,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

    # --- rename the files Fusion matches by name -----------------------------
    os.rename(os.path.join(target, '%s.py' % TEMPLATE_NAME),
              os.path.join(target, '%s.py' % name))
    os.rename(os.path.join(target, '%s.manifest' % TEMPLATE_NAME),
              os.path.join(target, '%s.manifest' % name))
    os.rename(os.path.join(target, '%s.py' % TEMPLATE_CORE),
              os.path.join(target, '%s.py' % core_name))

    icons = os.path.join(target, 'resources', TEMPLATE_NAME)
    if os.path.isdir(icons):
        os.rename(icons, os.path.join(target, 'resources', name))

    # --- rewrite the identifiers inside them ---------------------------------
    entry = os.path.join(target, '%s.py' % name)
    text = read(entry)
    text = text.replace("_CORE_MODULE = '%s'" % TEMPLATE_CORE,
                        "_CORE_MODULE = '%s'" % core_name)
    text = text.replace("CMD_ID = '%s'" % TEMPLATE_CMD_ID,
                        "CMD_ID = '%s'" % command_id)
    text = text.replace(TEMPLATE_NAME, name)
    write(entry, text)

    core_path = os.path.join(target, '%s.py' % core_name)
    write(core_path, read(core_path).replace(
        'tools/new_addin.py renames this file to <name>_core.py when it scaffolds a new\nadd-in, so two add-ins built from this template cannot collide in sys.modules.',
        'Scaffolded from AddInTemplate. This file is the shared machinery; the\nadd-in specific code lives in %s.py.' % name))

    manifest = os.path.join(target, '%s.manifest' % name)
    text = read(manifest)
    text = text.replace('00000000-0000-0000-0000-000000000000', str(uuid.uuid4()))
    text = text.replace('"author": "Your Name"', '"author": "%s"' % author)
    write(manifest, text)

    # --- put the new name in front of the user in every language -------------
    lang_dir = os.path.join(target, 'lang')
    display = xml_escape(name)
    for entry_name in sorted(os.listdir(lang_dir)):
        if not entry_name.endswith('.xml'):
            continue
        path = os.path.join(lang_dir, entry_name)
        text = read(path)
        text = replace_string_value(text, 'cmd.name', display)
        text = replace_string_value(
            text, 'cmd.tooltip', '%s\nTODO: describe what this command does.' % display)
        write(path, text)

    return target, core_name, command_id


def main():
    parser = argparse.ArgumentParser(
        description='Scaffold a new Fusion 360 add-in from this template.')
    parser.add_argument('name', help='add-in name, e.g. MyAddIn (letters and digits)')
    parser.add_argument('--out', help='where to create it (default: next to the template)')
    parser.add_argument('--install', action='store_true',
                        help="create it straight in Fusion's add-ins directory")
    parser.add_argument('--author', default='Your Name', help='manifest author field')
    parser.add_argument('--prefix', default='thw',
                        help='prefix for the command id, keeps it unique (default: thw)')
    parser.add_argument('--force', action='store_true',
                        help='overwrite an existing folder of that name')
    args = parser.parse_args()

    if args.install and args.out:
        raise SystemExit('Use either --install or --out, not both.')
    out_dir = args.out or (addin_directory() if args.install else os.path.dirname(REPO))
    out_dir = os.path.abspath(out_dir)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    target, core_name, command_id = scaffold(
        args.name, out_dir, args.author, args.prefix, args.force)

    print('created %s' % target)
    print('  entry point   %s.py' % args.name)
    print('  core module   %s.py' % core_name)
    print('  command id    %s' % command_id)
    print()
    print('Next:')
    print('  1. Edit %s.py between the CONFIGURE and END OF TEMPLATE markers.' % args.name)
    print('  2. Translate lang/*.xml - en.xml is the reference.')
    print('  3. Replace the placeholder icon in resources/%s/.' % args.name)
    if not args.install:
        print('  4. Copy the folder to %s' % addin_directory())
    print('  %d. In Fusion: Utilities -> ADD-INS -> Add-Ins -> Run.'
          % (4 if args.install else 5))


if __name__ == '__main__':
    main()
