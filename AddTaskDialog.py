# ---------------------------
# 添加任务对话框（支持“无到期时间”）
# ---------------------------


from translations import TRANSLATIONS


from PyQt5 import QtCore, QtWidgets


class AddTaskDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AddTaskDialog, self).__init__(parent)
        self.current_language = parent.current_language if parent else "zh"
        self.translations = parent.translations if parent else TRANSLATIONS[
            self.current_language]
        self.setWindowTitle(self.translations["add_task"])
        layout = QtWidgets.QFormLayout(self)

        self.taskNameEdit = QtWidgets.QLineEdit()
        self.taskDetailEdit = QtWidgets.QTextEdit()
        self.prioritySpin = QtWidgets.QSpinBox()
        self.prioritySpin.setRange(0, 10)
        self.deadlineEdit = QtWidgets.QDateTimeEdit(
            QtCore.QDateTime.currentDateTime())
        self.deadlineEdit.setCalendarPopup(True)
        self.noDeadlineCheck = QtWidgets.QCheckBox(
            self.translations.get("no_due", "无到期时间"))
        self.noDeadlineCheck.stateChanged.connect(self.toggleDeadline)

        layout.addRow(self.translations["task_name"], self.taskNameEdit)
        layout.addRow(self.translations["task_detail"], self.taskDetailEdit)
        layout.addRow(self.translations["priority"], self.prioritySpin)
        layout.addRow(self.translations["deadline"], self.deadlineEdit)
        layout.addRow("", self.noDeadlineCheck)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addRow(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def toggleDeadline(self, state):
        if state == QtCore.Qt.Checked:
            self.deadlineEdit.setEnabled(False)
        else:
            self.deadlineEdit.setEnabled(True)

    def getData(self):
        due = None if self.noDeadlineCheck.isChecked(
        ) else self.deadlineEdit.dateTime().toPyDateTime()
        return {
            "summary": self.taskNameEdit.text(),
            "description": self.taskDetailEdit.toPlainText(),
            "priority": self.prioritySpin.value(),
            "due": due
        }
