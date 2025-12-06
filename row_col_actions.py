# row_col_actions.py
import datetime
import logging
from PySide6.QtWidgets import QInputDialog, QMessageBox
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)

# استيراد التحذيرات من notifications
from notifications import (
    warn_invalid_date, warn_invalid_number,
    warn_invalid_percentage, warn_invalid_text, warn_invalid_file
)


class RowColumnActions:
    """
    وظائف إدارة الصفوف والأعمدة:
    - إضافة / حذف الصفوف والأعمدة
    - تغيير ارتفاع الصف / عرض العمود
    - التحقق من صحة الخلايا حسب النوع
    - دمج الخلايا وتطبيق الصيغ
    """

    # -------------------------- دوال مساعدة --------------------------
    def _ensure_current_sheet(self):
        sheet = getattr(self.db_manager, "current_sheet", None)
        if not sheet:
            QMessageBox.warning(None, "خطأ", "لا توجد ورقة حالية.")
            return None
        if sheet not in self.db_manager.sheets:
            QMessageBox.warning(None, "خطأ", "الورقة الحالية غير موجودة في قاعدة البيانات.")
            return None
        return sheet

    def _ensure_table_view_and_model(self):
        if not hasattr(self, "table_view") or self.table_view is None:
            logger.warning("table_view غير معرف")
            return False
        if not hasattr(self, "model") or self.model is None:
            logger.warning("model غير معرف")
            return False
        return True

    # -------------------------- الصفوف --------------------------
    def add_row(self):
        sheet = self._ensure_current_sheet()
        if not sheet:
            return
        df = self.db_manager.sheets[sheet]
        new_row = {col: "" for col in df.columns}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        self.db_manager.sheets[sheet] = df
        self.load_sheet(sheet)

    def delete_row(self):
        sheet = self._ensure_current_sheet()
        if not sheet or not self._ensure_table_view_and_model():
            return

        idx = self.table_view.currentIndex()
        if not idx.isValid():
            QMessageBox.warning(None, "خطأ", "الرجاء اختيار صف للحذف.")
            return

        df = self.db_manager.sheets[sheet].copy()
        df = df.drop(idx.row()).reset_index(drop=True)
        self.db_manager.sheets[sheet] = df
        self.load_sheet(sheet)

    # -------------------------- الأعمدة --------------------------
    def add_column(self):
        sheet = self._ensure_current_sheet()
        if not sheet:
            return

        col_name, ok = QInputDialog.getText(None, "إضافة عمود", "اسم العمود:")
        if not ok or not col_name.strip():
            return

        df = self.db_manager.sheets[sheet]
        df[col_name.strip()] = ""
        self.db_manager.sheets[sheet] = df
        self.load_sheet(sheet)

    def delete_column(self):
        sheet = self._ensure_current_sheet()
        if not sheet:
            return

        df = self.db_manager.sheets[sheet]
        if df.empty or df.shape[1] == 0:
            QMessageBox.warning(None, "خطأ", "لا توجد أعمدة للحذف.")
            return

        col_name, ok = QInputDialog.getItem(
            None, "حذف عمود", "اختر العمود المراد حذفه:", df.columns.tolist(), 0, False
        )
        if not ok or not col_name:
            return

        df = df.drop(columns=[col_name])
        self.db_manager.sheets[sheet] = df
        self.load_sheet(sheet)

    # -------------------------- تغيير أبعاد --------------------------
    def set_row_height(self):
        if not self._ensure_table_view_and_model():
            return

        idx = self.table_view.currentIndex()
        if not idx.isValid():
            QMessageBox.warning(None, "خطأ", "الرجاء اختيار صف لتغيير ارتفاعه.")
            return

        height, ok = QInputDialog.getInt(None, "تغيير ارتفاع الصف", "أدخل ارتفاع الصف (px):", 25, 10, 1000)
        if ok:
            self.table_view.setRowHeight(idx.row(), height)

    def set_column_widths(self):
        if not self._ensure_table_view_and_model():
            return

        idx = self.table_view.currentIndex()
        if not idx.isValid():
            QMessageBox.warning(None, "خطأ", "الرجاء اختيار عمود لتغيير عرضه.")
            return

        width, ok = QInputDialog.getInt(None, "تغيير عرض العمود", "أدخل عرض العمود (px):", 100, 10, 1000)
        if ok:
            self.table_view.setColumnWidth(idx.column(), width)

    # -------------------------- التحقق من صحة البيانات --------------------------
    def validate_cell_input(self, row, col, value, col_type):
        col_type_lower = str(col_type).lower()
        if col_type_lower in ["number", "رقم"]:
            try:
                float(value)
                return True
            except ValueError:
                warn_invalid_number(None, col)
                return False
        elif col_type_lower in ["percentage", "نسبة مئوية"]:
            try:
                v = float(value)
                if 0 <= v <= 100:
                    return True
                warn_invalid_percentage(None, col)
                return False
            except ValueError:
                warn_invalid_percentage(None, col)
                return False
        elif col_type_lower in ["date", "تاريخ"]:
            try:
                datetime.datetime.strptime(value, "%Y-%m-%d")
                return True
            except ValueError:
                warn_invalid_date(None, col)
                return False
        elif col_type_lower in ["text", "نص"]:
            if isinstance(value, str):
                return True
            warn_invalid_text(None, col)
            return False
        elif col_type_lower in ["image", "صورة", "pdf"]:
            return True
        else:
            warn_invalid_file(None, col)
            return False

    # -------------------------- دمج الخلايا --------------------------
    def merge_cells(self):
        if not self._ensure_table_view_and_model():
            return

        idxs = self.table_view.selectionModel().selectedIndexes()
        if not idxs:
            QMessageBox.warning(None, "خطأ", "اختر الخلايا لدمجها.")
            return

        try:
            first = idxs[0]
            merged_value = " ".join(str(self.model._df.iat[i.row(), i.column()]) for i in idxs)
            self.model._df.iat[first.row(), first.column()] = merged_value

            for idx in idxs[1:]:
                self.model._df.iat[idx.row(), idx.column()] = ""

            self.model.dataChanged.emit(first, idxs[-1], [Qt.DisplayRole])
        except Exception:
            logger.exception("فشل دمج الخلايا")
            QMessageBox.critical(None, "خطأ", "حدث خطأ أثناء دمج الخلايا.")

    # -------------------------- تطبيق الصيغ --------------------------
    def apply_formula(self):
        if not self._ensure_table_view_and_model() or not hasattr(self, "formula_bar"):
            return

        idx = self.table_view.currentIndex()
        if not idx.isValid():
            return

        formula = self.formula_bar.text()
        try:
            self.model._df.iat[idx.row(), idx.column()] = formula
            self.model.dataChanged.emit(idx, idx, [Qt.DisplayRole, Qt.EditRole])
            self.formula_bar.clear()
        except Exception:
            logger.exception("فشل تطبيق الصيغة")
            QMessageBox.critical(None, "خطأ", "حدث خطأ أثناء تطبيق الصيغة.")
