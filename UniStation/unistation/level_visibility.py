"""Native view state suppressed by a document's level flags."""

from dataclasses import dataclass

from unistation.i18n import tr


STATE = "UstnLevelViewState"
_HOLD_VISIBILITY = 1
_WAS_VISIBLE = 2
_HOLD_SELECTION = 4
_WAS_SELECTABLE = 8


def _view_state(obj):
    return getattr(obj, STATE, 0)


def is_frozen(obj):
    return bool(_view_state(obj) & _HOLD_SELECTION)


def _write_state(obj, state):
    if state is None:
        if STATE in obj.PropertiesList:
            obj.removeProperty(STATE)
        return
    if STATE not in obj.PropertiesList:
        obj.addProperty("App::PropertyInteger", STATE, "UniStation", hidden=True)
    if getattr(obj, STATE) != state:
        setattr(obj, STATE, state)


def _write_view(view, visible, selectable):
    if view.Visibility != visible:
        view.Visibility = visible
    if selectable is not None and view.Selectable != selectable:
        view.Selectable = selectable


@dataclass(frozen=True)
class ViewChange:
    obj: object
    view: object
    previous: tuple
    target: tuple

    def apply(self):
        state, visible, selectable = self.target
        _write_state(self.obj, state)
        _write_view(self.view, visible, selectable)

    def restore(self):
        state, visible, selectable = self.previous
        _write_state(self.obj, state)
        _write_view(self.view, visible, selectable)


def _masked_value(state, held, saved, current, suppress):
    if suppress:
        if not state & held:
            state |= held
            if current:
                state |= saved
        return state, False
    if state & held:
        return state & ~(held | saved), bool(state & saved)
    return state, current


def prepare_view_change(obj, available, frozen):
    previous_state = getattr(obj, STATE, None)
    if previous_state is None and available and not frozen:
        return None
    view = getattr(obj, "ViewObject", None)
    if view is None:
        from unistation.levels import LevelError
        raise LevelError(tr('Open the document in the FreeCAD GUI to change level visibility.'))
    visible = view.Visibility
    selectable = getattr(view, "Selectable", None)
    state, new_visibility = _masked_value(previous_state or 0, _HOLD_VISIBILITY,
                                          _WAS_VISIBLE, visible, not available)
    state, new_selectable = _masked_value(state, _HOLD_SELECTION, _WAS_SELECTABLE,
                                          selectable, frozen)
    previous = previous_state, visible, selectable
    target = state, new_visibility, new_selectable if selectable is not None else None
    if previous == target:
        return None
    return ViewChange(obj, view, previous, target)


def enforce_view_state(obj):
    state = _view_state(obj)
    if not state:
        return
    view = obj.ViewObject
    if view is not None:
        visible = view.Visibility and not bool(state & _HOLD_VISIBILITY)
        selectable = getattr(view, "Selectable", None)
        if selectable is not None and state & _HOLD_SELECTION:
            selectable = False
        _write_view(view, visible, selectable)


def copy_view_state(source, target):
    state = _view_state(source)
    if state:
        _write_state(target, state)
        enforce_view_state(target)


def refresh_level_selection(document, objects):
    import FreeCAD as App
    import FreeCADGui as Gui
    try:
        hidden = set()
        for obj in objects:
            state = _view_state(obj)
            if state & _HOLD_VISIBILITY:
                hidden.add(obj.Name)
            if state & _HOLD_SELECTION:
                Gui.Selection.removeSelection(obj)
        if hidden and App.ActiveDocument is document:
            Gui.Selection.clearPreselection()
            # Draft snap extensions/intersections can use previously picked
            # subelements even after the source stops being visible.
            snapper = getattr(Gui, "Snapper", None)
            names = getattr(snapper, "lastObj", ())
            subelements = getattr(snapper, "lastObjSubelements", ())
            if names and len(names) == len(subelements):
                keep = [(name, sub) for name, sub in zip(names, subelements) if name not in hidden]
                names[:] = [name for name, _sub in keep]
                subelements[:] = [sub for _name, sub in keep]
    except Exception as exc:
        # The document transaction has already finished.
        App.Console.PrintWarning(tr('UniStation: could not update selection or snapping: {}')
                                 .format(exc) + "\n")
