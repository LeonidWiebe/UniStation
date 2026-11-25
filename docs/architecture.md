# Architecture / Архитектура

UniStation is an external FreeCAD Python workbench. It uses the public AxisFlow
point-input API and FreeCAD/Draft geometry factories. It does not patch FreeCAD
or replace Draft's own Line tool.

```text
InitGui.py: commands, menus, five toolbars, activation/teardown
  gui.py: FreeCAD/Qt adapter, Coin preview, document/view guards
    InputSession: AxisFlow ownership, callbacks, generations, cleanup
      LineSession / WireSession / PlanarSession(Circle, Arc) / TransformSession
    Draft / Part geometry -> document transactions for confirmed geometry
```

## Input and geometry

AxisFlow returns world points. Sessions retain copied accepted points and
validate them before construction. The initial Draft WorkingPlane initializes
the compass; new/changed commands must use the current AxisFlow state while
running. PlanarSession reads `getCompassInfo` before validation/dynamics.
Circle's preview/result follow that orientation. Arc's final plane comes from
its three accepted world points, including after compass rotation.

Preview uses Coin nodes, not document geometry. Circle uses a 128-segment
display preview; final Circle/Arc geometry is exact Draft/Part geometry.
Line commits each segment separately. The continuation option keeps its
session active and uses the endpoint for the next preview and compass origin.
Circle commits after two valid points and Arc after three. Wire commits all
accepted segments together on finish or close. Move/Copy defer the commit to
the next Qt event cycle.

Wire stores accepted vertices and the circular segments that join them.
`wire_arc.py` computes each arc in the compass plane at center confirmation.
Wire temporarily switches AxisFlow to polar mode while placing the endpoint.
Straight-only Wire uses Draft. A Wire with arcs is one `Part::Feature` whose
`Part.Wire` holds exact straight and circular edges. Separate Coin nodes
display the temporary circle and guide radii.

Transactions encompass geometry creation and new-object indexed attributes.
Failures abort the transaction. Post-commit result selection is a separate UI
step controlled by a preference. Active drawing attributes are reread before
commit and can update the same Coin preview nodes during input.

## Lifecycle and UI

InputSession owns one AxisFlow session and idempotent cleanup. Document/view
guards, a document observer and workbench deactivation stop obsolete input.
An input generation prevents old callbacks and deferred commits from affecting
a newer state after Reset. Historical native lifecycle observations remain
unresolved; see [status](status.md).

Reset is a logical event handled by the active command. It rewinds, then exits
on another Reset without a new accepted point. Cancel is unconditional cleanup.
The modeless coordinate window is bound to a supported session/generation and
clears on context changes. Its close action leaves drawing active.

`palette.py`, `attributes.py` and `line_weights.py` maintain document-owned
`Ustn` metadata. Active attributes apply to new objects; separate palette tools
can change existing supported objects. levels.py and element_attributes.py store FCStd layer definitions, assignments and persistent attribute sources; level visibility/UI adapters enforce supported display and Lock behavior. The direct PDF pipeline exports planar XY geometry.

## По-русски

InitGui регистрирует команды и панели. `gui.py` связывает FreeCAD/Qt/Coin с
сессиями, независимыми от GUI. InputSession владеет вводом AxisFlow, поколением
callbacks и освобождением ресурсов. Предпросмотр существует в сцене Coin.
Line создаёт каждый отрезок отдельной транзакцией. Wire сохраняет все
принятые сегменты одной транзакцией при завершении. Смешанная линия состоит
из прямых и точных круговых рёбер Part.

Circle/Arc читают текущее состояние компаса. Принятые мировые точки Arc
сохраняются. Живые атрибуты обновляют Coin, затем перечитываются перед commit.
Reset откатывает состояние команды; Cancel полностью завершает ввод.
Палитра, активные атрибуты и толщины хранятся в метаданных `Ustn` документа;
таблица слоёв и источники атрибутов также сохраняются в FCStd.
