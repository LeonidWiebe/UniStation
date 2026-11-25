import FreeCADGui as Gui


class UniStationWorkbench(Gui.Workbench):
    MenuText = "UniStation"
    # FreeCAD executes InitGui.py with separate local/global namespaces.
    # Class registration must not depend on helpers imported at file scope.
    ToolTip = "Draft geometry with AxisFlow coordinate input"

    def __init__(self):
        import os
        import unistation
        self.__class__.Icon = os.path.join(
            os.path.dirname(unistation.__file__), "icons", "unistation.svg"
        )

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
        from unistation.levels_gui import COMMAND as level_manager, register as register_levels
        from unistation.levels_gui import ASSIGN_COMMAND as assign_level
        from unistation.plot_gui import COMMAND as plot_pdf, register as register_plot
        from unistation.change_attributes_gui import COMMAND as change_attributes, register as register_change_attributes
        register()
        register_palette()
        register_change_attributes()
        register_attributes()
        register_preferences()
        register_coordinates()
        register_levels()
        register_plot()
        snaps = register_snapping()
        drawing = ["UniStation_Line", "UniStation_Wire", "UniStation_Circle",
                   "UniStation_Arc", "UniStation_Rectangle", "UniStation_Freeform"]
        manipulation = ["UniStation_Copy", "UniStation_Move", "UniStation_Scale",
                        "UniStation_Rotate", "UniStation_Mirror", "UniStation_Array"]
        edit_palette = "UniStation_EditPalette"
        palette = ["UniStation_ImportPalette", "UniStation_ExportPalette"]
        self.appendToolbar("UniStation", ["UniStation_CoordinateInput", level_manager, plot_pdf, edit_palette])
        self.appendToolbar("Рисование", drawing)
        self.appendToolbar("Манипуляции", manipulation)
        self.appendToolbar("Атрибуты", ["UniStation_ActiveLayer", "UniStation_ActiveColor", "UniStation_ActiveLineStyle",
                                      "UniStation_ActiveLineWeight", change_attributes])
        self.appendToolbar("Привязки", snaps)
        self.appendMenu("UniStation", drawing + manipulation +
                        ["UniStation_Cancel", "Separator", "UniStation_Reset", "UniStation_CoordinateInput",
                         level_manager, assign_level, plot_pdf, "UniStation_Preferences"])
        self.appendMenu(QT_TRANSLATE_NOOP('Workbench', 'Palette'), [change_attributes, edit_palette] + palette)

    def Activated(self):
        from unistation.snapping import activate as activate_snapping
        activate_snapping()
        from unistation.mouse import activate as activate_mouse
        activate_mouse()
        from unistation.attributes_gui import activate
        activate()
        from unistation.level_visibility_gui import activate as activate_level_visibility
        activate_level_visibility()
        from unistation.level_ui import activate as activate_level_ui
        activate_level_ui()
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
        from unistation.level_visibility_gui import deactivate as deactivate_level_visibility
        deactivate_level_visibility()
        from unistation.level_ui import deactivate as deactivate_level_ui
        deactivate_level_ui()
        from unistation.toolbar_titles import deactivate as deactivate_titles
        deactivate_titles()
        from unistation.gui import cancel
        cancel()

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(UniStationWorkbench())
