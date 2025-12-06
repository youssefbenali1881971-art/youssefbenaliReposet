# formatting.py
from PySide6.QtGui import QFont, QColor
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QColorDialog
import logging

logger = logging.getLogger(__name__)

class FormattingActions:
    """
    وظائف تنسيق الجدول:
    - تغيير الخط وحجمه
    - ضبط المحاذاة
    - تفعيل/تعطيل Bold
    - تغيير لون الخلفية والنص
    """

    # -------------------------- دوال مساعدة --------------------------
    def _get_selected_indexes(self):
        """إرجاع جميع الخلايا المحددة، مع التحقق من table_view وmodel"""
        if not hasattr(self, "table_view") or self.table_view is None:
            logger.warning("table_view غير معرف")
            return []
        if not hasattr(self, "model") or self.model is None:
            logger.warning("model غير معرف")
            return []
        return self.table_view.selectionModel().selectedIndexes()

    def _update_format(self, idx, **kwargs):
        """تطبيق التنسيقات على خلية واحدة"""
        fmt = self.model._formats.get((idx.row(), idx.column()), {})
        for key, value in kwargs.items():
            fmt[key] = value
        self.model._formats[(idx.row(), idx.column())] = fmt

    # -------------------------- تغيير الخط --------------------------
    def apply_font(self):
        idxs = self._get_selected_indexes()
        if not idxs:
            return
        try:
            font_family = self.fontCombo.currentText()
            font_size = int(self.fontSizeCombo.currentText())
        except Exception as e:
            logger.exception("خطأ في قراءة إعدادات الخط")
            return

        for idx in idxs:
            fmt = self.model._formats.get((idx.row(), idx.column()), {})
            font = fmt.get("font", QFont())
            font.setFamily(font_family)
            font.setPointSize(font_size)
            fmt["font"] = font
            self.model._formats[(idx.row(), idx.column())] = fmt

        self.model.dataChanged.emit(idxs[0], idxs[-1], [Qt.FontRole])

    # -------------------------- المحاذاة --------------------------
    def apply_alignment(self):
        idxs = self._get_selected_indexes()
        if not idxs:
            return
        alignment_map = {
            "Left": Qt.AlignLeft,
            "Center": Qt.AlignCenter,
            "Right": Qt.AlignRight
        }
        align = alignment_map.get(getattr(self, "alignCombo", None).currentText(), Qt.AlignLeft)
        for idx in idxs:
            self._update_format(idx, align=align)
        self.model.dataChanged.emit(idxs[0], idxs[-1], [Qt.TextAlignmentRole])

    # -------------------------- Bold --------------------------
    def toggle_bold(self):
        idxs = self._get_selected_indexes()
        if not idxs:
            return

        current_bold = any(
            self.model._formats.get((idx.row(), idx.column()), {}).get("font", QFont()).bold()
            for idx in idxs
        )

        for idx in idxs:
            fmt = self.model._formats.get((idx.row(), idx.column()), {})
            font = fmt.get("font", QFont())
            font.setBold(not current_bold)
            fmt["font"] = font
            self.model._formats[(idx.row(), idx.column())] = fmt

        self.model.dataChanged.emit(idxs[0], idxs[-1], [Qt.FontRole])

    # -------------------------- لون الخلفية --------------------------
    def set_bg_color(self):
        idxs = self._get_selected_indexes()
        if not idxs:
            return

        color = QColorDialog.getColor()
        if not color.isValid():
            return

        for idx in idxs:
            self._update_format(idx, bg=color)
        self.model.dataChanged.emit(idxs[0], idxs[-1], [Qt.BackgroundRole])

    # -------------------------- لون النص --------------------------
    def set_text_color(self):
        idxs = self._get_selected_indexes()
        if not idxs:
            return

        color = QColorDialog.getColor()
        if not color.isValid():
            return

        for idx in idxs:
            self._update_format(idx, fg=color)
        self.model.dataChanged.emit(idxs[0], idxs[-1], [Qt.ForegroundRole])
