# signals.py
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QColorDialog, QMessageBox, QComboBox

def connect_signals(main_window):
    """
    ربط جميع الإشارات (Signals) للأزرار و ComboBoxes وشريط الصيغة.
    """

    def safe_connect(widget, signal, slot):
        """ربط إشارة بالوصول الآمن: إذا كان العنصر موجودًا فقط"""
        if widget:
            signal.connect(slot)

    # -------------------------- Database Actions --------------------------
    safe_connect(main_window.btnCreateDatabase, main_window.btnCreateDatabase.clicked, main_window.create_database)
    safe_connect(main_window.btnOpenDatabase, main_window.btnOpenDatabase.clicked, main_window.open_database)
    safe_connect(main_window.btnCloseDatabase, main_window.btnCloseDatabase.clicked, main_window.close_database)
    safe_connect(main_window.btnDeleteDatabase, main_window.btnDeleteDatabase.clicked, main_window.delete_database)
    safe_connect(main_window.btnRenameDatabase, main_window.btnRenameDatabase.clicked, main_window.rename_database)

    # -------------------------- Sheet Selection --------------------------
    safe_connect(main_window.sheet_selector, getattr(main_window.sheet_selector, "currentTextChanged", None), main_window.change_sheet)

    # -------------------------- Row / Column Operations --------------------------
    safe_connect(main_window.btnAddRow, main_window.btnAddRow.clicked, main_window.add_row)
    safe_connect(main_window.btnDeleteRow, main_window.btnDeleteRow.clicked, main_window.delete_row)
    safe_connect(main_window.btnAddColumn, main_window.btnAddColumn.clicked, main_window.add_column)
    safe_connect(main_window.btnDeleteColumn, main_window.btnDeleteColumn.clicked, main_window.delete_column)

    # -------------------------- Undo / Redo --------------------------
    safe_connect(main_window.btnUndo, main_window.btnUndo.clicked, main_window.undo)
    safe_connect(main_window.btnRedo, main_window.btnRedo.clicked, main_window.redo)

    # -------------------------- Saving & Export --------------------------
    safe_connect(main_window.btnSaveDatabase, main_window.btnSaveDatabase.clicked, main_window.save_database)
    safe_connect(main_window.btnExportDatabase, main_window.btnExportDatabase.clicked, main_window.export_database)
    safe_connect(main_window.btnSaveSheet, main_window.btnSaveSheet.clicked, main_window.save_sheet)
    safe_connect(main_window.btnClearSheet, main_window.btnClearSheet.clicked, main_window.clear_sheet)

    # -------------------------- Sheet Management --------------------------
    safe_connect(main_window.btnAddSheet, main_window.btnAddSheet.clicked, main_window.add_sheet)
    safe_connect(main_window.btnDeleteSheet, main_window.btnDeleteSheet.clicked, main_window.delete_sheet)
    safe_connect(main_window.btnRenameSheet, main_window.btnRenameSheet.clicked, main_window.rename_sheet)
    safe_connect(main_window.btnImportSheet, main_window.btnImportSheet.clicked, main_window.import_sheet)

    # -------------------------- Clipboard & Formatting --------------------------
    safe_connect(main_window.btnCopy, main_window.btnCopy.clicked, main_window.copy_selection)
    safe_connect(main_window.btnPaste, main_window.btnPaste.clicked, main_window.paste_from_clipboard)
    safe_connect(main_window.btnMerge, main_window.btnMerge.clicked, main_window.merge_cells)
    safe_connect(main_window.btnBold, main_window.btnBold.clicked, main_window.toggle_bold)
    safe_connect(main_window.btnBGColor, main_window.btnBGColor.clicked, main_window.set_bg_color)
    safe_connect(main_window.btnTextColor, main_window.btnTextColor.clicked, main_window.set_text_color)

    # -------------------------- Font & Alignment ComboBoxes --------------------------
    if hasattr(main_window, "fontCombo") and main_window.fontCombo:
        main_window.fontCombo.currentTextChanged.connect(main_window.apply_font)
    if hasattr(main_window, "fontSizeCombo") and main_window.fontSizeCombo:
        main_window.fontSizeCombo.currentTextChanged.connect(main_window.apply_font)
    if hasattr(main_window, "alignCombo") and main_window.alignCombo:
        main_window.alignCombo.currentTextChanged.connect(main_window.apply_alignment)

    # -------------------------- Formula Bar --------------------------
    if hasattr(main_window, "formula_bar") and main_window.formula_bar:
        main_window.formula_bar.returnPressed.connect(main_window.apply_formula)

    # -------------------------- Insert Files --------------------------
    safe_connect(main_window.btnInsertImage, main_window.btnInsertImage.clicked, main_window.insert_image)
    safe_connect(main_window.btnInsertPdf, main_window.btnInsertPdf.clicked, main_window.insert_pdf)

    # -------------------------- Table Dimensions --------------------------
    safe_connect(main_window.btnColumnWidth, main_window.btnColumnWidth.clicked, main_window.set_column_widths)
    safe_connect(main_window.btnRowHeight, main_window.btnRowHeight.clicked, main_window.set_row_height)

    # -------------------------- Sheet Direction --------------------------
    if hasattr(main_window, "dirCombo") and isinstance(main_window.dirCombo, QComboBox):
        main_window.dirCombo.clear()
        main_window.dirCombo.addItems(["من اليسار الى اليمين", "من اليمين الى اليسار"])
        main_window.dirCombo.currentTextChanged.connect(main_window.change_table_direction)

    # -------------------------- Research / Additional Tools --------------------------
    if hasattr(main_window, "btnResarch") and main_window.btnResarch:
        main_window.btnResarch.clicked.connect(main_window.open_research_window)
