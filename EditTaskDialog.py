from translations import TRANSLATIONS
from PyQt5 import QtCore, QtWidgets

class EditTaskDialog(QtWidgets.QDialog):
    def __init__(self, parent, task):
        super(EditTaskDialog, self).__init__(parent)
        self.current_language = parent.current_language if parent else "zh"
        self.translations = parent.translations if parent else TRANSLATIONS[self.current_language]
        self.setWindowTitle(self.translations["edit_task"])
        layout = QtWidgets.QFormLayout(self)

        self.taskNameEdit = QtWidgets.QLineEdit(task.summary)
        self.taskDetailEdit = QtWidgets.QTextEdit(task.description if task.description else "")

        # 使用 QComboBox 替代 QSpinBox 进行优先级选择
        self.priorityCombo = QtWidgets.QComboBox()
        self.priority_options = [
            (self.translations.get("priority_extremely_high", "极高"), 0),
            (self.translations.get("priority_high", "高"), 2),
            (self.translations.get("priority_medium", "中"), 5),
            (self.translations.get("priority_low", "低"), 8)
        ]
        for text, value in self.priority_options:
            self.priorityCombo.addItem(text, value)
        # 根据 task.priority 设置初始选项
        try:
            current_priority = int(task.priority)
        except Exception:
            current_priority = 2  # 默认设为“高”
        if current_priority == 0:
            index = 0
        elif 1 <= current_priority <= 3:
            index = 1
        elif 4 <= current_priority <= 6:
            index = 2
        elif 7 <= current_priority <= 9:
            index = 3
        else:
            index = 1
        self.priorityCombo.setCurrentIndex(index)

        self.deadlineEdit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.deadlineEdit.setCalendarPopup(True)
        if task.due:
            self.deadlineEdit.setDateTime(QtCore.QDateTime(task.due))
            initial_no_due = False
        else:
            initial_no_due = True
            self.deadlineEdit.setEnabled(False)
            
        self.noDeadlineCheck = QtWidgets.QCheckBox(self.translations.get("no_due", "无到期时间"))
        self.noDeadlineCheck.setChecked(initial_no_due)
        self.noDeadlineCheck.stateChanged.connect(self.toggleDeadline)
        
        layout.addRow(self.translations["task_name"], self.taskNameEdit)
        layout.addRow(self.translations["task_detail"], self.taskDetailEdit)
        layout.addRow(self.translations["priority"], self.priorityCombo)
        layout.addRow(self.translations["deadline"], self.deadlineEdit)
        layout.addRow("", self.noDeadlineCheck)
        
        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addRow(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        
    def toggleDeadline(self, state):
        if state == QtCore.Qt.Checked:
            self.deadlineEdit.setEnabled(False)
        else:
            self.deadlineEdit.setEnabled(True)
            
    def getData(self):
        due = None if self.noDeadlineCheck.isChecked() else self.deadlineEdit.dateTime().toPyDateTime()
        # 取出 comboBox 中存储的数字
        priority = self.priorityCombo.currentData()
        return {
            "summary": self.taskNameEdit.text(),
            "description": self.taskDetailEdit.toPlainText(),
            "priority": priority,
            "due": due
        }