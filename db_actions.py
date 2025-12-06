import os
import pandas as pd
import sqlite3
from PySide6.QtWidgets import QMessageBox, QInputDialog, QFileDialog

try:
    import pypyodbc
except ImportError:
    pypyodbc = None

# -------------------------
#  Database Manager
# -------------------------
class DatabaseManager:
    def __init__(self):
        self.sheets = {}
        self.current_sheet = None
        self.current_database_path = None

    # -------------------------
    def reset_database(self):
        """إعادة ضبط قاعدة البيانات بالكامل"""
        self.sheets.clear()
        self.current_sheet = None
        self.current_database_path = None

    # -------------------------
    def create_database(self, path):
        """إنشاء قاعدة بيانات مع Sheet افتراضي"""
        ext = os.path.splitext(path)[1].lower()
        if not ext:
            path += ".xlsx"
            ext = ".xlsx"

        self.reset_database()
        self.current_database_path = path

        # إنشاء Sheet افتراضي
        self.sheets["Sheet1"] = pd.DataFrame()
        self.current_sheet = "Sheet1"

        # حفظ القاعدة
        self.save_database()

    # -------------------------
    def open_database(self, path):
        """فتح قاعدة بيانات موجودة"""
        self.reset_database()
        self.current_database_path = path
        ext = os.path.splitext(path)[1].lower()

        try:
            if ext in (".xls", ".xlsx", ".xlsm"):
                xls = pd.ExcelFile(path)
                for sheet_name in xls.sheet_names:
                    df = pd.read_excel(path, sheet_name=sheet_name)
                    self.sheets[sheet_name] = df
            elif ext == ".csv":
                self.sheets["Sheet1"] = pd.read_csv(path)
            elif ext in (".sqlite", ".db"):
                conn = sqlite3.connect(path)
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
                for t in tables['name']:
                    self.sheets[t] = pd.read_sql(f"SELECT * FROM [{t}]", conn)
                conn.close()
            elif ext in (".h5", ".hdf5"):
                store = pd.HDFStore(path, mode="r")
                self.sheets = {k.strip('/'): store[k] for k in store.keys()}
                store.close()
            elif ext in (".mdb", ".accdb"):
                if not pypyodbc:
                    QMessageBox.critical(None, "خطأ", "مكتبة pypyodbc غير مثبتة لدعم Access")
                    return False
                conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"
                conn = pypyodbc.connect(conn_str, autocommit=True)
                cursor = conn.cursor()
                tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
                for t in tables:
                    self.sheets[t] = pd.read_sql(f"SELECT * FROM [{t}]", conn)
                conn.close()
            else:
                return False

            self.current_sheet = list(self.sheets.keys())[0] if self.sheets else None
            return True
        except Exception:
            return False

    # -------------------------
    def save_database(self):
        """حفظ قاعدة البيانات"""
        if not self.current_database_path:
            return
        ext = os.path.splitext(self.current_database_path)[1].lower()
        try:
            if ext in (".xls", ".xlsx", ".xlsm"):
                with pd.ExcelWriter(self.current_database_path, engine='openpyxl') as writer:
                    for name, df in self.sheets.items():
                        df.to_excel(writer, sheet_name=name, index=False)
            elif ext == ".csv":
                if self.current_sheet and self.current_sheet in self.sheets:
                    self.sheets[self.current_sheet].to_csv(self.current_database_path, index=False)
            elif ext in (".sqlite", ".db"):
                conn = sqlite3.connect(self.current_database_path)
                for sheet, df in self.sheets.items():
                    df.to_sql(sheet, conn, if_exists='replace', index=False)
                conn.close()
            elif ext in (".h5", ".hdf5"):
                with pd.HDFStore(self.current_database_path, mode="w") as store:
                    for sheet, df in self.sheets.items():
                        store[sheet] = df
            elif ext in (".mdb", ".accdb"):
                if not pypyodbc:
                    QMessageBox.critical(None, "خطأ", "مكتبة pypyodbc غير مثبتة لدعم Access")
                    return
                conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.current_database_path};"
                conn = pypyodbc.connect(conn_str, autocommit=True)
                cursor = conn.cursor()
                for sheet, df in self.sheets.items():
                    cursor.execute(f"DROP TABLE IF EXISTS [{sheet}]")
                    columns = ", ".join([f"[{c}] TEXT" for c in df.columns])
                    cursor.execute(f"CREATE TABLE [{sheet}] ({columns})")
                    for _, row in df.iterrows():
                        values = "', '".join(row.astype(str))
                        cursor.execute(f"INSERT INTO [{sheet}] VALUES ('{values}')")
                conn.close()
        except Exception as e:
            QMessageBox.critical(None, "خطأ في الحفظ", str(e))

    # -------------------------
    def export_database(self, path):
        """تصدير قاعدة البيانات إلى مسار آخر"""
        self.current_database_path = path
        self.save_database()

    # -------------------------
    def delete_database_file(self):
        """حذف ملف قاعدة البيانات"""
        if self.current_database_path and os.path.exists(self.current_database_path):
            os.remove(self.current_database_path)
            self.reset_database()

    # -------------------------
    def clear_sheet(self, sheet_name):
        """إفراغ الورقة مع الاحتفاظ بالأعمدة"""
        if sheet_name in self.sheets:
            self.sheets[sheet_name] = pd.DataFrame(columns=self.sheets[sheet_name].columns)

    # -------------------------
    def import_sheet(self, sheet_name, df):
        """استيراد ورقة جديدة"""
        self.sheets[sheet_name] = df.copy()
        self.current_sheet = sheet_name

    # -------------------------
    def rename_database_file(self, new_name):
        """إعادة تسمية قاعدة البيانات"""
        ext = os.path.splitext(new_name)[1].lower()
        if not ext:
            new_name += os.path.splitext(self.current_database_path)[1]
        if self.current_database_path and os.path.exists(self.current_database_path):
            new_path = os.path.join(os.path.dirname(self.current_database_path), new_name)
            os.rename(self.current_database_path, new_path)
            self.current_database_path = new_path

# -------------------------
#  Database Actions (Qt)
# -------------------------
class DatabaseActions:
    def __init__(self):
        self.db_manager = DatabaseManager()

    # -------------------------
    def create_database(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "إنشاء قاعدة بيانات", "",
            "Excel (*.xlsx *.xls *.xlsm);;CSV (*.csv);;SQLite (*.db *.sqlite);;HDF5 (*.h5 *.hdf5);;Access (*.mdb *.accdb)"
        )
        if path:
            self.db_manager.create_database(path)
            # تحديث واجهة المستخدم بعد إنشاء القاعدة
            if hasattr(self, "_update_sheet_selector"):
                self._update_sheet_selector()
            if hasattr(self, "load_sheet"):
                self.load_sheet(self.db_manager.current_sheet)
            QMessageBox.information(self, "تم", "تم إنشاء قاعدة البيانات بنجاح")

    # -------------------------
    def open_database(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "فتح قاعدة بيانات", "",
            "Excel (*.xlsx *.xls *.xlsm);;CSV (*.csv);;SQLite (*.db *.sqlite);;HDF5 (*.h5 *.hdf5);;Access (*.mdb *.accdb)"
        )
        if path:
            ok = self.db_manager.open_database(path)
            if ok:
                # تحديث قائمة الأوراق
                if hasattr(self, "_update_sheet_selector"):
                    self._update_sheet_selector()
                if hasattr(self, "load_sheet"):
                    self.load_sheet(self.db_manager.current_sheet)
                QMessageBox.information(self, "تم", "تم فتح قاعدة البيانات")
            else:
                QMessageBox.warning(self, "خطأ", "تعذر فتح قاعدة البيانات")

    # -------------------------
    def save_database(self):
        self.db_manager.save_database()
        QMessageBox.information(self, "تم", "تم حفظ قاعدة البيانات")

    # -------------------------
    def export_database(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير قاعدة البيانات", "",
            "Excel (*.xlsx *.xls *.xlsm);;CSV (*.csv);;SQLite (*.db *.sqlite);;HDF5 (*.h5 *.hdf5);;Access (*.mdb *.accdb)"
        )
        if path:
            self.db_manager.export_database(path)
            QMessageBox.information(self, "تم", "تم تصدير قاعدة البيانات")

    # -------------------------
    def close_database(self):
        self.db_manager.reset_database()
        if hasattr(self, "table_view"):
            self.table_view.setModel(None)
        if hasattr(self, "sheet_selector"):
            self.sheet_selector.clear()
        QMessageBox.information(self, "تم", "تم إغلاق قاعدة البيانات")

    # -------------------------
    def delete_database(self):
        reply = QMessageBox.question(
            self,
            "حذف قاعدة البيانات",
            "هل تريد حذف ملف قاعدة البيانات؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db_manager.delete_database_file()
            if hasattr(self, "table_view"):
                self.table_view.setModel(None)
            if hasattr(self, "sheet_selector"):
                self.sheet_selector.clear()
            QMessageBox.information(self, "تم", "تم حذف قاعدة البيانات")

    # -------------------------
    def rename_database(self):
        new_name, ok = QInputDialog.getText(self, "إعادة التسمية", "الاسم الجديد:")
        if ok and new_name:
            self.db_manager.rename_database_file(new_name)
            QMessageBox.information(self, "تم", "تمت إعادة التسمية")
