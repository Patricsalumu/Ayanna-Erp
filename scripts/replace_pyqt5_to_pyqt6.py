"""
Script to replace PyQt5 imports with PyQt6 across the repository.
Usage (from project root):
    python scripts/replace_pyqt5_to_pyqt6.py
This will:
- Replace occurrences of 'from PyQt5' -> 'from PyQt6'
- Replace occurrences of 'import PyQt5' -> 'import PyQt6'
- Update enum/flag qualifications for PyQt6 API
- Create a backup copy for each modified file with suffix .bak
"""
import os
import sys
import re

root = os.path.abspath(os.getcwd())
changed = []

# Pattern replacements to adapt PyQt5 → PyQt6 API differences
# Order matters - more specific patterns should come first
replacements = [
    # ============== Qt Namespace ==============
    # Alignment flags
    (r'\bQt\.AlignCenter\b', 'Qt.AlignmentFlag.AlignCenter'),
    (r'\bQt\.AlignLeft\b', 'Qt.AlignmentFlag.AlignLeft'),
    (r'\bQt\.AlignRight\b', 'Qt.AlignmentFlag.AlignRight'),
    (r'\bQt\.AlignTop\b', 'Qt.AlignmentFlag.AlignTop'),
    (r'\bQt\.AlignBottom\b', 'Qt.AlignmentFlag.AlignBottom'),
    (r'\bQt\.AlignVCenter\b', 'Qt.AlignmentFlag.AlignVCenter'),
    (r'\bQt\.AlignHCenter\b', 'Qt.AlignmentFlag.AlignHCenter'),
    (r'\bQt\.AlignJustify\b', 'Qt.AlignmentFlag.AlignJustify'),
    
    # Window flags
    (r'\bQt\.WindowStaysOnTopHint\b', 'Qt.WindowType.WindowStaysOnTopHint'),
    (r'\bQt\.FramelessWindowHint\b', 'Qt.WindowType.FramelessWindowHint'),
    (r'\bQt\.Dialog\b', 'Qt.WindowType.Dialog'),
    (r'\bQt\.Window\b', 'Qt.WindowType.Window'),
    (r'\bQt\.Tool\b', 'Qt.WindowType.Tool'),
    (r'\bQt\.Popup\b', 'Qt.WindowType.Popup'),
    (r'\bQt\.Sheet\b', 'Qt.WindowType.Sheet'),
    (r'\bQt\.Drawer\b', 'Qt.WindowType.Drawer'),
    (r'\bQt\.SplashScreen\b', 'Qt.WindowType.SplashScreen'),
    (r'\bQt\.SubWindow\b', 'Qt.WindowType.SubWindow'),
    (r'\bQt\.WindowModal\b', 'Qt.WindowModality.WindowModal'),
    (r'\bQt\.ApplicationModal\b', 'Qt.WindowModality.ApplicationModal'),
    (r'\bQt\.NonModal\b', 'Qt.WindowModality.NonModal'),
    
    # Orientation
    (r'\bQt\.Horizontal\b', 'Qt.Orientation.Horizontal'),
    (r'\bQt\.Vertical\b', 'Qt.Orientation.Vertical'),
    
    # Focus Policy
    (r'\bQt\.StrongFocus\b', 'Qt.FocusPolicy.StrongFocus'),
    (r'\bQt\.NoFocus\b', 'Qt.FocusPolicy.NoFocus'),
    (r'\bQt\.TabFocus\b', 'Qt.FocusPolicy.TabFocus'),
    (r'\bQt\.ClickFocus\b', 'Qt.FocusPolicy.ClickFocus'),
    (r'\bQt\.WheelFocus\b', 'Qt.FocusPolicy.WheelFocus'),
    
    # Cursor shape
    (r'\bQt\.WaitCursor\b', 'Qt.CursorShape.WaitCursor'),
    (r'\bQt\.ArrowCursor\b', 'Qt.CursorShape.ArrowCursor'),
    (r'\bQt\.PointingHandCursor\b', 'Qt.CursorShape.PointingHandCursor'),
    (r'\bQt\.CrossCursor\b', 'Qt.CursorShape.CrossCursor'),
    (r'\bQt\.IBeamCursor\b', 'Qt.CursorShape.IBeamCursor'),
    
    # Scroll bar policy
    (r'\bQt\.ScrollBarAsNeeded\b', 'Qt.ScrollBarPolicy.ScrollBarAsNeeded'),
    (r'\bQt\.ScrollBarAlwaysOn\b', 'Qt.ScrollBarPolicy.ScrollBarAlwaysOn'),
    (r'\bQt\.ScrollBarAlwaysOff\b', 'Qt.ScrollBarPolicy.ScrollBarAlwaysOff'),
    
    # Sort order
    (r'\bQt\.AscendingOrder\b', 'Qt.SortOrder.AscendingOrder'),
    (r'\bQt\.DescendingOrder\b', 'Qt.SortOrder.DescendingOrder'),
    
    # Text format
    (r'\bQt\.RichText\b', 'Qt.TextFormat.RichText'),
    (r'\bQt\.PlainText\b', 'Qt.TextFormat.PlainText'),
    (r'\bQt\.AutoText\b', 'Qt.TextFormat.AutoText'),
    (r'\bQt\.MarkdownText\b', 'Qt.TextFormat.MarkdownText'),
    
    # Check state
    (r'\bQt\.Checked\b', 'Qt.CheckState.Checked'),
    (r'\bQt\.Unchecked\b', 'Qt.CheckState.Unchecked'),
    (r'\bQt\.PartiallyChecked\b', 'Qt.CheckState.PartiallyChecked'),
    
    # Item flags
    (r'\bQt\.ItemIsSelectable\b', 'Qt.ItemFlag.ItemIsSelectable'),
    (r'\bQt\.ItemIsEditable\b', 'Qt.ItemFlag.ItemIsEditable'),
    (r'\bQt\.ItemIsEnabled\b', 'Qt.ItemFlag.ItemIsEnabled'),
    (r'\bQt\.ItemIsUserCheckable\b', 'Qt.ItemFlag.ItemIsUserCheckable'),
    
    # Item data role
    (r'\bQt\.UserRole\b', 'Qt.ItemDataRole.UserRole'),
    (r'\bQt\.DisplayRole\b', 'Qt.ItemDataRole.DisplayRole'),
    (r'\bQt\.EditRole\b', 'Qt.ItemDataRole.EditRole'),
    (r'\bQt\.DecorationRole\b', 'Qt.ItemDataRole.DecorationRole'),
    (r'\bQt\.ToolTipRole\b', 'Qt.ItemDataRole.ToolTipRole'),
    (r'\bQt\.StatusTipRole\b', 'Qt.ItemDataRole.StatusTipRole'),
    (r'\bQt\.WhatsThisRole\b', 'Qt.ItemDataRole.WhatsThisRole'),
    (r'\bQt\.BackgroundRole\b', 'Qt.ItemDataRole.BackgroundRole'),
    (r'\bQt\.ForegroundRole\b', 'Qt.ItemDataRole.ForegroundRole'),
    (r'\bQt\.TextAlignmentRole\b', 'Qt.ItemDataRole.TextAlignmentRole'),
    
    # Aspect ratio mode
    (r'\bQt\.KeepAspectRatio\b', 'Qt.AspectRatioMode.KeepAspectRatio'),
    (r'\bQt\.IgnoreAspectRatio\b', 'Qt.AspectRatioMode.IgnoreAspectRatio'),
    (r'\bQt\.KeepAspectRatioByExpanding\b', 'Qt.AspectRatioMode.KeepAspectRatioByExpanding'),
    
    # Transformation mode
    (r'\bQt\.SmoothTransformation\b', 'Qt.TransformationMode.SmoothTransformation'),
    (r'\bQt\.FastTransformation\b', 'Qt.TransformationMode.FastTransformation'),
    
    # Key
    (r'\bQt\.Key_Return\b', 'Qt.Key.Key_Return'),
    (r'\bQt\.Key_Enter\b', 'Qt.Key.Key_Enter'),
    (r'\bQt\.Key_Escape\b', 'Qt.Key.Key_Escape'),
    (r'\bQt\.Key_Tab\b', 'Qt.Key.Key_Tab'),
    (r'\bQt\.Key_Backtab\b', 'Qt.Key.Key_Backtab'),
    (r'\bQt\.Key_Delete\b', 'Qt.Key.Key_Delete'),
    (r'\bQt\.Key_Backspace\b', 'Qt.Key.Key_Backspace'),
    (r'\bQt\.Key_Space\b', 'Qt.Key.Key_Space'),
    (r'\bQt\.Key_Up\b', 'Qt.Key.Key_Up'),
    (r'\bQt\.Key_Down\b', 'Qt.Key.Key_Down'),
    (r'\bQt\.Key_Left\b', 'Qt.Key.Key_Left'),
    (r'\bQt\.Key_Right\b', 'Qt.Key.Key_Right'),
    
    # ============== QFont ==============
    (r'\bQFont\.Bold\b', 'QFont.Weight.Bold'),
    (r'\bQFont\.Normal\b', 'QFont.Weight.Normal'),
    (r'\bQFont\.Light\b', 'QFont.Weight.Light'),
    (r'\bQFont\.DemiBold\b', 'QFont.Weight.DemiBold'),
    (r'\bQFont\.Black\b', 'QFont.Weight.Black'),
    (r'\bQFont\.Thin\b', 'QFont.Weight.Thin'),
    (r'\bQFont\.ExtraLight\b', 'QFont.Weight.ExtraLight'),
    (r'\bQFont\.Medium\b', 'QFont.Weight.Medium'),
    (r'\bQFont\.ExtraBold\b', 'QFont.Weight.ExtraBold'),
    
    # ============== QFrame ==============
    (r'\bQFrame\.HLine\b', 'QFrame.Shape.HLine'),
    (r'\bQFrame\.VLine\b', 'QFrame.Shape.VLine'),
    (r'\bQFrame\.NoFrame\b', 'QFrame.Shape.NoFrame'),
    (r'\bQFrame\.Box\b', 'QFrame.Shape.Box'),
    (r'\bQFrame\.Panel\b', 'QFrame.Shape.Panel'),
    (r'\bQFrame\.StyledPanel\b', 'QFrame.Shape.StyledPanel'),
    (r'\bQFrame\.WinPanel\b', 'QFrame.Shape.WinPanel'),
    (r'\bQFrame\.Sunken\b', 'QFrame.Shadow.Sunken'),
    (r'\bQFrame\.Raised\b', 'QFrame.Shadow.Raised'),
    (r'\bQFrame\.Plain\b', 'QFrame.Shadow.Plain'),
    
    # ============== QSizePolicy ==============
    (r'\bQSizePolicy\.Expanding\b', 'QSizePolicy.Policy.Expanding'),
    (r'\bQSizePolicy\.Fixed\b', 'QSizePolicy.Policy.Fixed'),
    (r'\bQSizePolicy\.Minimum\b', 'QSizePolicy.Policy.Minimum'),
    (r'\bQSizePolicy\.Maximum\b', 'QSizePolicy.Policy.Maximum'),
    (r'\bQSizePolicy\.Preferred\b', 'QSizePolicy.Policy.Preferred'),
    (r'\bQSizePolicy\.MinimumExpanding\b', 'QSizePolicy.Policy.MinimumExpanding'),
    (r'\bQSizePolicy\.Ignored\b', 'QSizePolicy.Policy.Ignored'),
    
    # ============== QLineEdit ==============
    (r'\bQLineEdit\.Password\b', 'QLineEdit.EchoMode.Password'),
    (r'\bQLineEdit\.Normal\b', 'QLineEdit.EchoMode.Normal'),
    (r'\bQLineEdit\.NoEcho\b', 'QLineEdit.EchoMode.NoEcho'),
    (r'\bQLineEdit\.PasswordEchoOnEdit\b', 'QLineEdit.EchoMode.PasswordEchoOnEdit'),
    
    # ============== QAbstractItemView ==============
    (r'\bQAbstractItemView\.SelectRows\b', 'QAbstractItemView.SelectionBehavior.SelectRows'),
    (r'\bQAbstractItemView\.SelectColumns\b', 'QAbstractItemView.SelectionBehavior.SelectColumns'),
    (r'\bQAbstractItemView\.SelectItems\b', 'QAbstractItemView.SelectionBehavior.SelectItems'),
    (r'\bQAbstractItemView\.SingleSelection\b', 'QAbstractItemView.SelectionMode.SingleSelection'),
    (r'\bQAbstractItemView\.MultiSelection\b', 'QAbstractItemView.SelectionMode.MultiSelection'),
    (r'\bQAbstractItemView\.ExtendedSelection\b', 'QAbstractItemView.SelectionMode.ExtendedSelection'),
    (r'\bQAbstractItemView\.NoSelection\b', 'QAbstractItemView.SelectionMode.NoSelection'),
    (r'\bQAbstractItemView\.NoEditTriggers\b', 'QAbstractItemView.EditTrigger.NoEditTriggers'),
    (r'\bQAbstractItemView\.DoubleClicked\b', 'QAbstractItemView.EditTrigger.DoubleClicked'),
    (r'\bQAbstractItemView\.CurrentChanged\b', 'QAbstractItemView.EditTrigger.CurrentChanged'),
    (r'\bQAbstractItemView\.SelectedClicked\b', 'QAbstractItemView.EditTrigger.SelectedClicked'),
    (r'\bQAbstractItemView\.EditKeyPressed\b', 'QAbstractItemView.EditTrigger.EditKeyPressed'),
    (r'\bQAbstractItemView\.AnyKeyPressed\b', 'QAbstractItemView.EditTrigger.AnyKeyPressed'),
    (r'\bQAbstractItemView\.AllEditTriggers\b', 'QAbstractItemView.EditTrigger.AllEditTriggers'),
    
    # ============== QTableWidget / QTableView ==============
    (r'\bQTableWidget\.SelectRows\b', 'QAbstractItemView.SelectionBehavior.SelectRows'),
    (r'\bQTableWidget\.SelectColumns\b', 'QAbstractItemView.SelectionBehavior.SelectColumns'),
    (r'\bQTableWidget\.SelectItems\b', 'QAbstractItemView.SelectionBehavior.SelectItems'),
    
    # ============== QHeaderView ==============
    (r'\bQHeaderView\.Stretch\b', 'QHeaderView.ResizeMode.Stretch'),
    (r'\bQHeaderView\.ResizeToContents\b', 'QHeaderView.ResizeMode.ResizeToContents'),
    (r'\bQHeaderView\.Fixed\b', 'QHeaderView.ResizeMode.Fixed'),
    (r'\bQHeaderView\.Interactive\b', 'QHeaderView.ResizeMode.Interactive'),
    
    # ============== QMessageBox ==============
    (r'\bQMessageBox\.Yes\b', 'QMessageBox.StandardButton.Yes'),
    (r'\bQMessageBox\.No\b', 'QMessageBox.StandardButton.No'),
    (r'\bQMessageBox\.Ok\b', 'QMessageBox.StandardButton.Ok'),
    (r'\bQMessageBox\.Cancel\b', 'QMessageBox.StandardButton.Cancel'),
    (r'\bQMessageBox\.Close\b', 'QMessageBox.StandardButton.Close'),
    (r'\bQMessageBox\.Save\b', 'QMessageBox.StandardButton.Save'),
    (r'\bQMessageBox\.Discard\b', 'QMessageBox.StandardButton.Discard'),
    (r'\bQMessageBox\.Apply\b', 'QMessageBox.StandardButton.Apply'),
    (r'\bQMessageBox\.Reset\b', 'QMessageBox.StandardButton.Reset'),
    (r'\bQMessageBox\.RestoreDefaults\b', 'QMessageBox.StandardButton.RestoreDefaults'),
    (r'\bQMessageBox\.Help\b', 'QMessageBox.StandardButton.Help'),
    (r'\bQMessageBox\.SaveAll\b', 'QMessageBox.StandardButton.SaveAll'),
    (r'\bQMessageBox\.YesToAll\b', 'QMessageBox.StandardButton.YesToAll'),
    (r'\bQMessageBox\.NoToAll\b', 'QMessageBox.StandardButton.NoToAll'),
    (r'\bQMessageBox\.Abort\b', 'QMessageBox.StandardButton.Abort'),
    (r'\bQMessageBox\.Retry\b', 'QMessageBox.StandardButton.Retry'),
    (r'\bQMessageBox\.Ignore\b', 'QMessageBox.StandardButton.Ignore'),
    (r'\bQMessageBox\.Information\b', 'QMessageBox.Icon.Information'),
    (r'\bQMessageBox\.Warning\b', 'QMessageBox.Icon.Warning'),
    (r'\bQMessageBox\.Critical\b', 'QMessageBox.Icon.Critical'),
    (r'\bQMessageBox\.Question\b', 'QMessageBox.Icon.Question'),
    (r'\bQMessageBox\.NoIcon\b', 'QMessageBox.Icon.NoIcon'),
    
    # ============== QDialogButtonBox ==============
    (r'\bQDialogButtonBox\.Ok\b', 'QDialogButtonBox.StandardButton.Ok'),
    (r'\bQDialogButtonBox\.Cancel\b', 'QDialogButtonBox.StandardButton.Cancel'),
    (r'\bQDialogButtonBox\.Yes\b', 'QDialogButtonBox.StandardButton.Yes'),
    (r'\bQDialogButtonBox\.No\b', 'QDialogButtonBox.StandardButton.No'),
    (r'\bQDialogButtonBox\.Apply\b', 'QDialogButtonBox.StandardButton.Apply'),
    (r'\bQDialogButtonBox\.Close\b', 'QDialogButtonBox.StandardButton.Close'),
    (r'\bQDialogButtonBox\.Save\b', 'QDialogButtonBox.StandardButton.Save'),
    (r'\bQDialogButtonBox\.Discard\b', 'QDialogButtonBox.StandardButton.Discard'),
    (r'\bQDialogButtonBox\.Reset\b', 'QDialogButtonBox.StandardButton.Reset'),
    (r'\bQDialogButtonBox\.RestoreDefaults\b', 'QDialogButtonBox.StandardButton.RestoreDefaults'),
    (r'\bQDialogButtonBox\.Help\b', 'QDialogButtonBox.StandardButton.Help'),
    
    # ============== QFileDialog ==============
    (r'\bQFileDialog\.ShowDirsOnly\b', 'QFileDialog.Option.ShowDirsOnly'),
    (r'\bQFileDialog\.DontResolveSymlinks\b', 'QFileDialog.Option.DontResolveSymlinks'),
    (r'\bQFileDialog\.DontConfirmOverwrite\b', 'QFileDialog.Option.DontConfirmOverwrite'),
    (r'\bQFileDialog\.DontUseNativeDialog\b', 'QFileDialog.Option.DontUseNativeDialog'),
    (r'\bQFileDialog\.ReadOnly\b', 'QFileDialog.Option.ReadOnly'),
    (r'\bQFileDialog\.HideNameFilterDetails\b', 'QFileDialog.Option.HideNameFilterDetails'),
    
    # ============== QTabWidget ==============
    (r'\bQTabWidget\.North\b', 'QTabWidget.TabPosition.North'),
    (r'\bQTabWidget\.South\b', 'QTabWidget.TabPosition.South'),
    (r'\bQTabWidget\.West\b', 'QTabWidget.TabPosition.West'),
    (r'\bQTabWidget\.East\b', 'QTabWidget.TabPosition.East'),
    
    # ============== QComboBox ==============
    (r'\bQComboBox\.InsertAtTop\b', 'QComboBox.InsertPolicy.InsertAtTop'),
    (r'\bQComboBox\.InsertAtBottom\b', 'QComboBox.InsertPolicy.InsertAtBottom'),
    (r'\bQComboBox\.InsertAtCurrent\b', 'QComboBox.InsertPolicy.InsertAtCurrent'),
    (r'\bQComboBox\.InsertAfterCurrent\b', 'QComboBox.InsertPolicy.InsertAfterCurrent'),
    (r'\bQComboBox\.InsertBeforeCurrent\b', 'QComboBox.InsertPolicy.InsertBeforeCurrent'),
    (r'\bQComboBox\.InsertAlphabetically\b', 'QComboBox.InsertPolicy.InsertAlphabetically'),
    (r'\bQComboBox\.NoInsert\b', 'QComboBox.InsertPolicy.NoInsert'),
    
    # ============== QPalette ==============
    (r'\bQPalette\.Window\b', 'QPalette.ColorRole.Window'),
    (r'\bQPalette\.WindowText\b', 'QPalette.ColorRole.WindowText'),
    (r'\bQPalette\.Base\b', 'QPalette.ColorRole.Base'),
    (r'\bQPalette\.AlternateBase\b', 'QPalette.ColorRole.AlternateBase'),
    (r'\bQPalette\.ToolTipBase\b', 'QPalette.ColorRole.ToolTipBase'),
    (r'\bQPalette\.ToolTipText\b', 'QPalette.ColorRole.ToolTipText'),
    (r'\bQPalette\.Text\b', 'QPalette.ColorRole.Text'),
    (r'\bQPalette\.Button\b', 'QPalette.ColorRole.Button'),
    (r'\bQPalette\.ButtonText\b', 'QPalette.ColorRole.ButtonText'),
    (r'\bQPalette\.BrightText\b', 'QPalette.ColorRole.BrightText'),
    (r'\bQPalette\.Link\b', 'QPalette.ColorRole.Link'),
    (r'\bQPalette\.Highlight\b', 'QPalette.ColorRole.Highlight'),
    (r'\bQPalette\.HighlightedText\b', 'QPalette.ColorRole.HighlightedText'),
    
    # ============== QImage ==============
    (r'\bQImage\.Format_RGB32\b', 'QImage.Format.Format_RGB32'),
    (r'\bQImage\.Format_ARGB32\b', 'QImage.Format.Format_ARGB32'),
    (r'\bQImage\.Format_RGB888\b', 'QImage.Format.Format_RGB888'),
    (r'\bQImage\.Format_Grayscale8\b', 'QImage.Format.Format_Grayscale8'),
    
    # ============== QTextCursor ==============
    (r'\bQTextCursor\.MoveAnchor\b', 'QTextCursor.MoveMode.MoveAnchor'),
    (r'\bQTextCursor\.KeepAnchor\b', 'QTextCursor.MoveMode.KeepAnchor'),
    (r'\bQTextCursor\.End\b', 'QTextCursor.MoveOperation.End'),
    (r'\bQTextCursor\.Start\b', 'QTextCursor.MoveOperation.Start'),
    
    # ============== exec_() -> exec() ==============
    (r'\.exec_\(\)', '.exec()'),
]

def apply_replacements(content: str) -> str:
    new = content
    
    # Basic textual replacement for PyQt5 -> PyQt6
    new = new.replace('from PyQt5', 'from PyQt6')
    new = new.replace('import PyQt5', 'import PyQt6')
    new = new.replace('PyQt5.', 'PyQt6.')
    
    # Apply regex replacements for enums and flags
    for pattern, repl in replacements:
        new = re.sub(pattern, repl, new)
    
    return new


# Main execution
for dirpath, dirnames, filenames in os.walk(root):
    # Skip virtual env and dist/build folders
    if any(part in ('venv', 'build', 'dist', '__pycache__', '.git') for part in dirpath.split(os.sep)):
        continue
    for fname in filenames:
        if not fname.endswith('.py'):
            continue
        # Skip this script itself
        if fname == 'replace_pyqt5_to_pyqt6.py':
            continue
        fpath = os.path.join(dirpath, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        new = apply_replacements(content)
        if new != content:
            # Create backup
            backup_path = fpath + '.pyqt5.bak'
            with open(backup_path, 'w', encoding='utf-8') as b:
                b.write(content)
            # Write new content
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(new)
            changed.append(fpath)

print('=' * 60)
print('PyQt5 to PyQt6 Migration Complete')
print('=' * 60)
print(f'\nModified {len(changed)} files:')
for p in changed:
    print(f'  ✓ {os.path.relpath(p, root)}')

print('\n' + '=' * 60)
print('IMPORTANT: Next steps')
print('=' * 60)
print('''
1. Update requirements.txt:
   - Replace: PyQt5>=5.15.0
   - With:    PyQt6>=6.4.0

2. Install PyQt6:
   pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip -y
   pip install PyQt6

3. Test the application and fix any remaining issues.

4. Backup files created with .pyqt5.bak extension.
''')
