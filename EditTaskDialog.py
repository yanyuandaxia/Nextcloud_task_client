# ---------------------------
# 修改任务对话框
# ---------------------------


from translations import TRANSLATIONS


from PyQt5 import QtCore, QtWidgets


class EditTaskDialog(QtWidgets.QDialog):
    def __init__(self, parent, task):
        super(EditTaskDialog, self).__init__(parent)
        self.current_language = parent.current_language if parent else "zh"
        self.translations = parent.translations if parent else TRANSLATIONS[
            self.current_language]
        self.setWindowTitle(self.translations["edit_task"])
        layout = QtWidgets.QFormLayout(self)

        self.taskNameEdit = QtWidgets.QLineEdit(task.summary)
        self.taskDetailEdit = QtWidgets.QTextEdit(
            task.description if task.description else "")
        self.prioritySpin = QtWidgets.QSpinBox()
        self.prioritySpin.setRange(0, 10)
        try:
            self.prioritySpin.setValue(int(task.priority))
        except Exception:
            self.prioritySpin.setValue(0)
        self.deadlineEdit = QtWidgets.QDateTimeEdit(
            QtCore.QDateTime.currentDateTime())
        if task.due:
            self.deadlineEdit.setDateTime(QtCore.QDateTime(task.due))
        self.deadlineEdit.setCalendarPopup(True)

        layout.addRow(self.translations["task_name"], self.taskNameEdit)
        layout.addRow(self.translations["task_detail"], self.taskDetailEdit)
        layout.addRow(self.translations["priority"], self.prioritySpin)
        layout.addRow(self.translations["deadline"], self.deadlineEdit)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addRow(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getData(self):
        return {
            "summary": self.taskNameEdit.text(),
            "description": self.taskDetailEdit.toPlainText(),
            "priority": self.prioritySpin.value(),
            "due": self.deadlineEdit.dateTime().toPyDateTime()
        }
