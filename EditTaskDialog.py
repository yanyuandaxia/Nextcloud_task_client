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
            current_priority = 2  # 默认设为"高"
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

        # 使用 QDateTimeEdit 同时支持日期和时间的编辑
        self.deadlineEdit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.deadlineEdit.setCalendarPopup(True)
        self.deadlineEdit.setDisplayFormat("yyyy-MM-dd HH:mm")
        if task.due:
            # 确保 due 是 datetime 对象
            import datetime
            due_datetime = task.due
            if isinstance(due_datetime, str):
                try:
                    due_datetime = datetime.datetime.strptime(due_datetime, "%Y-%m-%dT%H:%M:%S")
                except Exception:
                    due_datetime = datetime.datetime.now()
            self.deadlineEdit.setDateTime(QtCore.QDateTime(due_datetime))
            initial_no_due = False
        else:
            initial_no_due = True
            self.deadlineEdit.setEnabled(False)
            
        # 创建无到期时间复选框
        self.noDeadlineCheck = QtWidgets.QCheckBox(self.translations.get("no_due", "无到期时间"))
        self.noDeadlineCheck.setChecked(initial_no_due)
        self.noDeadlineCheck.toggled.connect(self.toggleDeadline)

        # 周期任务设置
        self.recurringCheck = QtWidgets.QCheckBox(self.translations.get("recurring_task", "周期任务"))
        is_recurring = getattr(task, 'is_recurring', False) or False
        self.recurringCheck.setChecked(is_recurring)
        self.recurringCheck.toggled.connect(self.toggleRecurring)
        
        # 获取间隔分钟数，兼容旧版 recurrence_interval_days
        interval_minutes = getattr(task, 'recurrence_interval_minutes', None)
        if interval_minutes is None:
            # 兼容旧版：从 recurrence_interval_days 转换
            interval_days_old = getattr(task, 'recurrence_interval_days', None)
            if interval_days_old:
                interval_minutes = interval_days_old * 24 * 60
            else:
                interval_minutes = 0
        
        # 拆分为天、小时、分钟
        days = interval_minutes // (24 * 60)
        hours = (interval_minutes % (24 * 60)) // 60
        minutes = interval_minutes % 60
        
        self.intervalDaysSpin = QtWidgets.QSpinBox()
        self.intervalDaysSpin.setMinimum(0)
        self.intervalDaysSpin.setMaximum(365)
        self.intervalDaysSpin.setValue(days)
        self.intervalDaysSpin.setEnabled(is_recurring)
        
        self.intervalHoursSpin = QtWidgets.QSpinBox()
        self.intervalHoursSpin.setMinimum(0)
        self.intervalHoursSpin.setMaximum(23)
        self.intervalHoursSpin.setValue(hours)
        self.intervalHoursSpin.setEnabled(is_recurring)
        
        self.intervalMinutesSpin = QtWidgets.QSpinBox()
        self.intervalMinutesSpin.setMinimum(0)
        self.intervalMinutesSpin.setMaximum(59)
        self.intervalMinutesSpin.setValue(minutes)
        self.intervalMinutesSpin.setEnabled(is_recurring)
        
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
                total_minutes = None
        
        return {
            "summary": self.taskNameEdit.text(),
            "description": self.taskDetailEdit.toPlainText(),
            "priority": priority,
            "due": due,
            "is_recurring": self.recurringCheck.isChecked() and total_minutes is not None,
            "recurrence_interval_minutes": total_minutes
        }
