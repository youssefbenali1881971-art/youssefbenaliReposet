from PySide6.QtCore import Qt, QAbstractTableModel
from PySide6.QtGui import QFont, QColor
import pandas as pd
import datetime
import os
from notifications import warn_invalid_input

class DataFrameModel(QAbstractTableModel):
    """
    نموذج بيانات لدعم QTableView مع:
    - DataFrame من pandas
    - تنسيقات لكل خلية
    - التحقق من نوع البيانات لكل عمود
    - دعم تعطيل/تمكين تحرير الخلايا
    """

    def __init__(self, df=pd.DataFrame(), column_types=None, editable=False):
        super().__init__()
        self._df = df.copy()
        self._formats = {}
        self.column_types = column_types or {col: "str" for col in df.columns}
        self._editable = editable  # كل الخلايا غير قابلة للتحرير افتراضياً

    # -------------------------- إعدادات النموذج --------------------------
    def rowCount(self, parent=None):
        return len(self._df.index)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section]) if section < len(self._df.columns) else ""
        else:
            return str(section + 1)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if self._editable:
            flags |= Qt.ItemIsEditable
        return flags

    # -------------------------- عرض البيانات --------------------------
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        r, c = index.row(), index.column()
        val = self._df.iat[r, c]
        fmt = self._formats.get((r, c), {})

        if role in (Qt.DisplayRole, Qt.EditRole):
            return "" if pd.isna(val) or val is None else str(val)
        if role == Qt.FontRole:
            return fmt.get("font", None)
        if role == Qt.BackgroundRole:
            return fmt.get("bg", None)
        if role == Qt.ForegroundRole:
            return fmt.get("fg", None)
        if role == Qt.TextAlignmentRole:
            return fmt.get("align", None)
        return None

    # -------------------------- تعيين البيانات مع التحقق --------------------------
    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid() or role != Qt.EditRole:
            return False
        if not self._editable:
            return False  # إذا كان التحرير معطل، لا نفعل شيئًا

        row, col = index.row(), index.column()
        col_name = self._df.columns[col]
        col_type = self.column_types.get(col_name, "str")

        if not self._validate_value(value, col_type):
            warn_invalid_input(None, col_name, col_type)
            return False

        value = self._convert_value(value, col_type)
        self._df.iat[row, col] = value
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    # -------------------------- تحديث كامل DataFrame --------------------------
    def update_dataframe(self, df, column_types=None):
        self.beginResetModel()
        df.columns = [str(c) if c else f"Column {i+1}" for i, c in enumerate(df.columns)]
        self._df = df.copy()
        self._formats.clear()
        if column_types:
            self.column_types = column_types
        else:
            for col in df.columns:
                if col not in self.column_types:
                    self.column_types[col] = "str"
        self.endResetModel()

    # -------------------------- تنسيقات الخلايا --------------------------
    def set_format_for_indexes(self, indexes, font=None, bg=None, fg=None, align=None):
        changed = []
        for idx in indexes:
            if not idx.isValid():
                continue
            key = (idx.row(), idx.column())
            fmt = self._formats.get(key, {})
            if font is not None: fmt["font"] = font
            if bg is not None: fmt["bg"] = bg
            if fg is not None: fmt["fg"] = fg
            if align is not None: fmt["align"] = align
            self._formats[key] = fmt
            changed.append(idx)
        if changed:
            self.dataChanged.emit(
                changed[0], changed[-1],
                [Qt.FontRole, Qt.BackgroundRole, Qt.ForegroundRole, Qt.TextAlignmentRole]
            )

    # -------------------------- تمكين / تعطيل تحرير الخلايا --------------------------
    def set_editable(self, editable: bool):
        """تمكين أو تعطيل التحرير لجميع الخلايا"""
        self._editable = editable
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole])

    # -------------------------- التحقق من صحة البيانات --------------------------
    def _validate_value(self, value, col_type):
        if col_type in ("str",):
            return True
        elif col_type in ("int", "float"):
            try:
                float(value)
                return True
            except:
                return False
        elif col_type == "percent":
            try:
                v = float(value)
                return 0 <= v <= 100
            except:
                return False
        elif col_type == "date":
            try:
                if isinstance(value, datetime.date):
                    return True
                pd.to_datetime(value)
                return True
            except:
                return False
        elif col_type in ("image", "pdf"):
            if not isinstance(value, str):
                return False
            ext = os.path.splitext(value)[1].lower()
            if col_type == "image":
                return ext in (".png", ".jpg", ".jpeg", ".bmp")
            if col_type == "pdf":
                return ext == ".pdf"
        return False

    def _convert_value(self, value, col_type):
        if col_type == "int":
            return int(float(value))
        if col_type in ("float", "percent"):
            return float(value)
        if col_type == "date":
            if isinstance(value, datetime.date):
                return value
            return pd.to_datetime(value).date()
        return value
