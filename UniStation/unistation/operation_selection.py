"""Apply result-selection preferences only after an operation has committed."""

import FreeCAD as App
import FreeCADGui as Gui

from unistation.i18n import tr
from unistation.preferences import auto_select_result


def finish(document, objects):
    try:
        if (App.ActiveDocument is not document
                or App.listDocuments().get(document.Name) is not document):
            return
        results = [obj for obj in objects
                   if obj is not None and obj.Document is document
                   and document.getObject(obj.Name) is obj]
        auto_select = auto_select_result()
        Gui.Selection.clearSelection(document.Name)
        Gui.Selection.clearPreselection()
        if auto_select:
            for obj in results:
                Gui.Selection.addSelection(obj)
    except Exception as exc:
        # Selection is UI state. Never report a committed operation as failed,
        # or try to abort its already completed geometry transaction.
        App.Console.PrintWarning(tr(
            'UniStation: the operation succeeded, but selection could not be updated: {0}'
        ).format(str(exc)) + "\n")
