import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QMovie
from undo_redo import UndoRedoActions
from notifications import warn_no_database, warn_no_sheet

# وحدات العمليات
from db_actions import DatabaseActions
from sheet_actions import SheetActions
from row_col_actions import RowColumnActions
from formatting import FormattingActions
from clipboard import ClipboardActions
from insert_files import InsertFilesActions
from signals import connect_signals

# -------------------------- مسارات ثابتة --------------------------
UI_PATH = r"C:\Users\nizar\Desktop\New folder\tab.ui"
LOGO_PATH = r"C:\Users\nizar\Desktop\New folder\logo.gif"


def load_main_ui():
    """تحميل واجهة المستخدم من ملف .ui وإعداد الشعار"""
    loader = QUiLoader()
    if not os.path.exists(UI_PATH):
        raise FileNotFoundError(f"ملف الواجهة غير موجود: {UI_PATH}")
    
    ui = loader.load(UI_PATH)
    
    # إعداد الشعار (GIF متحرك)
    logo_label = ui.findChild(QLabel, "logo")
    if logo_label and os.path.exists(LOGO_PATH):
        logo_label.setFixedSize(50, 50)
        movie = QMovie(LOGO_PATH)
        logo_label.setMovie(movie)
        movie.start()
    
    return ui


# -------------------------- MainWindow --------------------------
class MainWindow(
    QMainWindow,
    DatabaseActions,
    SheetActions,
    RowColumnActions,
    FormattingActions,
    ClipboardActions,
    InsertFilesActions,
    UndoRedoActions
):
    def __init__(self):
        super().__init__()

        # -------------------------- تحميل واجهة المستخدم --------------------------
        self.ui = load_main_ui()
        self.setCentralWidget(self.ui)

        # -------------------------- ربط العناصر الرئيسية --------------------------
        self._bind_ui_elements()

        # -------------------------- ربط جميع الإشارات --------------------------
        connect_signals(self)

        # -------------------------- ضبط حالة التحرير الافتراضية --------------------------
        self.cells_editable = False
        self._update_cell_editable_state()

        # -------------------------- تحميل أول ورقة إذا موجودة --------------------------
        if hasattr(self, "db_manager") and self.db_manager.current_sheet:
            self.load_sheet(self.db_manager.current_sheet)

        # -------------------------- ربط زر تحرير/قفل الخلايا --------------------------
        if self.btnEditCells:
            self.btnEditCells.clicked.connect(self.toggle_edit_cells)

        # -------------------------- ضبط اتجاه الجدول حسب dirCombo --------------------------
        if self.dirCombo:
            self.dirCombo.currentTextChanged.connect(self.change_table_direction)
            # تطبيق الاتجاه الافتراضي عند التحميل
            self.change_table_direction(self.dirCombo.currentText() or "من الشمال الى اليمين")

        # -------------------------- إنشاء undo/redo stacks --------------------------
        if not hasattr(self, "undo_stack"):
            self.undo_stack = []
        if not hasattr(self, "redo_stack"):
            self.redo_stack = []

        # -------------------------- ربط أزرار قاعدة البيانات وأوراق العمل مع التحقق --------------------------
        self._wrap_database_buttons()
        self._wrap_sheet_buttons()

    # -------------------------- وظائف مساعدة --------------------------
    def _bind_ui_elements(self):
        """ربط كل عناصر الواجهة بالمتغيرات"""
        # Table & Formula
        self.table_view = getattr(self.ui, "tableView", None)
        self.formula_bar = getattr(self.ui, "formulaBar", None)
        self.sheet_selector = getattr(self.ui, "sheetSelector", None)
        self.dirCombo = getattr(self.ui, "dirCombo", None)

        # Database Buttons
        self.btnCreateDatabase = getattr(self.ui, "btnCreateDatabase", None)
        self.btnOpenDatabase = getattr(self.ui, "btnOpenDatabase", None)
        self.btnCloseDatabase = getattr(self.ui, "btnCloseDatabase", None)
        self.btnDeleteDatabase = getattr(self.ui, "btnDeleteDatabase", None)
        self.btnRenameDatabase = getattr(self.ui, "btnRenameDatabase", None)

        # Row/Column Buttons
        self.btnAddRow = getattr(self.ui, "btnAddRow", None)
        self.btnDeleteRow = getattr(self.ui, "btnDeleteRow", None)
        self.btnAddColumn = getattr(self.ui, "btnAddColumn", None)
        self.btnDeleteColumn = getattr(self.ui, "btnDeleteColumn", None)

        # Undo/Redo
        self.btnUndo = getattr(self.ui, "btnUndo", None)
        self.btnRedo = getattr(self.ui, "btnRedo", None)

        # Save/Export
        self.btnSaveDatabase = getattr(self.ui, "btnSaveDatabase", None)
        self.btnExportDatabase = getattr(self.ui, "btnExportDatabase", None)
        self.btnSaveSheet = getattr(self.ui, "btnSaveSheet", None)
        self.btnClearSheet = getattr(self.ui, "btnClearSheet", None)

        # Sheet Management
        self.btnAddSheet = getattr(self.ui, "btnAddSheet", None)
        self.btnDeleteSheet = getattr(self.ui, "btnDeleteSheet", None)
        self.btnRenameSheet = getattr(self.ui, "btnRenameSheet", None)
        self.btnImportSheet = getattr(self.ui, "btnImportSheet", None)

        # Clipboard & Formatting
        self.btnCopy = getattr(self.ui, "btnCopy", None)
        self.btnPaste = getattr(self.ui, "btnPaste", None)
        self.btnMerge = getattr(self.ui, "btnMerge", None)
        self.btnBold = getattr(self.ui, "btnBold", None)
        self.btnBGColor = getattr(self.ui, "btnBGColor", None)
        self.btnTextColor = getattr(self.ui, "btnTextColor", None)

        # Insert Files
        self.btnInsertImage = getattr(self.ui, "btnInsertImage", None)
        self.btnInsertPdf = getattr(self.ui, "btnInsertPdf", None)

        # Table dimensions
        self.btnColumnWidth = getattr(self.ui, "btnColumnWidth", None)
        self.btnRowHeight = getattr(self.ui, "btnRowHeight", None)

        # Research / Additional Tools
        self.btnResarch = getattr(self.ui, "btnResarch", None)

        # زر تحرير/قفل الخلايا
        self.btnEditCells = getattr(self.ui, "btnEditCells", None)

        # ComboBoxes إضافية
        self.fontCombo = getattr(self.ui, "fontCombo", None)
        self.fontSizeCombo = getattr(self.ui, "fontSizeCombo", None)
        self.alignCombo = getattr(self.ui, "alignCombo", None)
        self.colTypeCombo = getattr(self.ui, "colTypeCombo", None)

    # -------------------------- إدارة تحرير الخلايا --------------------------
    def _update_cell_editable_state(self):
        """تحديث حالة التحرير حسب self.cells_editable"""
        if not self.table_view or not self.table_view.model():
            return
        model = self.table_view.model()
        if hasattr(model, "set_editable"):
            model.set_editable(self.cells_editable)

    def toggle_edit_cells(self):
        """تبديل حالة تحرير الخلايا عند الضغط على الزر"""
        if not self.table_view or not self.table_view.model():
            warn_no_sheet(self)
            return
        self.cells_editable = not self.cells_editable
        self._update_cell_editable_state()
        state = "مفعل" if self.cells_editable else "معطل"

        QMessageBox.information(self, "تحرير الخلايا", f"تم {state} تحرير الخلايا.")

    # -------------------------- Undo/Redo مع تحذير --------------------------
    def undo_wrapper(self):
        if not hasattr(self, "table_view") or self.table_view is None or not self.table_view.model():
            warn_no_sheet(self)
            return
        self.undo()

    def redo_wrapper(self):
        if not hasattr(self, "table_view") or self.table_view is None or not self.table_view.model():
            warn_no_sheet(self)
            return
        self.redo()

    # -------------------------- ربط أزرار قاعدة البيانات وأوراق العمل مع التحقق --------------------------
    def _wrap_database_buttons(self):
        db_buttons = [
            ("btnSaveDatabase", self.save_database),
            ("btnDeleteDatabase", self.delete_database),
            ("btnCloseDatabase", self.close_database),
            ("btnRenameDatabase", self.rename_database),
            ("btnExportDatabase", self.export_database),
        ]
        for btn_name, method in db_buttons:
            btn = getattr(self, btn_name, None)
            if btn:
                btn.clicked.connect(lambda checked, m=method: self._check_db_and_run(m))

    def _wrap_sheet_buttons(self):
        sheet_buttons = [
            ("btnAddSheet", self.add_sheet),
            ("btnDeleteSheet", self.delete_sheet),
            ("btnRenameSheet", self.rename_sheet),
            ("btnImportSheet", self.import_sheet),
            ("btnSaveSheet", self.save_sheet),
            ("btnClearSheet", self.clear_sheet),
            ("btnAddRow", self.add_row),
            ("btnDeleteRow", self.delete_row),
            ("btnAddColumn", self.add_column),
            ("btnDeleteColumn", self.delete_column),
        ]
        for btn_name, method in sheet_buttons:
            btn = getattr(self, btn_name, None)
            if btn:
                btn.clicked.connect(lambda checked, m=method: self._check_sheet_and_run(m))

    def _check_db_and_run(self, func):
        if not hasattr(self, "db_manager") or self.db_manager is None:
            warn_no_database(self)
            return
        func()

    def _check_sheet_and_run(self, func):
        if not hasattr(self, "db_manager") or self.db_manager is None:
            warn_no_database(self)
            return
        if not getattr(self.db_manager, "current_sheet", None):
            warn_no_sheet(self)
            return
        func()


# -------------------------- تشغيل التطبيق --------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
