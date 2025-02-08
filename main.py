#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtCore, QtGui
from nextcloudtasks import NextcloudTask, Todo
from local_tasks import load_local_tasks, save_server_tasks
import sys
import datetime
import json
import urllib3

TRANSLATIONS = {
    "zh": {
        "window_title": "Nextcloud Task 同步客户端",
        "add_task": "添加任务",
        "edit_task": "修改任务",
        "delete_task": "删除任务",
        "sync_task": "同步任务",
        "fetch_task": "获取任务",
        "task_name": "任务名称:",
        "task_detail": "任务详情:",
        "priority": "优先级:",
        "deadline": "截止时间:",
        "completed": "完成",
        "restore": "恢复",
        "quit": "退出",
        "language_menu": "语言",
        "about_menu": "关于",
        "tray_tooltip": "Nextcloud Task 同步客户端",
        "app_minimized": "应用已最小化到系统托盘",
        # 消息框相关
        "connection_error": "连接错误",
        "connection_failed": "连接 Nextcloud 失败: {}",
        "fetch_error_title": "获取任务错误",
        "fetch_error_message": "网络异常，将加载本地数据: {}",
        "select_task_edit": "请选择一项任务进行修改",
        "edit_success": "任务已修改",
        "add_success": "任务已添加并自动同步至服务器",
        "add_error": "添加任务错误",
        "sync_error": "同步任务错误",
        "delete_error": "删除任务错误",
        "delete_error_sub": "将仅删除本地数据",
        "delete_success": "任务已删除",
        "sync_warning": "当前网络不可用，无法与服务器同步，操作仅限本地保存。",
        "sync_success": "任务同步完成，JSON文件与服务器数据保持一致",
        "update_error": "更新任务错误",
        "local_edit_success": "本地任务已修改",
        "no_local_task": "未找到对应本地任务数据",
        # 托盘消息相关
        "tray_deadline_title": "任务提醒",
        "tray_deadline_message": "任务 '{summary}' 即将到期",
        # JSON数据不一致时的询问
        "json_mismatch_title": "数据不一致",
        "json_mismatch_message": "本地数据与服务器数据不一致，您想使用哪一份数据？",
        "use_local": "使用本地数据",
        "use_server": "使用服务器数据",
        # 关于菜单相关
        "about_title": "关于",
        "about_message": "作者：燕园大侠\nGitHub：https://github.com/yanyuandaxia/Nextcloud_task_client"
    },
    "en": {
        "window_title": "Nextcloud Task Sync Client",
        "add_task": "Add Task",
        "edit_task": "Edit Task",
        "delete_task": "Delete Task",
        "sync_task": "Sync Task",
        "fetch_task": "Fetch Tasks",
        "task_name": "Task Name:",
        "task_detail": "Task Detail:",
        "priority": "Priority:",
        "deadline": "Deadline:",
        "completed": "Completed",
        "restore": "Restore",
        "quit": "Quit",
        "language_menu": "Language",
        "about_menu": "About",
        "tray_tooltip": "Nextcloud Task Sync Client",
        "app_minimized": "Application minimized to system tray",
        # 消息框相关
        "connection_error": "Connection Error",
        "connection_failed": "Failed to connect to Nextcloud: {}",
        "fetch_error_title": "Fetch Tasks Error",
        "fetch_error_message": "Network error, loading local data: {}",
        "select_task_edit": "Please select a task to edit",
        "edit_success": "Task has been updated",
        "add_success": "Task added and synced to server successfully",
        "add_error": "Add Task Error",
        "sync_error": "Sync Task Error",
        "delete_error": "Delete Task Error",
        "delete_error_sub": "Only local data will be deleted",
        "delete_success": "Task deleted",
        "sync_warning": "Network unavailable, only local changes will be saved.",
        "sync_success": "Tasks synced, JSON file updated with server data",
        "update_error": "Update Task Error",
        "local_edit_success": "Local task updated",
        "no_local_task": "Corresponding local task not found",
        # 托盘消息相关
        "tray_deadline_title": "Task Reminder",
        "tray_deadline_message": "Task '{summary}' is about to expire",
        # JSON数据不一致时的询问
        "json_mismatch_title": "Data Mismatch",
        "json_mismatch_message": "Local data and server data are inconsistent. Which one would you like to use?",
        "use_local": "Use Local Data",
        "use_server": "Use Server Data",
        # 关于菜单相关
        "about_title": "About",
        "about_message": "Author: Yanyuandaxia\nGitHub: https://github.com/yanyuandaxia/Nextcloud_task_client"
    }
}

# 添加任务对话框


class AddTaskDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AddTaskDialog, self).__init__(parent)
        self.current_language = parent.current_language if parent else "zh"
        self.translations = parent.translations if parent else TRANSLATIONS
        self.setWindowTitle(
            self.translations[self.current_language]["add_task"])
        layout = QtWidgets.QFormLayout(self)

        self.taskNameEdit = QtWidgets.QLineEdit()
        self.taskDetailEdit = QtWidgets.QTextEdit()
        self.prioritySpin = QtWidgets.QSpinBox()
        self.prioritySpin.setRange(0, 10)
        self.deadlineEdit = QtWidgets.QDateTimeEdit(
            QtCore.QDateTime.currentDateTime())
        self.deadlineEdit.setCalendarPopup(True)

        layout.addRow(
            self.translations[self.current_language]["task_name"], self.taskNameEdit)
        layout.addRow(
            self.translations[self.current_language]["task_detail"], self.taskDetailEdit)
        layout.addRow(
            self.translations[self.current_language]["priority"], self.prioritySpin)
        layout.addRow(
            self.translations[self.current_language]["deadline"], self.deadlineEdit)

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


# 修改任务对话框，预填已有任务数据
class EditTaskDialog(QtWidgets.QDialog):
    def __init__(self, parent, task):
        super(EditTaskDialog, self).__init__(parent)
        self.current_language = parent.current_language if parent else "zh"
        self.translations = parent.translations if parent else TRANSLATIONS
        self.setWindowTitle(
            self.translations[self.current_language]["edit_task"])
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

        layout.addRow(
            self.translations[self.current_language]["task_name"], self.taskNameEdit)
        layout.addRow(
            self.translations[self.current_language]["task_detail"], self.taskDetailEdit)
        layout.addRow(
            self.translations[self.current_language]["priority"], self.prioritySpin)
        layout.addRow(
            self.translations[self.current_language]["deadline"], self.deadlineEdit)

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


# 主窗口：显示任务列表（只读）、添加任务、修改任务、同步任务等
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        if len(sys.argv)>1:
            self.path_conf = sys.argv[1]
        else:
            self.path_conf = "conf.json"
        def load_conf(path_conf):
            with open(path_conf, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config
        self.config = load_conf(self.path_conf)
        self.path_tasks = self.config["tasks_json_path"]
        self.path_icon = self.config["icon_path"]
        self.current_language = self.config["language"]  # "zh" 或 "en"
        self.translations = TRANSLATIONS
        self.setWindowTitle(
            self.translations[self.current_language]["window_title"])
        self.resize(530, 400)
        self.initUI()
        self.createMenuBar()  # 增加菜单栏（含语言切换）
        self.createTrayIcon()
        self.setWindowIcon(QtGui.QIcon(self.path_icon))
        self.setupDeadlineChecker()

        # 从文件加载本地任务列表（JSON 格式）
        self.local_tasks = load_local_tasks(self.path_tasks)
        self.tasks = None

        if not self.config["ssl_verify_cert"]:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        # 加载 Nextcloud 参数，初始化客户端
        self.nc_client = NextcloudTask(config=self.config)
        if not self.config['offline_mode']:
            try:
                self.nc_client.connect(
                    self.config["username"], self.config["password"])
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    self.translations[self.current_language]["connection_error"],
                    self.translations[self.current_language]["connection_failed"].format(
                        e)
                )

    def initUI(self):
        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)
        layout = QtWidgets.QVBoxLayout(centralWidget)

        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels([
            self.translations[self.current_language]["completed"],
            self.translations[self.current_language]["task_name"].replace(
                ":", ""),
            self.translations[self.current_language]["priority"].replace(
                ":", ""),
            self.translations[self.current_language]["deadline"].replace(
                ":", ""),
            self.translations[self.current_language]["task_detail"].replace(
                ":", "")
        ])
        self.tableWidget.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.tableWidget)

        btnLayout = QtWidgets.QHBoxLayout()
        self.fetchButton = QtWidgets.QPushButton(
            self.translations[self.current_language]["fetch_task"])
        self.addButton = QtWidgets.QPushButton(
            self.translations[self.current_language]["add_task"])
        self.editButton = QtWidgets.QPushButton(
            self.translations[self.current_language]["edit_task"])
        self.deleteButton = QtWidgets.QPushButton(
            self.translations[self.current_language]["delete_task"])
        self.syncButton = QtWidgets.QPushButton(
            self.translations[self.current_language]["sync_task"])

        btnLayout.addWidget(self.fetchButton)
        btnLayout.addWidget(self.addButton)
        btnLayout.addWidget(self.editButton)
        btnLayout.addWidget(self.deleteButton)
        btnLayout.addWidget(self.syncButton)
        layout.addLayout(btnLayout)

        self.fetchButton.clicked.connect(self.fetchTasks)
        self.addButton.clicked.connect(self.openAddTaskDialog)
        self.editButton.clicked.connect(self.editTask)
        self.syncButton.clicked.connect(self.syncServerTasks)
        self.deleteButton.clicked.connect(self.deleteTask)

    def createMenuBar(self):
        menubar = self.menuBar()
        # 增加语言菜单
        self.languageMenu = menubar.addMenu(
            self.translations[self.current_language]["language_menu"])
        self.actionChinese = self.languageMenu.addAction("中文")
        self.actionEnglish = self.languageMenu.addAction("English")
        self.actionChinese.triggered.connect(lambda: self.setLanguage("zh"))
        self.actionEnglish.triggered.connect(lambda: self.setLanguage("en"))

        # 在语言菜单旁边增加一个“关于”菜单
        self.aboutMenu = menubar.addMenu(
            self.translations[self.current_language]["about_menu"])
        self.aboutAction = self.aboutMenu.addAction(
            self.translations[self.current_language]["about_menu"])
        self.aboutAction.triggered.connect(self.showAbout)

    def setLanguage(self, lang):
        if lang not in self.translations:
            return
        self.current_language = lang
        self.updateTranslations()

    def updateTranslations(self):
        # 更新主窗口及各控件文本
        self.setWindowTitle(
            self.translations[self.current_language]["window_title"])
        self.tableWidget.setHorizontalHeaderLabels([
            self.translations[self.current_language]["completed"],
            self.translations[self.current_language]["task_name"].replace(
                ":", ""),
            self.translations[self.current_language]["priority"].replace(
                ":", ""),
            self.translations[self.current_language]["deadline"].replace(
                ":", ""),
            self.translations[self.current_language]["task_detail"].replace(
                ":", "")
        ])
        self.fetchButton.setText(
            self.translations[self.current_language]["fetch_task"])
        self.addButton.setText(
            self.translations[self.current_language]["add_task"])
        self.editButton.setText(
            self.translations[self.current_language]["edit_task"])
        self.deleteButton.setText(
            self.translations[self.current_language]["delete_task"])
        self.syncButton.setText(
            self.translations[self.current_language]["sync_task"])
        self.trayIcon.setToolTip(
            self.translations[self.current_language]["tray_tooltip"])
        # 更新托盘菜单
        trayMenu = self.trayIcon.contextMenu()
        trayMenu.actions()[0].setText(
            self.translations[self.current_language]["restore"])
        trayMenu.actions()[1].setText(
            self.translations[self.current_language]["quit"])
        # 更新语言菜单显示
        self.languageMenu.setTitle(
            self.translations[self.current_language]["language_menu"])
        # 更新关于菜单显示
        self.aboutMenu.setTitle(
            self.translations[self.current_language]["about_menu"])
        self.aboutAction.setText(
            self.translations[self.current_language]["about_menu"])

    def showAbout(self):
        # 弹出关于窗口，显示作者和 GitHub 链接
        QtWidgets.QMessageBox.information(
            self,
            self.translations[self.current_language]["about_title"],
            self.translations[self.current_language]["about_message"]
        )

    def createTrayIcon(self):
        self.trayIcon = QtWidgets.QSystemTrayIcon(self)
        icon = QtGui.QIcon(self.path_icon)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setToolTip(
            self.translations[self.current_language]["tray_tooltip"])
        trayMenu = QtWidgets.QMenu(self)
        restoreAction = trayMenu.addAction(
            self.translations[self.current_language]["restore"])
        restoreAction.triggered.connect(self.showNormal)
        quitAction = trayMenu.addAction(
            self.translations[self.current_language]["quit"])
        quitAction.triggered.connect(QtWidgets.QApplication.quit)
        self.trayIcon.setContextMenu(trayMenu)
        self.trayIcon.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        # self.trayIcon.showMessage(
        #     self.translations[self.current_language]["window_title"],
        #     self.translations[self.current_language]["app_minimized"],
        #     QtWidgets.QSystemTrayIcon.Information, 2000
        # )

    def checkLocalServerTasks(self):
        def normalize_due_datetime(due):
            if isinstance(due, datetime.datetime):
                return due
            try:
                # 尝试 ISO 格式（带 T 分隔符）
                dt = datetime.datetime.strptime(due, "%Y-%m-%dT%H:%M:%S")
                return dt
            except Exception:
                try:
                    # 尝试空格分隔的格式
                    dt = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return None

        def compare_data(local_data, server_tasks):
            local_data_in = local_data.copy()
            server_tasks_in = server_tasks.copy()
            local_data_in.sort(key=lambda x: x.get("uid", ""))
            server_tasks_in.sort(key=lambda x: x.get("uid", ""))
            # print(local_data_in, server_tasks_in)
            # 本地数据与服务器数据不一致时返回 True
            if len(local_data) != len(server_tasks):
                return True
            for i, task in enumerate(local_data_in):
                task['due'] = normalize_due_datetime(task.get('due', ''))
                server_tasks_in[i]['due'] = normalize_due_datetime(
                    server_tasks_in[i].get('due', ''))
                if str(task) != str(server_tasks_in[i]):
                    return True
            return False

        try:
            if self.config['offline_mode']:
                raise Exception("offline mode")
            self.nc_client.updateTodos()
            todos = self.nc_client.todos
            self.tasks = []
            for t in todos:
                task = Todo(t.data)
                self.tasks.append(task)
            # 将服务器任务转换为字典列表
            server_tasks = [task.to_dict() for task in self.tasks]
            # 加载本地 JSON 数据并归一化 due 字段
            local_data = load_local_tasks(self.path_tasks)
            # 比较本地与服务器数据（归一化后的）
            if compare_data(local_data, server_tasks):
                msgBox = QtWidgets.QMessageBox(self)
                msgBox.setWindowTitle(
                    self.translations[self.current_language]["json_mismatch_title"])
                msgBox.setText(
                    self.translations[self.current_language]["json_mismatch_message"])
                btnLocal = msgBox.addButton(
                    self.translations[self.current_language]["use_local"], QtWidgets.QMessageBox.AcceptRole)
                btnServer = msgBox.addButton(
                    self.translations[self.current_language]["use_server"], QtWidgets.QMessageBox.RejectRole)
                msgBox.exec_()
                if msgBox.clickedButton() == btnLocal:
                    final_tasks = local_data
                    self.syncServerTasks(check=False)
                else:
                    final_tasks = server_tasks
            else:
                final_tasks = server_tasks
            # 保存最终数据到本地 JSON 文件
            save_server_tasks(final_tasks, self.path_tasks)
        except Exception as e:
            print(e)
            if str(e) != "offline mode":
                QtWidgets.QMessageBox.critical(
                    self,
                    self.translations[self.current_language]["fetch_error_title"],
                    self.translations[self.current_language]["fetch_error_message"].format(
                        e)
                )
        self.refreshTaskTable()

    def fetchTasks(self):
        try:
            if self.config['offline_mode']:
                raise Exception("offline mode")
            self.nc_client.updateTodos()
            todos = self.nc_client.todos
            self.tasks = []
            for t in todos:
                task = Todo(t.data)
                self.tasks.append(task)
            # 保存服务器任务到本地 JSON 文件
            tasks_list = [task.to_dict() for task in self.tasks]
            save_server_tasks([], self.path_tasks)
            save_server_tasks(tasks_list, self.path_tasks)
        except Exception as e:
            if str(e) != "offline mode":
                QtWidgets.QMessageBox.critical(
                    self,
                    self.translations[self.current_language]["fetch_error_title"],
                    self.translations[self.current_language]["fetch_error_message"].format(
                        e)
                )
            # 网络异常则加载本地数据
            tasks_list = load_local_tasks(self.path_tasks)
            self.tasks = []
            for t in tasks_list:
                local_task = type("LocalTask", (), {})()
                local_task.summary = t.get("summary", "")
                local_task.uid = t.get("uid", "")
                local_task.priority = t.get("priority", "")
                local_task.due = t.get("due", None)
                local_task.status = t.get("status", "")
                self.tasks.append(local_task)
        self.refreshTaskTable()

    def refreshTaskTable(self):
        self.tableWidget.setRowCount(0)
        try:
            if self.config['offline_mode']:
                raise Exception("offline mode")
            self.nc_client.updateTodos()
            todos = self.nc_client.todos
            self.tasks = []
            for t in todos:
                task = Todo(t.data)
                self.tasks.append(task)
            tasks_list = [task.to_dict() for task in self.tasks]
            save_server_tasks(tasks_list, self.path_tasks)
        except Exception as e:
            if str(e) != "offline mode":
                QtWidgets.QMessageBox.critical(
                    self,
                    self.translations[self.current_language]["fetch_error_title"],
                    self.translations[self.current_language]["fetch_error_message"].format(
                        e)
                )
            tasks_list = load_local_tasks(self.path_tasks)
            self.tasks = []
            for t in tasks_list:
                local_task = type("LocalTask", (), {})()
                local_task.summary = t.get("summary", "")
                local_task.uid = t.get("uid", "")
                local_task.priority = t.get("priority", "")
                local_task.due = t.get("due", None)
                local_task.description = t.get("description", "")
                local_task.status = t.get("status", "NEEDS-ACTION")
                self.tasks.append(local_task)

        self.tableWidget.setRowCount(0)
        for task in self.tasks:
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)

            checkbox = QtWidgets.QCheckBox()
            if task.status == "COMPLETED":
                checkbox.setChecked(True)
            checkbox.setProperty("uid", task.uid)
            checkbox.setProperty("summary", task.summary)
            checkbox.stateChanged.connect(self.onCheckboxStateChanged)
            self.tableWidget.setCellWidget(rowPosition, 0, checkbox)

            item_name = QtWidgets.QTableWidgetItem(task.summary)
            item_name.setData(QtCore.Qt.UserRole, task.uid)
            self.tableWidget.setItem(rowPosition, 1, item_name)
            self.tableWidget.setItem(
                rowPosition, 2, QtWidgets.QTableWidgetItem(str(task.priority)))
            deadline_str = task.due.strftime(
                '%Y-%m-%d %H:%M') if task.due else "无"
            self.tableWidget.setItem(
                rowPosition, 3, QtWidgets.QTableWidgetItem(deadline_str))
            detail_str = task.description if task.description else "无"
            self.tableWidget.setItem(
                rowPosition, 4, QtWidgets.QTableWidgetItem(detail_str))

    def onCheckboxStateChanged(self, state):
        checkbox = self.sender()
        if not isinstance(checkbox, QtWidgets.QCheckBox):
            return
        is_checked = checkbox.isChecked()
        uid = checkbox.property("uid")
        summary = checkbox.property("summary")
        new_percent = 100 if is_checked else 0
        new_status = "COMPLETED" if is_checked else "NEEDS-ACTION"

        if uid:
            try:
                if self.config['offline_mode']:
                    raise Exception("offline mode")
                self.nc_client.updateTodo(uid, percent_complete=new_percent)
            except Exception as e:
                if str(e) != "offline mode":
                    QtWidgets.QMessageBox.warning(
                        self,
                        self.translations[self.current_language]["update_error"],
                        f"{self.translations[self.current_language]['update_error']}: {summary} 更新失败: {e}"
                    )

        tasks = load_local_tasks(self.path_tasks)
        updated = False
        for task in tasks:
            if (uid and task.get("uid") == uid) or (not uid and task.get("summary") == summary):
                task["status"] = new_status
                task["percent_complete"] = new_percent
                updated = True
        if updated:
            save_server_tasks(tasks, self.path_tasks)
        self.fetchTasks()

    def openAddTaskDialog(self):
        dialog = AddTaskDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.getData()
            self.local_tasks.append(data)
            save_server_tasks(self.local_tasks, self.path_tasks)

            try:
                if self.config['offline_mode']:
                    raise Exception("offline mode")
                self.nc_client.addTodo(
                    data["summary"], priority=data["priority"], percent_complete=0)
                self.nc_client.updateTodos()
                uid = self.nc_client.getUidbySummary(data["summary"])
                self.nc_client.updateTodo(uid,
                                          note=data["description"],
                                          due=data["due"],
                                          priority=data["priority"])
                self.local_tasks.remove(data)
                save_server_tasks(self.local_tasks, self.path_tasks)
                QtWidgets.QMessageBox.information(
                    self,
                    self.translations[self.current_language]["add_task"],
                    self.translations[self.current_language]["add_success"]
                )
            except Exception as e:
                if str(e) != "offline mode":
                    QtWidgets.QMessageBox.critical(
                        self,
                        self.translations[self.current_language]["add_error"],
                        str(e)
                    )
            self.fetchTasks()

    def editTask(self):
        selectedItems = self.tableWidget.selectedItems()
        if not selectedItems:
            QtWidgets.QMessageBox.warning(
                self,
                self.translations[self.current_language]["edit_task"],
                self.translations[self.current_language]["select_task_edit"]
            )
            return
        row = selectedItems[0].row()
        uid = self.tableWidget.item(row, 1).data(QtCore.Qt.UserRole)
        if uid:
            try:
                task_obj = next((t for t in self.tasks if t.uid == uid), None)
                dialog = EditTaskDialog(self, task_obj)
                if dialog.exec_() == QtWidgets.QDialog.Accepted:
                    data = dialog.getData()
                    try:
                        if self.config['offline_mode']:
                            raise Exception("offline mode")
                        self.nc_client.updateTodo(uid,
                                                  summary=data["summary"],
                                                  note=data["description"],
                                                  due=data["due"],
                                                  priority=data["priority"])
                        QtWidgets.QMessageBox.information(
                            self,
                            self.translations[self.current_language]["edit_task"],
                            self.translations[self.current_language]["edit_success"]
                        )
                    except Exception as e:
                        if str(e) != "offline mode":
                            QtWidgets.QMessageBox.warning(
                                self,
                                self.translations[self.current_language]["update_error"],
                                f"{self.translations[self.current_language]['update_error']}: 网络错误，将仅更新本地数据.\n错误信息: {e}"
                            )
                        tasks = load_local_tasks(self.path_tasks)
                        updated = False
                        for t in tasks:
                            if t.get("uid") == uid:
                                t.update(data)
                                updated = True
                                break
                        if updated:
                            save_server_tasks(tasks, self.path_tasks)
                    self.fetchTasks()
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    self.translations[self.current_language]["edit_task"],
                    str(e)
                )
        else:
            index = None
            task_name = self.tableWidget.item(row, 1).text()
            for i, task in enumerate(self.local_tasks):
                if task.get("summary") == task_name:
                    index = i
                    break
            if index is not None:
                dialog = EditTaskDialog(self, type(
                    "LocalTask", (), self.local_tasks[index])())
                if dialog.exec_() == QtWidgets.QDialog.Accepted:
                    data = dialog.getData()
                    self.local_tasks[index] = data
                    save_server_tasks(self.local_tasks, self.path_tasks)
                    QtWidgets.QMessageBox.information(
                        self,
                        self.translations[self.current_language]["edit_task"],
                        self.translations[self.current_language]["local_edit_success"]
                    )
                    self.fetchTasks()
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.translations[self.current_language]["edit_task"],
                    self.translations[self.current_language]["no_local_task"]
                )

    def deleteTask(self):
        selectedItems = self.tableWidget.selectedItems()
        if not selectedItems:
            QtWidgets.QMessageBox.warning(
                self,
                self.translations[self.current_language]["delete_task"],
                self.translations[self.current_language]["select_task_edit"]
            )
            return
        row = selectedItems[0].row()
        summary = self.tableWidget.item(row, 1).text()
        uid = self.tableWidget.item(row, 1).data(QtCore.Qt.UserRole)

        if uid:
            try:
                if self.config['offline_mode']:
                    raise Exception("offline mode")
                self.nc_client.deleteByUid(uid)
            except Exception as e:
                if str(e) != "offline mode":
                    QtWidgets.QMessageBox.warning(
                        self,
                        self.translations[self.current_language]["delete_error"],
                        f"{self.translations[self.current_language]['delete_error']}:{e}\n{self.translations[self.current_language]['delete_error_sub']}"
                    )
        tasks = load_local_tasks(self.path_tasks)
        new_tasks = [task for task in tasks if task.get(
            "uid") != uid and task.get("summary") != summary]
        save_server_tasks(new_tasks, self.path_tasks)
        self.tasks = load_local_tasks(self.path_tasks)

        QtWidgets.QMessageBox.information(
            self,
            self.translations[self.current_language]["delete_task"],
            self.translations[self.current_language]["delete_success"]
        )
        self.fetchTasks()

    def syncServerTasks(self, check=True):
        if check:
            self.checkLocalServerTasks()
        try:
            if self.config['offline_mode']:
                raise Exception("offline mode")
            self.nc_client.updateTodos()
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                self.translations[self.current_language]["sync_task"],
                self.translations[self.current_language]["sync_warning"]
            )
            return

        local_tasks = load_local_tasks(self.path_tasks)
        for task in local_tasks:
            try:
                if not task.get("uid"):
                    self.nc_client.addTodo(
                        task["summary"], priority=task["priority"],
                        percent_complete=task['percent_complete'])
                    self.nc_client.updateTodos()
                    uid = self.nc_client.getUidbySummary(task["summary"])
                    self.nc_client.updateTodo(
                        uid,
                        note=task["description"],
                        due=task["due"],
                        priority=task["priority"],
                        percent_complete=task['percent_complete'],)
                    task["uid"] = uid
                else:
                    self.nc_client.updateTodo(
                        task["uid"],
                        summary=task["summary"],
                        note=task.get("description", ""),
                        due=task["due"],
                        priority=task["priority"],
                        percent_complete=task['percent_complete'],)
            except Exception as ex:
                print(
                    f"{task['summary']} \n{self.translations[self.current_language]['sync_error']}: {ex}")
                task["sync_error"] = str(ex)

        try:
            self.nc_client.updateTodos()
            todos = self.nc_client.todos
            server_tasks = []
            for t in todos:
                task_obj = Todo(t.data)
                server_tasks.append(task_obj.to_dict())
            save_server_tasks(server_tasks, self.path_tasks)
        except Exception as ex:
            print(
                f"{self.translations[self.current_language]['sync_error']}: {ex}")

        QtWidgets.QMessageBox.information(
            self,
            self.translations[self.current_language]["sync_task"],
            self.translations[self.current_language]["sync_success"]
        )
        self.fetchTasks()

    def setupDeadlineChecker(self):
        self.deadlineTimer = QtCore.QTimer(self)
        self.deadlineTimer.timeout.connect(self.checkDeadlines)
        self.deadlineTimer.start(self.config["check_interval"] * 1000)

    def checkDeadlines(self):
        now = datetime.datetime.now()
        for task in self.tasks:
            # print(task.__dict__)
            if task.due and now > task.due - datetime.timedelta(minutes=10) and now < task.due:
                title = self.translations[self.current_language]["tray_deadline_title"]
                msg_template = self.translations[self.current_language]["tray_deadline_message"]
                msg = msg_template.format(summary=task.summary)
                self.trayIcon.showMessage(
                    title, msg, QtWidgets.QSystemTrayIcon.Warning, 5000)
                if self.config['show_ddl_message_box']:
                    QtWidgets.QMessageBox.warning(
                            self,
                            title,
                            f"{msg}"
                        )


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.checkLocalServerTasks()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
