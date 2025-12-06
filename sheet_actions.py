# sheet_actions.py
import os
import logging
from typing import Optional

import pandas as pd
from PySide6.QtWidgets import QInputDialog, QMessageBox, QFileDialog, QWidget
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class SheetActions:
    """
    فصلت وظائف إدارة الأوراق (sheets) هنا بشكل آمن:
    - إضافة / حذف / إعادة تسمية / تحميل / مسح / استيراد أوراق
    - التعامل الآمن مع model وsheet_selector وtable_view
    - تجنب الاعتماد على مسارات ثابتة
    """

    # -------------------------- دوال مساعدة داخلية --------------------------
    def _ensure_db(self) -> bool:
        """تأكد أن db_manager موجود"""
        if not hasattr(self, "db_manager") or self.db_manager is None:
            logger.error("db_manager غير مُعرّف")
            QMessageBox.critical(self, "خطأ داخلي", "db_manager غير مُهيأ.")
            return False
        return True

    def _safe_sheet_name(self, name: str) -> str:
        """تنظيف الاسم: إزالة مسافات زائدة"""
        return name.strip()

    def _unique_sheet_name(self, base: str) -> str:
        """إرجاع اسم فريد إن كان الاسم موجودًا بالفعل (base, base (1), ...)"""
        base = self._safe_sheet_name(base) or "Sheet"
        if base not in self.db_manager.sheets:
            return base
        i = 1
        while True:
            candidate = f"{base} ({i})"
            if candidate not in self.db_manager.sheets:
                return candidate
            i += 1

    def _add_sheet_to_ui(self, name: str):
        """أضف عنصرًا إلى sheet_selector إن وُجد"""
        if hasattr(self, "sheet_selector") and self.sheet_selector:
            self.sheet_selector.addItem(name)

    def _remove_current_sheet_from_ui(self):
        """إزالة العنصر المحدد من sheet_selector إن وُجد"""
        if hasattr(self, "sheet_selector") and self.sheet_selector:
            idx = self.sheet_selector.currentIndex()
            if idx >= 0:
                self.sheet_selector.removeItem(idx)

    def _set_current_sheet_in_ui(self, name: Optional[str]):
        """تحديث اختيار الواجهة لتعكس current_sheet"""
        if hasattr(self, "sheet_selector") and self.sheet_selector:
            if name is None:
                self.sheet_selector.setCurrentIndex(-1)
            else:
                idx = self.sheet_selector.findText(name)
                if idx >= 0:
                    self.sheet_selector.setCurrentIndex(idx)

    def _update_model_with_df(self, df: pd.DataFrame):
        """تحديث الـ model وربطه بـ table_view"""
        from models import DataFrameModel

        df = df.copy()
        df.columns = [str(c) if c and str(c).strip() != "" else f"Column {i+1}" for i, c in enumerate(df.columns)]

        if hasattr(self, "model") and self.model is not None and hasattr(self.model, "update_dataframe"):
            try:
                self.model.update_dataframe(df)
            except Exception:
                logger.exception("فشل في model.update_dataframe")
        else:
            self.model = DataFrameModel(df, editable=getattr(self, "cells_editable", False))
            if hasattr(self, "table_view") and self.table_view is not None:
                self.table_view.setModel(self.model)

    # -------------------------- وظائف المستخدم --------------------------
    def add_sheet(self):
        if not self._ensure_db():
            return

        name, ok = QInputDialog.getText(self, "إضافة ورقة", "اسم الورقة:")
        if not ok:
            return

        name = self._safe_sheet_name(name)
        if not name:
            QMessageBox.warning(self, "اسم غير صالح", "الرجاء إدخال اسم ورقة صحيح.")
            return

        if name in self.db_manager.sheets:
            reply = QMessageBox.question(
                self, "الورقة موجودة",
                f"الورقة '{name}' موجودة مسبقًا. هل تريد إنشاء اسم فريد بدلاً من ذلك؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                name = self._unique_sheet_name(name)
            else:
                return

        self.db_manager.sheets[name] = pd.DataFrame()
        self.db_manager.current_sheet = name
        self._add_sheet_to_ui(name)
        self._set_current_sheet_in_ui(name)
        self.load_sheet(name)

    def delete_sheet(self):
        if not self._ensure_db():
            return

        sheet = getattr(self.db_manager, "current_sheet", None)
        if not sheet:
            QMessageBox.information(self, "لا توجد ورقة", "لا توجد ورقة حالية للحذف.")
            return

        reply = QMessageBox.question(
            self, "تأكيد الحذف", f"هل تريد حذف الورقة '{sheet}'؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.db_manager.sheets.pop(sheet, None)
            self._remove_current_sheet_from_ui()

            if self.db_manager.sheets:
                new_current = list(self.db_manager.sheets.keys())[0]
                self.db_manager.current_sheet = new_current
                self._set_current_sheet_in_ui(new_current)
                self.load_sheet(new_current)
            else:
                self.db_manager.current_sheet = None
                if hasattr(self, "table_view") and self.table_view:
                    self.table_view.setModel(None)
                self._set_current_sheet_in_ui(None)
        except Exception:
            logger.exception("فشل أثناء حذف الورقة")
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء حذف الورقة.")

    def rename_sheet(self):
        if not self._ensure_db():
            return

        old_name = getattr(self.db_manager, "current_sheet", None)
        if not old_name:
            QMessageBox.information(self, "لا توجد ورقة", "لا توجد ورقة حالية لإعادة التسمية.")
            return

        new_name, ok = QInputDialog.getText(self, "إعادة تسمية الورقة", f"الاسم الجديد للورقة (القديمة: {old_name}):")
        if not ok:
            return

        new_name = self._safe_sheet_name(new_name)
        if not new_name:
            QMessageBox.warning(self, "اسم غير صالح", "الاسم الجديد غير صالح.")
            return

        if new_name == old_name:
            return

        if new_name in self.db_manager.sheets:
            QMessageBox.warning(self, "اسم مكرر", "يوجد ورقة بنفس الاسم. اختر اسمًا آخر.")
            return

        try:
            self.db_manager.sheets[new_name] = self.db_manager.sheets.pop(old_name)
            self.db_manager.current_sheet = new_name

            if hasattr(self, "sheet_selector") and self.sheet_selector:
                idx = self.sheet_selector.currentIndex()
                if idx >= 0:
                    self.sheet_selector.setItemText(idx, new_name)

            self.load_sheet(new_name)
        except Exception:
            logger.exception("فشل أثناء إعادة تسمية الورقة")
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء إعادة تسمية الورقة.")

    def load_sheet(self, sheet_name: str):
        if not self._ensure_db():
            return
        if sheet_name not in self.db_manager.sheets:
            logger.warning("طلب تحميل ورقة غير موجودة: %s", sheet_name)
            return

        try:
            df = self.db_manager.sheets[sheet_name].copy()
            df.columns = [str(c) if c and str(c).strip() != "" else f"Column {i+1}" for i, c in enumerate(df.columns)]
            self._update_model_with_df(df)
            self.db_manager.current_sheet = sheet_name
            self._set_current_sheet_in_ui(sheet_name)
        except Exception:
            logger.exception("فشل أثناء تحميل الورقة %s", sheet_name)
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الورقة: {sheet_name}")

    def clear_sheet(self):
        if not self._ensure_db():
            return
        sheet = getattr(self.db_manager, "current_sheet", None)
        if not sheet:
            QMessageBox.information(self, "لا توجد ورقة", "لا توجد ورقة حالية للمسح.")
            return

        reply = QMessageBox.question(
            self, "تأكيد المسح", f"هل تريد مسح محتوى الورقة '{sheet}'؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.db_manager.clear_sheet(sheet)
            self.load_sheet(sheet)
        except Exception:
            logger.exception("فشل أثناء مسح الورقة")
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء مسح الورقة.")

    def import_sheet(self):
        if not self._ensure_db():
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "استيراد ورقة", "", "Excel (*.xlsx *.xls *.xlsm)")
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)
        except Exception:
            logger.exception("فشل قراءة ملف الإكسل عند الاستيراد")
            QMessageBox.critical(self, "خطأ", "فشل قراءة ملف الإكسل المحدد.")
            return

        sheet_name, ok = QInputDialog.getText(self, "اسم الورقة الجديدة", "اختر اسمًا للورقة:")
        if not ok:
            return

        sheet_name = self._safe_sheet_name(sheet_name)
        if not sheet_name:
            QMessageBox.warning(self, "اسم غير صالح", "الرجاء إدخال اسم ورقة صالح.")
            return

        if sheet_name in self.db_manager.sheets:
            reply = QMessageBox.question(
                self, "الورقة موجودة",
                f"الورقة '{sheet_name}' موجودة. هل تريد استبدالها؟ (نعم=استبدال، لا=إنشاء اسم فريد)",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.db_manager.sheets[sheet_name] = df.copy()
            else:
                sheet_name = self._unique_sheet_name(sheet_name)
                self.db_manager.sheets[sheet_name] = df.copy()
        else:
            self.db_manager.sheets[sheet_name] = df.copy()

        self._add_sheet_to_ui(sheet_name)
        self.db_manager.current_sheet = sheet_name
        self.load_sheet(sheet_name)

    def change_sheet(self, sheet_name: str):
        if not self._ensure_db():
            return
        if not sheet_name:
            return
        if sheet_name in self.db_manager.sheets:
            self.db_manager.current_sheet = sheet_name
            self.load_sheet(sheet_name)
        else:
            logger.warning("المستخدم حاول تغيير الورقة إلى اسم غير موجود: %s", sheet_name)

    def save_sheet(self):
        if not self._ensure_db():
            return

        sheet = getattr(self.db_manager, "current_sheet", None)
        if not sheet:
            QMessageBox.information(self, "لا توجد ورقة", "لا توجد ورقة حالية للحفظ.")
            return

        try:
            if hasattr(self.db_manager, "save_sheet"):
                try:
                    self.db_manager.save_sheet(sheet)
                except Exception:
                    logger.exception("فشل save_sheet; سأنفّذ save_database كبديل")
                    self.db_manager.save_database()
            else:
                self.db_manager.save_database()

            QMessageBox.information(self, "تم", f"تم حفظ الورقة '{sheet}'.")
            self.load_sheet(sheet)
        except Exception:
            logger.exception("فشل أثناء حفظ الورقة")
            QMessageBox.critical(self, "خطأ", "حدث خطأ أثناء حفظ الورقة.")

    def change_table_direction(self, text: str):
        if not hasattr(self, "table_view") or self.table_view is None:
            logger.debug("table_view غير موجود؛ تجاهل تغيير الاتجاه")
            return

        try:
            text_norm = str(text).strip().lower()
            if "rtl" in text_norm or "يمين" in text_norm or "right to left" in text_norm:
                self.table_view.setLayoutDirection(Qt.RightToLeft)
            else:
                self.table_view.setLayoutDirection(Qt.LeftToRight)
        except Exception:
            logger.exception("فشل أثناء تغيير اتجاه الجدول")

    def open_research_window(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(base_dir, "research.ui")

        if not os.path.exists(ui_path):
            try:
                from notifications import critical_open_error
                critical_open_error(self, f"ملف البحث غير موجود:\n{ui_path}")
            except Exception:
                QMessageBox.critical(self, "خطأ", f"ملف البحث غير موجود:\n{ui_path}")
            return

        loader = QUiLoader()
        try:
            research_win = loader.load(ui_path)
            if research_win is None:
                raise RuntimeError("QUiLoader أعاد None")
            self.research_window = research_win
            if isinstance(self.research_window, QWidget):
                self.research_window.show()
            else:
                logger.warning("research.ui لا يرجع QWidget صريحًا")
        except Exception:
            logger.exception("فشل تحميل research.ui")
            try:
                from notifications import critical_open_error
                critical_open_error(self, f"فشل تحميل واجهة البحث:\n{ui_path}")
            except Exception:
                QMessageBox.critical(self, "خطأ", f"فشل تحميل واجهة البحث:\n{ui_path}")

    def _update_sheet_selector(self):
        if not hasattr(self, "sheet_selector") or self.sheet_selector is None:
            return

        self.sheet_selector.blockSignals(True)
        self.sheet_selector.clear()

        if hasattr(self, "db_manager") and self.db_manager.sheets:
            self.sheet_selector.addItems(list(self.db_manager.sheets.keys()))
            current = getattr(self.db_manager, "current_sheet", None)
            if current and current in self.db_manager.sheets:
                index = self.sheet_selector.findText(current)
                if index >= 0:
                    self.sheet_selector.setCurrentIndex(index)

        self.sheet_selector.blockSignals(False)
