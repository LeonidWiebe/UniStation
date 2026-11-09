"""UniStation profile preferences; input action IDs never depend on UI language."""

import FreeCAD as App
from unistation.input_events import InputType


PATH = "User parameter:BaseApp/Preferences/Mod/UniStation/Mouse"
NATIVE = "Native"
RESET = InputType.RESET.value
RIGHT_BUTTON = "RightButtonAction"
ACTIONS = (NATIVE, RESET)
OPERATIONS_PATH = "User parameter:BaseApp/Preferences/Mod/UniStation/Operations"
AUTO_SELECT = "AutoSelectResult"


def right_button_action():
    value = App.ParamGet(PATH).GetString(RIGHT_BUTTON, NATIVE)
    return value if value in ACTIONS else NATIVE


def save_right_button_action(action):
    save_settings(action, auto_select_result())


def auto_select_result():
    return App.ParamGet(OPERATIONS_PATH).GetBool(AUTO_SELECT, False)


def save_settings(action, auto_select):
    if action not in ACTIONS:
        raise ValueError("Unsupported UniStation mouse action")
    if type(auto_select) is not bool:
        raise ValueError("Unsupported UniStation selection setting")
    params = App.ParamGet(PATH)
    operations = App.ParamGet(OPERATIONS_PATH)
    previous = params.GetString(RIGHT_BUTTON, NATIVE)
    previous_auto_select = operations.GetBool(AUTO_SELECT, False)
    try:
        params.SetString(RIGHT_BUTTON, action)
        operations.SetBool(AUTO_SELECT, auto_select)
        App.saveParameter()
    except Exception:
        # Keep the live assignment consistent with the failed Apply operation.
        params.SetString(RIGHT_BUTTON, previous)
        operations.SetBool(AUTO_SELECT, previous_auto_select)
        raise
