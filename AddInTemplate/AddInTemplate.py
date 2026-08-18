# -*- coding: utf-8 -*-
"""
AddInTemplate - Fusion 360 add-in entry point.

Everything you edit lives between the CONFIGURE and END OF TEMPLATE markers.
The reusable machinery sits in addin_core.py next to this file.

The demo command asks for one sketch line and a length, then draws a
perpendicular tick at its midpoint. Replace build_result() and the inputs in
CommandCreatedHandler with your own; the rest of the file can stay as it is.
"""

import os
import sys
import importlib

import adsk.core
import adsk.fusion

# --- module loading ---------------------------------------------------------
# Fusion caches imported modules, so an edited helper would keep serving its
# old version until Fusion restarts. Dropping it from sys.modules before the
# import makes "stop, run" pick up changes.
#
# The name is renamed per add-in by tools/new_addin.py, which is what stops two
# add-ins built from this template from overwriting each other's core module.
_CORE_MODULE = 'addin_core'

_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)
if _CORE_MODULE in sys.modules:
    del sys.modules[_CORE_MODULE]
core = importlib.import_module(_CORE_MODULE)


# ============================================================== CONFIGURE ====

# Unique across every add-in installed in Fusion. Prefix it with something of
# your own; a collision silently hijacks the other add-in's button.
CMD_ID = 'thwAddInTemplateCmd'

# Where the button goes. FusionSolidEnvironment is the design workspace.
WORKSPACE_ID = 'FusionSolidEnvironment'

# Tried in order, first one that exists wins. Common ids:
#   SketchCreatePanel, SketchModifyPanel  - the SKETCH tab
#   SolidCreatePanel, SolidModifyPanel    - the SOLID tab
#   InspectPanel, ToolsPanel              - the UTILITIES tab
PANEL_IDS = ('SketchCreatePanel', 'SolidCreatePanel')

# Command input ids. Keep the prefix unique-ish; they only have to be unique
# inside this command.
IN_LINE = 'tplLine'
IN_LENGTH = 'tplLength'
IN_FLIP = 'tplFlip'

RESOURCE_FOLDER = os.path.join(_DIR, 'resources', 'AddInTemplate')
LANG_DIR = os.path.join(_DIR, 'lang')

# Last used values, kept for the duration of the Fusion session.
# Lengths are in cm - Fusion's internal unit - regardless of what the value
# input displays.
_last = {
    IN_LENGTH: 1.0,     # 10 mm
    IN_FLIP: False,
}

# =============================================================================

S = core.Strings(LANG_DIR)
S.load(core.FALLBACK_LANGUAGE)
_handlers = core.HandlerRegistry()
_control = None
_updating = False       # re-entrancy guard for inputChanged


def T(key, *args):
    return S.get(key, *args)


def fail(key, *args):
    """Raise an explainable error carrying a language-independent key."""
    raise core.AddInError(S, key, *args)


# ============================================================ YOUR CODE HERE ==

def read_inputs(inputs):
    """Pull every value out of the dialog in one place.

    Doing this once keeps execute, executePreview and validateInputs looking at
    exactly the same numbers.
    """
    selection = inputs.itemById(IN_LINE)
    line = None
    if selection.selectionCount == 1:
        entity = selection.selection(0).entity
        if entity and entity.objectType == adsk.fusion.SketchLine.classType():
            line = entity
    return dict(
        line=line,
        length=inputs.itemById(IN_LENGTH).value,
        flip=inputs.itemById(IN_FLIP).value,
    )


def validate(values):
    """Raise an AddInError for anything the user has to fix.

    Called before drawing and again from validateInputs, so an impossible
    combination disables OK instead of failing halfway through.
    """
    if values['line'] is None:
        fail('err.no_selection')
    if values['length'] <= 1e-9:
        fail('err.length_positive')

    start = values['line'].startSketchPoint.geometry
    end = values['line'].endSketchPoint.geometry
    span = ((end.x - start.x) ** 2 + (end.y - start.y) ** 2) ** 0.5
    if span <= 1e-9:
        fail('err.zero_length')
    if values['length'] > span:
        fail('err.too_long', '%.2f' % (span * 10.0))


def build_result(values):
    """Do the actual work. Everything is already validated at this point."""
    line = values['line']
    sketch = line.parentSketch
    start = line.startSketchPoint.geometry
    end = line.endSketchPoint.geometry

    span = ((end.x - start.x) ** 2 + (end.y - start.y) ** 2) ** 0.5
    u = ((end.x - start.x) / span, (end.y - start.y) / span)
    n = (-u[1], u[0])
    if values['flip']:
        n = (-n[0], -n[1])

    mid = ((start.x + end.x) / 2.0, (start.y + end.y) / 2.0)
    tip = (mid[0] + n[0] * values['length'], mid[1] + n[1] * values['length'])

    # isComputeDeferred keeps the solver quiet until the whole run is drawn.
    # Always reset it in a finally block, or a raised error leaves the sketch
    # in a state where nothing updates any more.
    sketch.isComputeDeferred = True
    try:
        sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(mid[0], mid[1], 0.0),
            adsk.core.Point3D.create(tip[0], tip[1], 0.0))
    finally:
        sketch.isComputeDeferred = False


def build_inputs(inputs):
    """Lay out the dialog. Every label comes from the text catalogue."""
    selection = inputs.addSelectionInput(IN_LINE, T('in.line'), T('in.line.prompt'))
    selection.addSelectionFilter('SketchLines')
    selection.setSelectionLimits(1, 1)

    # 'mm' is the display unit; createByReal takes cm. A value input respects
    # the document's units and accepts expressions like "2 * 3 mm".
    inputs.addValueInput(IN_LENGTH, T('in.length'), 'mm',
                         adsk.core.ValueInput.createByReal(_last[IN_LENGTH]))
    inputs.addBoolValueInput(IN_FLIP, T('in.flip'), True, '', _last[IN_FLIP])
    return selection


def remember(values):
    """Carry settings over to the next invocation within this session."""
    _last[IN_LENGTH] = values['length']
    _last[IN_FLIP] = values['flip']


def on_input_changed(inputs, changed):
    """React to one field to enable, disable or adjust another.

    Set _updating around any value you write back here, otherwise the write
    re-enters this handler.
    """
    return


# ========================================================= END OF TEMPLATE ====

def _run_command(inputs):
    values = read_inputs(inputs)
    validate(values)
    build_result(values)
    return values


class ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        ui = adsk.core.Application.get().userInterface
        try:
            remember(_run_command(args.firingEvent.sender.commandInputs))
        except core.AddInError as err:
            ui.messageBox(str(err), T('cmd.name'))
        except Exception:
            core.report(ui, S, 'msg.exec_failed')


class PreviewHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            _run_command(args.firingEvent.sender.commandInputs)
            # False makes Fusion run execute again for the real result. Set it
            # to True only when the preview already produced the final feature.
            args.isValidResult = False
        except Exception:
            # The preview fires on every keystroke, including half-typed
            # values. Staying silent here is deliberate; validateInputs is what
            # tells the user what is wrong.
            pass


class ValidateHandler(adsk.core.ValidateInputsEventHandler):
    def notify(self, args):
        try:
            validate(read_inputs(args.firingEvent.sender.commandInputs))
            args.areInputsValid = True
        except Exception:
            args.areInputsValid = False


class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def notify(self, args):
        if _updating:
            return
        try:
            changed = args.input
            on_input_changed(changed.parentCommand.commandInputs, changed)
        except Exception:
            pass


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        ui = adsk.core.Application.get().userInterface
        try:
            command = args.command
            command.isRepeatable = True
            inputs = command.commandInputs

            # Whatever was selected before the button was pressed. Read it
            # before the inputs exist, then hand it to the selection input, so
            # clicking a line and then the button just works.
            preselected = []
            for i in range(ui.activeSelections.count):
                entity = ui.activeSelections.item(i).entity
                if entity and entity.objectType == adsk.fusion.SketchLine.classType():
                    preselected.append(entity)

            selection = build_inputs(inputs)
            if preselected and selection and selection.selectionCount == 0:
                selection.addSelection(preselected[0])

            _handlers.add(command.execute, ExecuteHandler())
            _handlers.add(command.executePreview, PreviewHandler())
            _handlers.add(command.validateInputs, ValidateHandler())
            _handlers.add(command.inputChanged, InputChangedHandler())
        except Exception:
            core.report(ui, S, 'msg.dialog_failed')


def run(context):
    global _control
    ui = None
    try:
        ui = adsk.core.Application.get().userInterface
        S.load(core.detect_language())

        # A definition left behind by a previous run would keep its old label
        # and its old handler, so drop it first.
        stale = ui.commandDefinitions.itemById(CMD_ID)
        if stale:
            stale.deleteMe()

        icons = RESOURCE_FOLDER if os.path.isdir(RESOURCE_FOLDER) else ''
        definition = ui.commandDefinitions.addButtonDefinition(
            CMD_ID,
            core.display_name(T('cmd.name'), core.read_version(_DIR, 'AddInTemplate')),
            T('cmd.tooltip'), icons)
        _handlers.add(definition.commandCreated, CommandCreatedHandler())

        panel = core.find_panel(ui, WORKSPACE_ID, PANEL_IDS)
        if not panel:
            ui.messageBox(T('msg.panel_missing'), T('cmd.name'))
            return
        _control = core.add_button(ui, panel, definition)
    except Exception:
        if ui:
            core.report(ui, S, 'msg.run_failed')


def stop(context):
    global _control
    ui = None
    try:
        ui = adsk.core.Application.get().userInterface
        core.remove_button(ui, WORKSPACE_ID, PANEL_IDS, CMD_ID)
        _control = None
        _handlers.clear()
    except Exception:
        if ui:
            core.report(ui, S, 'msg.stop_failed')
