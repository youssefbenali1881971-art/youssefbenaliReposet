from PySide6.QtCore import Qt, QModelIndex

class UndoRedoActions:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def register_change(self, row, col, old_value, new_value):
        self.undo_stack.append({
            'row': row,
            'col': col,
            'old_value': old_value,
            'new_value': new_value
        })
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        change = self.undo_stack.pop()
        row, col = change['row'], change['col']
        old_val = change['old_value']
        new_val = change['new_value']

        self.redo_stack.append(change)
        self.model._df.iat[row, col] = old_val
        idx = self.model.index(row, col)
        self.model.dataChanged.emit(idx, idx, [Qt.DisplayRole, Qt.EditRole])

    def redo(self):
        if not self.redo_stack:
            return
        change = self.redo_stack.pop()
        row, col = change['row'], change['col']
        old_val = change['old_value']
        new_val = change['new_value']

        self.undo_stack.append(change)
        self.model._df.iat[row, col] = new_val
        idx = self.model.index(row, col)
        self.model.dataChanged.emit(idx, idx, [Qt.DisplayRole, Qt.EditRole])

    def clear_history(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
