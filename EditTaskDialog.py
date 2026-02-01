from nextcloudtasks import make_rrule, minutes_to_rrule, parse_rrule, parse_rrule_to_minutes
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
        self._raw_description = task.description if task.description else ""
        self.taskDetailEdit = QtWidgets.QTextEdit()
        self.taskDetailEdit.setPlainText(self._raw_description)

        # 优先级选择
        self.priorityCombo = QtWidgets.QComboBox()
        self.priority_options = [
            (self.translations.get("priority_extremely_high", "极高"), 0),
            (self.translations.get("priority_high", "高"), 2),
            (self.translations.get("priority_medium", "中"), 5),
            (self.translations.get("priority_low", "低"), 8)
        ]
        for text, value in self.priority_options:
            self.priorityCombo.addItem(text, value)
        
        try:
            current_priority = int(task.priority)
        except Exception:
            current_priority = 2
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

        # 截止时间
        self.deadlineEdit = QtWidgets.QDateTimeEdit(QtCore.QDateTime.currentDateTime())
        self.deadlineEdit.setCalendarPopup(True)
        self.deadlineEdit.setDisplayFormat("yyyy-MM-dd HH:mm")
        if task.due:
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
            
        self.noDeadlineCheck = QtWidgets.QCheckBox(self.translations.get("no_due", "无到期时间"))
        self.noDeadlineCheck.setChecked(initial_no_due)
        self.noDeadlineCheck.toggled.connect(self.toggleDeadline)

        # 周期任务设置
        self.recurringCheck = QtWidgets.QCheckBox(self.translations.get("recurring_task", "周期任务"))
        
        # 解析现有 RRULE
        rrule_val = getattr(task, 'rrule', None)
        if rrule_val is None and isinstance(task, dict):
            rrule_val = task.get('rrule')
            
        is_recurring = bool(rrule_val)
        freq, interval = parse_rrule(rrule_val) if rrule_val else (None, 1)
        
        self.recurringCheck.setChecked(is_recurring)
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
        self.freqCombo.setEnabled(is_recurring)
        self.freqCombo.currentIndexChanged.connect(self.onFreqChanged)
        
        # 设置当前频率
        freq_index = 0  # 默认 DAILY
        is_custom = False
        if freq in ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]:
            for i, (_, val) in enumerate(self.freq_options):
                if val == freq:
                    freq_index = i
                    break
        elif freq in ["HOURLY", "MINUTELY"]:
            # 自定义间隔
            freq_index = 4  # CUSTOM
            is_custom = True
        self.freqCombo.setCurrentIndex(freq_index)
        
        # 间隔数值
        self.intervalSpin = QtWidgets.QSpinBox()
        self.intervalSpin.setMinimum(1)
        self.intervalSpin.setMaximum(999)
        self.intervalSpin.setValue(interval if not is_custom else 1)
        self.intervalSpin.setEnabled(is_recurring)
        
        # 自定义间隔设置
        self.customWidget = QtWidgets.QWidget()
        customLayout = QtWidgets.QHBoxLayout(self.customWidget)
        customLayout.setContentsMargins(0, 0, 0, 0)
        
        # 如果是自定义，解析分钟
        interval_minutes = parse_rrule_to_minutes(rrule_val) or 0 if is_custom else 0
        days = interval_minutes // (24 * 60)
        hours = (interval_minutes % (24 * 60)) // 60
        minutes = interval_minutes % 60
        
        self.intervalDaysSpin = QtWidgets.QSpinBox()
        self.intervalDaysSpin.setMinimum(0)
        self.intervalDaysSpin.setMaximum(365)
        self.intervalDaysSpin.setValue(days)
        
        self.intervalHoursSpin = QtWidgets.QSpinBox()
        self.intervalHoursSpin.setMinimum(0)
        self.intervalHoursSpin.setMaximum(23)
        self.intervalHoursSpin.setValue(hours)
        
        self.intervalMinutesSpin = QtWidgets.QSpinBox()
        self.intervalMinutesSpin.setMinimum(0)
        self.intervalMinutesSpin.setMaximum(59)
        self.intervalMinutesSpin.setValue(minutes)
        
        customLayout.addWidget(QtWidgets.QLabel(self.translations.get("interval_days", "天:")))
        customLayout.addWidget(self.intervalDaysSpin)
        customLayout.addWidget(QtWidgets.QLabel(self.translations.get("interval_hours", "小时:")))
        customLayout.addWidget(self.intervalHoursSpin)
        customLayout.addWidget(QtWidgets.QLabel(self.translations.get("interval_minutes", "分钟:")))
        customLayout.addWidget(self.intervalMinutesSpin)
        self.customWidget.setEnabled(is_custom and is_recurring)
        self.customWidget.setVisible(is_custom)
        
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
        
        description = self.taskDetailEdit.toPlainText()

        return {
            "summary": self.taskNameEdit.text(),
            "description": description,
            "priority": priority,
            "due": due,
            "rrule": rrule_val
        }
