from nextcloudtasks import make_rrule, minutes_to_rrule
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
        self.deadlineEdit.setDisplayFormat("yyyy-MM-dd HH:mm")

        # 创建无到期时间复选框
        self.noDeadlineCheck = QtWidgets.QCheckBox(self.translations.get("no_due", "无到期时间"))
        self.noDeadlineCheck.toggled.connect(self.toggleDeadline)

        # 周期任务设置
        self.recurringCheck = QtWidgets.QCheckBox(self.translations.get("recurring_task", "周期任务"))
        self.recurringCheck.toggled.connect(self.toggleRecurring)
        
        # 周期类型选择
        self.freqCombo = QtWidgets.QComboBox()
        self.freq_options = [
            (self.translations.get("freq_daily", "每日"), "DAILY"),
            (self.translations.get("freq_weekly", "每周"), "WEEKLY"),
            (self.translations.get("freq_monthly", "每月"), "MONTHLY"),
            (self.translations.get("freq_yearly", "每年"), "YEARLY"),
            (self.translations.get("freq_custom", "自定义"), "CUSTOM"),
        ]
        for text, value in self.freq_options:
            self.freqCombo.addItem(text, value)
        self.freqCombo.setEnabled(False)
        self.freqCombo.currentIndexChanged.connect(self.onFreqChanged)
        
        # 间隔数值（用于标准频率）
        self.intervalSpin = QtWidgets.QSpinBox()
        self.intervalSpin.setMinimum(1)
        self.intervalSpin.setMaximum(999)
        self.intervalSpin.setValue(1)
        self.intervalSpin.setEnabled(False)
        
        # 自定义间隔设置：天、小时、分钟
        self.customWidget = QtWidgets.QWidget()
        customLayout = QtWidgets.QHBoxLayout(self.customWidget)
        customLayout.setContentsMargins(0, 0, 0, 0)
        
        self.intervalDaysSpin = QtWidgets.QSpinBox()
        self.intervalDaysSpin.setMinimum(0)
        self.intervalDaysSpin.setMaximum(365)
        self.intervalDaysSpin.setValue(0)
        
        self.intervalHoursSpin = QtWidgets.QSpinBox()
        self.intervalHoursSpin.setMinimum(0)
        self.intervalHoursSpin.setMaximum(23)
        self.intervalHoursSpin.setValue(0)
        
        self.intervalMinutesSpin = QtWidgets.QSpinBox()
        self.intervalMinutesSpin.setMinimum(0)
        self.intervalMinutesSpin.setMaximum(59)
        self.intervalMinutesSpin.setValue(0)
        
        customLayout.addWidget(QtWidgets.QLabel(self.translations.get("interval_days", "天:")))
        customLayout.addWidget(self.intervalDaysSpin)
        customLayout.addWidget(QtWidgets.QLabel(self.translations.get("interval_hours", "小时:")))
        customLayout.addWidget(self.intervalHoursSpin)
        customLayout.addWidget(QtWidgets.QLabel(self.translations.get("interval_minutes", "分钟:")))
        customLayout.addWidget(self.intervalMinutesSpin)
        self.customWidget.setEnabled(False)
        self.customWidget.hide()

        layout.addRow(self.translations["task_name"], self.taskNameEdit)
        layout.addRow(self.translations["task_detail"], self.taskDetailEdit)
        layout.addRow(self.translations["priority"], self.priorityCombo)
        layout.addRow(self.translations["deadline"], self.deadlineEdit)
        layout.addRow("", self.noDeadlineCheck)
        layout.addRow("", self.recurringCheck)
        
        # 周期类型行
        freqLayout = QtWidgets.QHBoxLayout()
        freqLayout.addWidget(QtWidgets.QLabel(self.translations.get("recur_type", "周期类型:")))
        freqLayout.addWidget(self.freqCombo)
        freqLayout.addWidget(QtWidgets.QLabel(self.translations.get("recur_interval", "间隔:")))
        freqLayout.addWidget(self.intervalSpin)
        freqLayout.addStretch()
        layout.addRow("", freqLayout)
        
        # 自定义间隔行
        layout.addRow("", self.customWidget)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addRow(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def toggleDeadline(self, checked):
        self.deadlineEdit.setEnabled(not checked)

    def toggleRecurring(self, checked):
        self.freqCombo.setEnabled(checked)
        self.intervalSpin.setEnabled(checked)
        self.onFreqChanged()

    def onFreqChanged(self):
        if not hasattr(self, 'customWidget'):
            return
        is_custom = self.freqCombo.currentData() == "CUSTOM" and self.recurringCheck.isChecked()
        self.customWidget.setVisible(is_custom)
        self.customWidget.setEnabled(is_custom)
        self.intervalSpin.setVisible(self.freqCombo.currentData() != "CUSTOM")

    def getData(self):
        due = None if self.noDeadlineCheck.isChecked() else self.deadlineEdit.dateTime().toPyDateTime()
        priority = self.priorityCombo.currentData()
        
        rrule_val = None
        if self.recurringCheck.isChecked():
            freq = self.freqCombo.currentData()
            if freq == "CUSTOM":
                mins = (self.intervalDaysSpin.value() * 24 * 60 + 
                       self.intervalHoursSpin.value() * 60 + 
                       self.intervalMinutesSpin.value())
                if mins > 0:
                    rrule_val = minutes_to_rrule(mins)
            else:
                interval = self.intervalSpin.value()
                rrule_val = make_rrule(freq, interval)
        
        return {
            "summary": self.taskNameEdit.text(),
            "description": self.taskDetailEdit.toPlainText(),
            "priority": priority,
            "due": due,
            "rrule": rrule_val
        }
