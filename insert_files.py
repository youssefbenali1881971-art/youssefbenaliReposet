# insert_files.py
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import Qt
from notifications import warn_invalid_file  # تأكد من وجودها في notifications.py
import logging

logger = logging.getLogger(__name__)

class InsertFilesActions:
    """
    وظائف لإدراج الملفات في الجدول:
    - صور (png, jpg, jpeg, bmp)
    - PDF
    تتحقق من نوع الملف قبل الإدراج وتعرض تحذيرًا عند الخطأ.
    """

    # -------------------------- دوال مساعدة --------------------------
    def _get_current_index(self):
        """إرجاع الخلية الحالية مع التحقق من صحة المؤشر"""
        if not hasattr(self, "table_view") or not self.table_view:
            logger.warning("table_view غير موجود")
            return None
        idx = self.table_view.currentIndex()
        if not idx.isValid():
            return None
        return idx

    def _insert_file(self, file_path, valid_extensions, file_type):
        """إدراج مسار ملف في الخلية الحالية بعد التحقق من الامتداد"""
        if not file_path:
            return

        if not file_path.lower().endswith(valid_extensions):
            warn_invalid_file(None, "العمود", file_type)
            return

        idx = self._get_current_index()
        if not idx or not hasattr(self, "model") or not self.model:
            return

        self.model._df.iat[idx.row(), idx.column()] = file_path
        self.model.dataChanged.emit(idx, idx, [Qt.DisplayRole])

    # -------------------------- إدراج صورة --------------------------
    def insert_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "اختر صورة", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        self._insert_file(file_path, (".png", ".jpg", ".jpeg", ".bmp"), "Image")

    # -------------------------- إدراج PDF --------------------------
    def insert_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "اختر ملف PDF", "", "PDF (*.pdf)"
        )
        self._insert_file(file_path, (".pdf",), "PDF")
