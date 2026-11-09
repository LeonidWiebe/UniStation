import FreeCADGui as Gui


class UniStationWorkbench(Gui.Workbench):
    MenuText = "UniStation"
    # FreeCAD executes InitGui.py with separate local/global namespaces.
    # Class registration must not depend on helpers imported at file scope.
    ToolTip = "Draft geometry with AxisFlow coordinate input"

    def Initialize(self):
        from unistation.i18n import QT_TRANSLATE_NOOP, install, tr
        install()
        self.ToolTip = tr('Draft geometry with AxisFlow coordinate input')
        from unistation.gui import register
        from unistation.palette_gui import register as register_palette
        from unistation.attributes_gui import register as register_attributes
        from unistation.preferences_gui import register as register_preferences
        from unistation.snapping import register as register_snapping
        from unistation.coordinate_input import register as register_coordinates
        register()
        register_palette()
        register_attributes()
        register_preferences()
        register_coordinates()
        snaps = register_snapping()
        drawing = ["UniStation_Line", "UniStation_Wire", "UniStation_Circle",
                   "UniStation_Arc", "UniStation_Rectangle", "UniStation_Freeform"]
        manipulation = ["UniStation_Copy", "UniStation_Move", "UniStation_Scale",
                        "UniStation_Rotate", "UniStation_Mirror", "UniStation_Array"]
        cancel = ["UniStation_Cancel"]
        palette = ["UniStation_IndexedColor", "UniStation_EditPalette",
                   "UniStation_ImportPalette", "UniStation_ExportPalette"]
        self.appendToolbar("UniStation", cancel + ["UniStation_CoordinateInput"])
        self.appendToolbar("Рисование", drawing)
        self.appendToolbar("Манипуляции", manipulation)
        self.appendToolbar("Палитра", palette)
        self.appendToolbar("Атрибуты", ["UniStation_ActiveLayer", "UniStation_ActiveColor", "UniStation_ActiveLineStyle",
                                      "UniStation_ActiveLineWeight"])
        self.appendToolbar("Привязки", snaps)
        self.appendMenu("UniStation", drawing + manipulation + cancel +
                        ["Separator", "UniStation_Reset", "UniStation_CoordinateInput",
                         "UniStation_Preferences"])
        self.appendMenu(QT_TRANSLATE_NOOP('Workbench', 'Palette'), palette)

    def Activated(self):
        from unistation.snapping import activate as activate_snapping
        activate_snapping()
        from unistation.mouse import activate as activate_mouse
        activate_mouse()
        from unistation.attributes_gui import activate
        activate()
        from unistation.toolbar_titles import activate as activate_titles
        activate_titles()

    def Deactivated(self):
        from unistation.coordinate_input import deactivate as deactivate_coordinates
        deactivate_coordinates()
        from unistation.snapping import deactivate as deactivate_snapping
        deactivate_snapping()
        from unistation.mouse import deactivate as deactivate_mouse
        deactivate_mouse()
        from unistation.attributes_gui import deactivate
        deactivate()
        from unistation.toolbar_titles import deactivate as deactivate_titles
        deactivate_titles()
        from unistation.gui import cancel
        cancel()

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(UniStationWorkbench())
