# notifications.py
from PySide6.QtWidgets import QMessageBox

# -------------------------- دوال مساعدة --------------------------
def _show_warning(parent, title, msg):
    QMessageBox.warning(parent, title, msg)

def _show_info(parent, title, msg):
    QMessageBox.information(parent, title, msg)

def _show_critical(parent, title, msg):
    QMessageBox.critical(parent, title, msg)

def _ask_question(parent, title, msg):
    return QMessageBox.question(parent, title, msg, QMessageBox.Yes | QMessageBox.No)

# -------------------------- تحذيرات عامة --------------------------
def warn_no_database(parent):
    _show_warning(parent, "خطأ", "لا توجد قاعدة بيانات مفتوحة.")

def warn_no_sheet(parent):
    _show_warning(parent, "خطأ", "لا توجد ورقة محددة.")

# -------------------------- إعلامات النجاح --------------------------
def info_success_export(parent):
    _show_info(parent, "تم", "تم تصدير قاعدة البيانات بنجاح.")

def info_success_save(parent, sheet=None):
    if sheet:
        _show_info(parent, "نجاح", f"تم حفظ الورقة '{sheet}' بنجاح.")
    else:
        _show_info(parent, "نجاح", "تم حفظ قاعدة البيانات بنجاح.")

def info_sheet_deleted(parent, sheet):
    _show_info(parent, "تم", f"تم حذف الورقة '{sheet}' بنجاح.")

# -------------------------- تحذيرات الحذف --------------------------
def warn_delete_database(parent, db_name):
    return _ask_question(parent, "تأكيد الحذف", f"هل أنت متأكد من حذف قاعدة البيانات:\n{db_name}؟")

def warn_delete_sheet(parent, sheet_name):
    return _ask_question(parent, "تأكيد الحذف", f"هل تريد حذف الورقة {sheet_name}؟")

def warn_clear_sheet(parent, sheet_name):
    return _ask_question(parent, "تأكيد المسح", f"هل تريد مسح محتوى الورقة '{sheet_name}'؟")

# -------------------------- أخطاء حرجة --------------------------
def critical_export_error(parent, msg):
    _show_critical(parent, "خطأ", f"حدث خطأ أثناء التصدير:\n{msg}")

def critical_save_error(parent, msg):
    _show_critical(parent, "خطأ", f"حدث خطأ أثناء الحفظ:\n{msg}")

def critical_delete_error(parent, msg):
    _show_critical(parent, "خطأ", f"حدث خطأ أثناء الحذف:\n{msg}")

def critical_open_error(parent, msg):
    _show_critical(parent, "خطأ", f"فشل فتح قاعدة البيانات:\n{msg}")

def critical_import_error(parent, msg):
    _show_critical(parent, "خطأ", f"فشل استيراد الورقة:\n{msg}")

# -------------------------- تحذيرات إدخال بيانات --------------------------
def warn_invalid_input(parent, column_name, col_type):
    _show_warning(
        parent,
        "خطأ في البيانات",
        f"الرجاء إدخال قيمة صحيحة من نوع {col_type} في العمود '{column_name}'."
    )

def warn_invalid_number(parent, column_name):
    warn_invalid_input(parent, column_name, "رقم")

def warn_invalid_percentage(parent, column_name):
    warn_invalid_input(parent, column_name, "نسبة مئوية (0-100)")

def warn_invalid_date(parent, column_name):
    warn_invalid_input(parent, column_name, "تاريخ (YYYY-MM-DD)")

def warn_invalid_text(parent, column_name):
    warn_invalid_input(parent, column_name, "نص")

def warn_invalid_file(parent, column_name, file_type):
    warn_invalid_input(parent, column_name, file_type)

def warn_invalid_data(parent, column_name):
    warn_invalid_input(parent, column_name, "غير صالح / غير معروف")

def warn_empty_cell(parent, column_name):
    _show_warning(parent, "خطأ في البيانات", f"لا يمكن ترك الخلية في العمود '{column_name}' فارغة.")
