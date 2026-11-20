"""Keep level visibility and tree selection consistent in the workbench."""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore

from unistation.level_visibility import STATE, enforce_view_state, is_frozen, refresh_level_selection


class VisibilityObserver:
    def __init__(self):
        self.pending = {}
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.update)
        App.addDocumentObserver(self)
        Gui.addDocumentObserver(self)
        Gui.Selection.addObserver(self)
        self.slotActivateDocument(App.ActiveDocument)

    def close(self):
        self.timer.stop()
        Gui.Selection.removeObserver(self)
        Gui.removeDocumentObserver(self)
        App.removeDocumentObserver(self)
        self.pending.clear()

    def schedule(self, obj):
        if obj.Document is not None:
            self.pending.setdefault(obj.Document.Name, set()).add(obj.Name)
            self.timer.start(0)

    def slotActivateDocument(self, _document):
        document = App.ActiveDocument
        if document is not None:
            names = {obj.Name for obj in document.Objects if getattr(obj, STATE, 0)}
            if names:
                self.pending.setdefault(document.Name, set()).update(names)
                self.timer.start(0)

    def slotChangedObject(self, source, prop):
        if prop == STATE:
            self.schedule(source)
        elif prop in ("Visibility", "Selectable"):
            if isinstance(source, App.DocumentObject):
                return
            try:
                # FreeCAD can notify before attaching the view provider.
                # Document checks attachment before Object can be read safely.
                if source.Document is None:
                    return
            except (AttributeError, RuntimeError, ReferenceError):
                return
            obj = source.Object
            if getattr(obj, STATE, 0):
                self.schedule(obj)

    def addSelection(self, document_name, object_name, _subelement, _point):
        document = App.listDocuments().get(document_name)
        obj = document.getObject(object_name) if document is not None else None
        if obj is not None and is_frozen(obj):
            self.schedule(obj)

    def update(self):
        # Wait for FreeCAD to finish notifying observers, especially on Undo/Redo
        # and while adding a selection from the tree.
        pending, self.pending = self.pending, {}
        documents = App.listDocuments()
        for document_name, names in pending.items():
            document = documents.get(document_name)
            if document is None:
                continue
            objects = [obj for name in names if (obj := document.getObject(name)) is not None]
            for obj in objects:
                enforce_view_state(obj)
            refresh_level_selection(document, objects)


_observer = None


def activate():
    global _observer
    if _observer is None:
        _observer = VisibilityObserver()


def deactivate():
    global _observer
    if _observer is not None:
        _observer.close()
        _observer = None
