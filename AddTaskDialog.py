from translations import TRANSLATIONS
from PyQt5 import QtCore, QtWidgets

class AddTaskDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AddTaskDialog, self).__init__(parent)
        self.current_language = parent.current_language if parent else "zh"
        self.translations = parent.translations if parent else TRANSLATIONS[self.current_language]
        self.setWindowTitle(self.translations["add_task"])
        layout = QtWidgets.QFormLayout(self)

        self.taskNameEdit = QtWidgets.QLineEdit()
        self.taskDetailEdit = QtWidgets.QTextEdit()
        
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

        # 使用 QDateTimeEdit 同时支持日期和时间的编辑
        self.deadlineEdit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.deadlineEdit.setCalendarPopup(True)
        # 设置显示格式，使得日期和时间都可编辑
        self.deadlineEdit.setDisplayFormat("yyyy-MM-dd HH:mm")

        # 创建无到期时间复选框
        self.noDeadlineCheck = QtWidgets.QCheckBox(self.translations.get("no_due", "无到期时间"))
        self.noDeadlineCheck.toggled.connect(self.toggleDeadline)

        # 周期任务设置
        self.recurringCheck = QtWidgets.QCheckBox(self.translations.get("recurring_task", "周期任务"))
        self.recurringCheck.toggled.connect(self.toggleRecurring)
        
        # 间隔设置：天、小时、分钟
        self.intervalDaysSpin = QtWidgets.QSpinBox()
        self.intervalDaysSpin.setMinimum(0)
        self.intervalDaysSpin.setMaximum(365)
        self.intervalDaysSpin.setValue(0)
        self.intervalDaysSpin.setEnabled(False)
        
        self.intervalHoursSpin = QtWidgets.QSpinBox()
        self.intervalHoursSpin.setMinimum(0)
        self.intervalHoursSpin.setMaximum(23)
        self.intervalHoursSpin.setValue(0)
        self.intervalHoursSpin.setEnabled(False)
        
        self.intervalMinutesSpin = QtWidgets.QSpinBox()
        self.intervalMinutesSpin.setMinimum(0)
        self.intervalMinutesSpin.setMaximum(59)
        self.intervalMinutesSpin.setValue(0)
        self.intervalMinutesSpin.setEnabled(False)

        layout.addRow(self.translations["task_name"], self.taskNameEdit)
        layout.addRow(self.translations["task_detail"], self.taskDetailEdit)
        layout.addRow(self.translations["priority"], self.priorityCombo)
        layout.addRow(self.translations["deadline"], self.deadlineEdit)
        layout.addRow("", self.noDeadlineCheck)
        layout.addRow("", self.recurringCheck)
        
        # 间隔设置行
        intervalLayout = QtWidgets.QHBoxLayout()
        intervalLayout.addWidget(QtWidgets.QLabel(self.translations.get("interval_days", "天:")))
        intervalLayout.addWidget(self.intervalDaysSpin)
        intervalLayout.addWidget(QtWidgets.QLabel(self.translations.get("interval_hours", "小时:")))
        intervalLayout.addWidget(self.intervalHoursSpin)
        intervalLayout.addWidget(QtWidgets.QLabel(self.translations.get("interval_minutes", "分钟:")))
        intervalLayout.addWidget(self.intervalMinutesSpin)
        layout.addRow("", intervalLayout)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addRow(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def toggleDeadline(self, checked):
        self.deadlineEdit.setEnabled(not checked)

    def toggleRecurring(self, checked):
        self.intervalDaysSpin.setEnabled(checked)
        self.intervalHoursSpin.setEnabled(checked)
        self.intervalMinutesSpin.setEnabled(checked)

    def getData(self):
        due = None if self.noDeadlineCheck.isChecked() else self.deadlineEdit.dateTime().toPyDateTime()
        # 取出 comboBox 中存储的数字
        priority = self.priorityCombo.currentData()
        
        # 计算总分钟数
        total_minutes = None
        if self.recurringCheck.isChecked():
            total_minutes = (self.intervalDaysSpin.value() * 24 * 60 + 
                           self.intervalHoursSpin.value() * 60 + 
                           self.intervalMinutesSpin.value())
            if total_minutes == 0:
                total_minutes = None  # 如果为0则不设置周期
        
        return {
            "summary": self.taskNameEdit.text(),
            "description": self.taskDetailEdit.toPlainText(),
            "priority": priority,
            "due": due,
            "is_recurring": self.recurringCheck.isChecked() and total_minutes is not None,
            "recurrence_interval_minutes": total_minutes
        }
