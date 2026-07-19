---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/house_photo_mapper/presentation/views/report_color_dialog.py
  - src/house_photo_mapper/domain/services/persistence.py
  - src/house_photo_mapper/presentation/views/main_window.py
autonomous: true
requirements: []
must_haves:
  truths:
    - User can choose "Use original colors" or "Override with custom color" before report generation
    - Custom color selection uses QColorDialog for color picking
    - Selected color preference persists across sessions via QSettings
    - Report annotations use the override color when set, original colors when not
  artifacts:
    - src/house_photo_mapper/presentation/views/report_color_dialog.py
  key_links:
    - ReportColorDialog → main_window._generate_report flow
    - PersistenceService → QSettings read/write for report color preference
    - color override → ReportPageData.color field in pages_data construction
---

<objective>
Add a report color configuration dialog that lets users choose between original annotation colors and a user-selected override color for PDF exports, with settings persisted via QSettings.

Purpose: Gives users control over annotation appearance in exported reports, useful when original colors clash with print or presentation requirements.
Output: New ReportColorDialog class, QSettings integration in PersistenceService, wired into the report generation flow.
</objective>

<execution_context>
@/Users/sorin/.config/opencode/gsd-core/workflows/execute-plan.md
@/Users/sorin/.config/opencode/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@src/house_photo_mapper/presentation/views/layout_dialog.py
@src/house_photo_mapper/presentation/views/main_window.py
@src/house_photo_mapper/domain/services/report_generator.py
@src/house_photo_mapper/domain/services/persistence.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create ReportColorDialog</name>
  <files>src/house_photo_mapper/presentation/views/report_color_dialog.py</files>
  <action>
Create `src/house_photo_mapper/presentation/views/report_color_dialog.py` following the exact pattern of `layout_dialog.py`.

Class `ReportColorDialog(QDialog)` with:
- Window title "Report Colors", minimum size 350x200
- QGroupBox "Annotation Colors" containing a QFormLayout
- QComboBox with two items: "Use original colors", "Override with custom color"
- A QPushButton "Choose Color..." next to a color preview widget (a QLabel with fixed 24x24 size showing the current override color as background, plus hex text) — enabled only when override is selected
- QPushButton "Choose Color..." opens QColorDialog, updates the preview label and stores the hex string
- OK / Cancel buttons in a horizontal layout (matching layout_dialog.py pattern)
- Constructor accepts optional `current_mode: str = "original"` and `current_color: str = "#DC2828"` to restore saved state
- `get_selected_mode() -> str` returns `"original"` or `"override"`
- `get_selected_color() -> str` returns the hex color string (e.g. `"#FF0000"`)
- Connect combo box `currentIndexChanged` to enable/disable the color button (disable when index 0 = original)

Use PySide6 imports: QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QComboBox, QPushButton, QLabel, QColorDialog, Qt.
  </action>
  <verify>
    <automated>cd /Users/sorin/src/my/house-photo-mapper && python -c "from house_photo_mapper.presentation.views.report_color_dialog import ReportColorDialog; print('import OK')"</automated>
  </verify>
  <done>ReportColorDialog exists and is importable with correct API: get_selected_mode() and get_selected_color()</done>
</task>

<task type="auto">
  <name>Task 2: Add QSettings persistence for report color preference</name>
  <files>src/house_photo_mapper/domain/services/persistence.py</files>
  <action>
Add two methods to `PersistenceService` in `src/house_photo_mapper/domain/services/persistence.py`, following the exact pattern of existing QSettings methods (e.g. `load_auto_save_enabled` / `save_auto_save_enabled`):

1. `load_report_color_mode() -> str` — reads `self._settings.value("reportColor/mode", "original", type=str)`. Returns `"original"` or `"override"`.

2. `save_report_color_mode(mode: str) -> None` — writes `self._settings.setValue("reportColor/mode", mode)`.

3. `load_report_color_override() -> str` — reads `self._settings.value("reportColor/override", "#DC2828", type=str)`. Returns hex color string.

4. `save_report_color_override(color: str) -> None` — writes `self._settings.setValue("reportColor/override", color)`.

Place these methods after the existing auto_save methods (around line 425) to keep QSettings methods grouped together. Use the same docstring pattern as existing methods.
  </action>
  <verify>
    <automated>cd /Users/sorin/src/my/house-photo-mapper && python -c "
from house_photo_mapper.domain.services.persistence import PersistenceService
p = PersistenceService()
p.save_report_color_mode('override')
p.save_report_color_override('#FF0000')
assert p.load_report_color_mode() == 'override'
assert p.load_report_color_override() == '#FF0000'
p.save_report_color_mode('original')
assert p.load_report_color_mode() == 'original'
print('persistence OK')
"</automated>
  </verify>
  <done>PersistenceService can load/save report color mode and override color via QSettings</done>
</task>

<task type="auto">
  <name>Task 3: Wire dialog into report generation flow</name>
  <files>src/house_photo_mapper/presentation/views/main_window.py</files>
  <action>
Modify `_generate_report` in `src/house_photo_mapper/presentation/views/main_window.py` to show the ReportColorDialog after the LayoutDialog and apply color overrides.

Changes:

1. **Add import** at top of file (after the LayoutDialog import around line 27):
   `from house_photo_mapper.presentation.views.report_color_dialog import ReportColorDialog`

2. **In `_generate_report` method** (around line 1066-1070), after the LayoutDialog is accepted and before building pages_data:
   - Load saved preferences: `color_mode = self._persistence.load_report_color_mode()` and `color_override = self._persistence.load_report_color_override()`
   - Show `ReportColorDialog(current_mode=color_mode, current_color=color_override, parent=self)`
   - If rejected, return early (same pattern as LayoutDialog)
   - Save the user's choices: `self._persistence.save_report_color_mode(dialog.get_selected_mode())` and `self._persistence.save_report_color_override(dialog.get_selected_color())`
   - Store `use_override = (dialog.get_selected_mode() == "override")` and `override_color = dialog.get_selected_color()`

3. **In the pages_data loop** (around line 1170), when building `ReportPageData`, apply the override:
   - Replace `color=ann.color` with `color=override_color if use_override else ann.color`

This is a minimal, surgical change. The existing flow is unchanged when "original" is selected.
  </action>
  <verify>
    <automated>cd /Users/sorin/src/my/house-photo-mapper && python -c "
from house_photo_mapper.presentation.views.main_window import MainWindow
import inspect
src = inspect.getsource(MainWindow._generate_report)
assert 'ReportColorDialog' in src, 'Dialog not wired'
assert 'override_color' in src, 'Override not applied'
assert 'save_report_color_mode' in src, 'Mode not persisted'
print('wiring OK')
"</automated>
  </verify>
  <done>Report generation shows color dialog, applies override to annotations, and persists user preference</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| User input → QSettings | User-selected color stored in QSettings; no injection risk (PySide6 handles serialization) |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-quick-01 | Tampering | QSettings storage | low | accept | QSettings is user-scope only; local storage, no remote vector |
| T-quick-02 | DoS | QColorDialog | low | accept | Standard Qt widget, no resource exhaustion risk |
</threat_model>

<verification>
- `ReportColorDialog` imports and can be instantiated with default arguments
- `PersistenceService` round-trips color mode and override color through QSettings
- `MainWindow._generate_report` references ReportColorDialog, saves preferences, and applies override to page data
- Existing report generation behavior unchanged when "original" mode is selected
</verification>

<success_criteria>
- User can open report generation, see a color configuration step after layout selection
- User can pick "Use original colors" (default) or "Override with custom color" + color picker
- Selection persists across app restarts via QSettings
- When override is selected, all annotations in the PDF use the chosen color
</success_criteria>

<output>
Create `.planning/quick/260719-lpc-add-a-report-configuration-dialog-where-/260719-lpc-01-SUMMARY.md` when done
</output>
