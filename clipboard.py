# clipboard.py
from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ClipboardActions:
    """
    وظائف الحافظة:
    - نسخ البيانات مع التنسيقات
    - لصق البيانات مع التنسيقات
    """

    # -------------------------- دوال مساعدة --------------------------
    def _get_selected_indexes(self):
        """إرجاع جميع الخلايا المحددة، مع التحقق من table_view"""
        if hasattr(self, "table_view") and self.table_view:
            return sorted(self.table_view.selectionModel().selectedIndexes(),
                          key=lambda x: (x.row(), x.column()))
        return []

    # -------------------------- نسخ --------------------------
    def copy_selection(self):
        """نسخ البيانات والتنسيقات المختارة إلى الحافظة"""
        idxs = self._get_selected_indexes()
        if not idxs or not hasattr(self, "model") or not hasattr(self.model, "_df"):
            return

        # بناء مصفوفة البيانات والتنسيقات
        rows = {}
        formats = {}
        for idx in idxs:
            r, c = idx.row(), idx.column()
            rows.setdefault(r, {})[c] = self.model._df.iat[r, c]
            formats[(r - idxs[0].row(), c - idxs[0].column())] = self.model._formats.get((r, c), {}).copy()

        rmin, rmax = idxs[0].row(), idxs[-1].row()
        cmin, cmax = idxs[0].column(), idxs[-1].column()
        lines = []
        for r in range(rmin, rmax + 1):
            parts = [str(rows.get(r, {}).get(c, "")) for c in range(cmin, cmax + 1)]
            lines.append('\t'.join(parts))

        # حفظ البيانات في الحافظة
        QGuiApplication.clipboard().setText('\n'.join(lines))

        # حفظ التنسيقات مؤقتًا
        self._clipboard_formats = formats

    # -------------------------- لصق --------------------------
    def paste_from_clipboard(self):
        """لصق البيانات مع التنسيقات من الحافظة"""
        if not hasattr(self, "model") or not hasattr(self.model, "_df"):
            return

        text = QGuiApplication.clipboard().text()
        if not text:
            return

        start_idx = getattr(self.table_view, "currentIndex", lambda: None)()
        if not start_idx or not start_idx.isValid():
            start_idx = self.model.index(0, 0)

        r0, c0 = start_idx.row(), start_idx.column()
        rows = text.split('\n')

        for i, line in enumerate(rows):
            cols = line.split('\t')
            for j, val in enumerate(cols):
                r, c = r0 + i, c0 + j

                # إضافة صفوف إذا لزم
                while r >= self.model.rowCount():
                    if hasattr(self, "add_row"):
                        self.add_row()
                    else:
                        new_row = pd.DataFrame([[""] * self.model.columnCount()],
                                               columns=self.model._df.columns)
                        self.model._df = pd.concat([self.model._df, new_row], ignore_index=True)

                # إضافة أعمدة إذا لزم
                while c >= self.model.columnCount():
                    new_col_name = f"Column {self.model.columnCount() + 1}"
                    self.model._df[new_col_name] = ""

                # لصق القيمة
                self.model._df.iat[r, c] = val

                # لصق التنسيقات إذا موجودة
                if hasattr(self, "_clipboard_formats"):
                    fmt = self._clipboard_formats.get((i, j), {})
                    if fmt:
                        self.model._formats[(r, c)] = fmt.copy()

        # إشعار الجدول بتغيير البيانات
        self.model.dataChanged.emit(
            self.model.index(0, 0),
            self.model.index(self.model.rowCount() - 1, max(0, self.model.columnCount() - 1))
        )
