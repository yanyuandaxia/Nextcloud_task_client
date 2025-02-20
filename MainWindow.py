from translations import TRANSLATIONS
from nextcloudtasks import NextcloudTask, Todo
from local_tasks import load_local_tasks, save_local_tasks
from TaskHandler import TaskHandler
from SettingsDialog import SettingsDialog
from EditTaskDialog import EditTaskDialog
from AddTaskDialog import AddTaskDialog
from AboutDialog import AboutDialog
import datetime
import json
import sys
import urllib3
from PyQt5 import QtCore, QtGui, QtWidgets

# 自定义排序的 QTableWidgetItem


class SortedItem(QtWidgets.QTableWidgetItem):
    def __init__(self, text, sort_key=None):
        super().__init__(text)
        # 如果未指定，则用文本作为排序关键字
        self.sort_key = sort_key if sort_key is not None else text

    def __lt__(self, other):
        if isinstance(other, SortedItem):
            # 若内部数据为数字，则进行数字比较
            if isinstance(self.sort_key, (int, float)) and isinstance(other.sort_key, (int, float)):
                return self.sort_key < other.sort_key
            # 若为日期则直接比较
            if isinstance(self.sort_key, datetime.datetime) and isinstance(other.sort_key, datetime.datetime):
                return self.sort_key < other.sort_key
        # 否则按照字符串比较
        return str(self.sort_key) < str(other.sort_key)


# ---------------------------
# 主窗口
# ---------------------------


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        if len(sys.argv) > 1:
            self.path_conf = sys.argv[1]
        else:
            self.path_conf = "conf.json"

        def load_conf(path_conf):
            try:
                with open(path_conf, "r", encoding="utf-8") as f:
                    config = json.load(f)
                return config
            except Exception as e:
                dlg = SettingsDialog(path_conf)
                if dlg.exec_() == QtWidgets.QDialog.Accepted:
                    try:
                        with open(path_conf, "r", encoding="utf-8") as f:
                            config = json.load(f)
                        return config
                    except Exception as e2:
                        QtWidgets.QMessageBox.critical(None, TRANSLATIONS["en"]["error"],
                                                       TRANSLATIONS["en"]["cannot_load_config"])
                        sys.exit(1)
                else:
                    sys.exit(1)

        self.config = load_conf(self.path_conf)
        if "language" not in self.config.keys():
            self.config["language"] = "en"
        self.current_language = self.config.get("language")
        self.translations = TRANSLATIONS[self.current_language]

        if not self.config["ssl_verify_cert"]:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.path_tasks = self.config["tasks_json_path"]
        self.path_icon = self.config["icon_path"]
        self.setWindowTitle(self.translations["window_title"])
        self.resize(535, 400)
        self.initUI()
        self.createMenuBar()  # 含语言切换和设置
        self.createTrayIcon()
        self.setWindowIcon(QtGui.QIcon(self.path_icon))
        self.setupDeadlineChecker()
        if not self.config['offline_mode']:
            self.setupServerTasksChecker()

        self.nc_client = NextcloudTask(config=self.config)
        if not self.config['offline_mode']:
            try:
                self.nc_client.connect(
                    self.config["username"], self.config["password"])
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    self.translations["connection_error"],
                    self.translations["connection_failed"].format(e)
                )
        self.task_handler = TaskHandler(
            self.config, self.path_tasks, self.nc_client)
        self.tasks = self.task_handler.fetch_tasks()

    def initUI(self):
        centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(centralWidget)
        layout = QtWidgets.QVBoxLayout(centralWidget)

        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels([
            self.translations["completed"],
            self.translations["task_name"].replace(":", ""),
            self.translations["priority"].replace(":", ""),
            self.translations["deadline"].replace(":", ""),
            self.translations["task_detail"].replace(":", "")
        ])
        # 取消编辑，注意勾选框将在 itemChanged 中响应变化
        self.tableWidget.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.tableWidget)

        # 记录各列的当前排序顺序（用于点击时切换排序顺序）
        self.last_sort_order = {}

        # 连接表头点击信号（只对第0、1、2、3列响应排序）
        header = self.tableWidget.horizontalHeader()
        header.sectionClicked.connect(self.onHeaderClicked)

        # 监听 item 状态变化（用于完成列的勾选）
        self.tableWidget.itemChanged.connect(self.onItemChanged)

        btnLayout = QtWidgets.QHBoxLayout()
        self.fetchButton = QtWidgets.QPushButton(
            self.translations["fetch_task"])
        self.addButton = QtWidgets.QPushButton(self.translations["add_task"])
        self.editButton = QtWidgets.QPushButton(self.translations["edit_task"])
        self.deleteButton = QtWidgets.QPushButton(
            self.translations["delete_task"])
        self.syncButton = QtWidgets.QPushButton(self.translations["sync_task"])

        btnLayout.addWidget(self.fetchButton)
        btnLayout.addWidget(self.addButton)
        btnLayout.addWidget(self.editButton)
        btnLayout.addWidget(self.deleteButton)
        btnLayout.addWidget(self.syncButton)
        layout.addLayout(btnLayout)

        self.fetchButton.clicked.connect(self.fetchTasks)
        self.addButton.clicked.connect(self.openAddTaskDialog)
        self.editButton.clicked.connect(self.editTask)
        self.deleteButton.clicked.connect(self.deleteTask)
        self.syncButton.clicked.connect(self.syncServerTasks)

    def onHeaderClicked(self, logicalIndex):
        # 仅对第0（完成）、1（任务名）、2（优先级）、3（截止日期）列启用排序
        allowed = [0, 1, 2, 3]
        if logicalIndex not in allowed:
            return
        # 切换排序顺序：第一次点击为升序，再次点击为降序
        current_order = self.last_sort_order.get(
            logicalIndex, QtCore.Qt.AscendingOrder)
        new_order = QtCore.Qt.DescendingOrder if current_order == QtCore.Qt.AscendingOrder else QtCore.Qt.AscendingOrder
        self.last_sort_order[logicalIndex] = new_order
        self.tableWidget.sortItems(logicalIndex, new_order)

    def onItemChanged(self, item):
        # 仅对第0列（完成列）进行响应
        if item.column() != 0:
            return
        # 注意：为防止因刷新表格再次触发 itemChanged 信号，此处可考虑先断开信号，更新后再连接
        row = item.row()
        # 从任务名称所在列（第1列）取出 uid 与 summary
        uid_item = self.tableWidget.item(row, 1)
        if uid_item is None:
            return
        uid = uid_item.data(QtCore.Qt.UserRole)
        summary = uid_item.text()
        is_checked = item.checkState() == QtCore.Qt.Checked
        new_percent = 100 if is_checked else 0
        new_status = "COMPLETED" if is_checked else "NEEDS-ACTION"
        # 更新任务状态后重新刷新任务列表
        self.task_handler.update_status(uid, summary, new_status, new_percent)
        self.fetchTasks()

    def refreshTaskTable(self):
        # 在刷新期间屏蔽信号，防止 itemChanged 导致重复调用
        self.tableWidget.blockSignals(True)
        self.tableWidget.setRowCount(0)
        for task in self.tasks:
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)

            # 第0列：完成状态（使用可勾选项），同时保存排序关键字（1：完成，0：未完成）
            item_completed = SortedItem(
                "", sort_key=1 if task.status == "COMPLETED" else 0)
            item_completed.setFlags(
                QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable)
            if task.status == "COMPLETED":
                item_completed.setCheckState(QtCore.Qt.Checked)
            else:
                item_completed.setCheckState(QtCore.Qt.Unchecked)
            self.tableWidget.setItem(rowPosition, 0, item_completed)

            # 第1列：任务名称，同时存储 uid 方便查找任务
            item_name = SortedItem(task.summary, sort_key=task.summary)
            item_name.setData(QtCore.Qt.UserRole, task.uid)
            self.tableWidget.setItem(rowPosition, 1, item_name)

            # 第2列：优先级，先尝试转成数字用于排序
            try:
                p_val = int(task.priority)
            except Exception:
                p_val = None
            if p_val is None:
                display_priority = str(task.priority)
                sort_priority = 100  # 默认较低优先级
            else:
                if p_val == 0:
                    display_priority = self.translations.get(
                        "priority_extremely_high", "极高")
                elif 1 <= p_val <= 3:
                    display_priority = self.translations.get(
                        "priority_high", "高")
                elif 4 <= p_val <= 6:
                    display_priority = self.translations.get(
                        "priority_medium", "中")
                elif 7 <= p_val <= 9:
                    display_priority = self.translations.get(
                        "priority_low", "低")
                else:
                    display_priority = str(p_val)
                sort_priority = p_val
            item_priority = SortedItem(
                display_priority, sort_key=sort_priority)
            self.tableWidget.setItem(rowPosition, 2, item_priority)

            # 第3列：截止日期，若为 datetime 则显示格式化后的字符串，否则显示无截止日期，同时以 datetime 对象作排序依据
            if task.due and isinstance(task.due, datetime.datetime):
                deadline_str = task.due.strftime('%Y-%m-%d %H:%M')
                sort_deadline = task.due
            else:
                deadline_str = self.translations["no_due"]
                sort_deadline = datetime.datetime.max
            item_deadline = SortedItem(deadline_str, sort_key=sort_deadline)
            self.tableWidget.setItem(rowPosition, 3, item_deadline)

            # 第4列：任务详情（不启用排序，直接使用普通项）
            detail_str = task.description if task.description else (
                "无" if self.current_language == "zh" else "None")
            item_detail = QtWidgets.QTableWidgetItem(detail_str)
            self.tableWidget.setItem(rowPosition, 4, item_detail)
        self.tableWidget.blockSignals(False)

    # 其余函数保持不变
    def createMenuBar(self):
        menubar = self.menuBar()
        self.languageMenu = menubar.addMenu(self.translations["language_menu"])
        self.actionChinese = self.languageMenu.addAction("中文")
        self.actionEnglish = self.languageMenu.addAction("English")
        self.actionChinese.triggered.connect(lambda: self.setLanguage("zh"))
        self.actionEnglish.triggered.connect(lambda: self.setLanguage("en"))

        self.settingsAction = menubar.addAction(
            self.translations.get("settings", "设置"))
        self.settingsAction.triggered.connect(self.openSettingsDialog)

        self.aboutAction = menubar.addAction(self.translations["about_menu"])
        self.aboutAction.triggered.connect(self.showAbout)

    def openSettingsDialog(self):
        dlg = SettingsDialog(self.path_conf, self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            try:
                with open(self.path_conf, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                QtWidgets.QMessageBox.information(self, self.translations["settings"],
                                                  self.translations["config_updated"])
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, self.translations["error"],
                                              self.translations["reload_config_failed"].format(e))

    def setLanguage(self, lang):
        if lang not in TRANSLATIONS:
            return
        if lang == self.current_language:
            return
        self.current_language = lang
        self.config["language"] = lang
        self.translations = TRANSLATIONS[lang]
        try:
            with open(self.path_conf, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, self.translations["error"],
                                          self.translations["failed_write_config"].format(e))
        self.updateTranslations()

    def updateTranslations(self):
        self.setWindowTitle(self.translations["window_title"])
        self.tableWidget.setHorizontalHeaderLabels([
            self.translations["completed"],
            self.translations["task_name"].replace(":", ""),
            self.translations["priority"].replace(":", ""),
            self.translations["deadline"].replace(":", ""),
            self.translations["task_detail"].replace(":", "")
        ])
        self.fetchButton.setText(self.translations["fetch_task"])
        self.addButton.setText(self.translations["add_task"])
        self.editButton.setText(self.translations["edit_task"])
        self.deleteButton.setText(self.translations["delete_task"])
        self.syncButton.setText(self.translations["sync_task"])
        self.trayIcon.setToolTip(self.translations["tray_tooltip"])
        trayMenu = self.trayIcon.contextMenu()
        trayMenu.actions()[0].setText(self.translations["restore"])
        trayMenu.actions()[1].setText(self.translations["quit"])
        self.languageMenu.setTitle(self.translations["language_menu"])
        self.aboutAction.setText(self.translations["about_menu"])
        self.settingsAction.setText(self.translations.get("settings", "设置"))

    def showAbout(self):
        aboutDlg = AboutDialog(self.translations, self)
        aboutDlg.exec_()

    def createTrayIcon(self):
        self.trayIcon = QtWidgets.QSystemTrayIcon(self)
        icon = QtGui.QIcon(self.path_icon)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setToolTip(self.translations["tray_tooltip"])
        trayMenu = QtWidgets.QMenu(self)
        restoreAction = trayMenu.addAction(self.translations["restore"])
        restoreAction.triggered.connect(self.showNormal)
        quitAction = trayMenu.addAction(self.translations["quit"])
        quitAction.triggered.connect(QtWidgets.QApplication.quit)
        self.trayIcon.setContextMenu(trayMenu)
        self.trayIcon.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def fetchTasks(self):
        self.tasks = self.task_handler.fetch_tasks()
        self.refreshTaskTable()

    def openAddTaskDialog(self):
        dialog = AddTaskDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data = dialog.getData()
            self.task_handler.add_task(data)
            QtWidgets.QMessageBox.information(
                self,
                self.translations["add_task"],
                self.translations.get("add_success", "任务添加成功")
            )
            self.fetchTasks()

    def editTask(self):
        selectedItems = self.tableWidget.selectedItems()
        if not selectedItems:
            QtWidgets.QMessageBox.warning(
                self,
                self.translations["edit_task"],
                self.translations["select_task_edit"]
            )
            return
        row = selectedItems[0].row()
        uid = self.tableWidget.item(row, 1).data(QtCore.Qt.UserRole)
        if uid:
            task_obj = next((t for t in self.tasks if t.uid == uid), None)
            if not task_obj:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.translations["edit_task"],
                    self.translations.get("no_task_found", "未找到该任务")
                )
                return
            dialog = EditTaskDialog(self, task_obj)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                data = dialog.getData()
                self.task_handler.update_task(uid, data)
                QtWidgets.QMessageBox.information(
                    self,
                    self.translations["edit_task"],
                    self.translations.get("edit_success", "任务修改成功")
                )
                self.fetchTasks()
        else:
            task_name = self.tableWidget.item(row, 1).text()
            task_obj = next(
                (t for t in self.tasks if t.summary == task_name), None)
            if task_obj:
                dialog = EditTaskDialog(self, task_obj)
                if dialog.exec_() == QtWidgets.QDialog.Accepted:
                    data = dialog.getData()
                    self.task_handler.update_task(task_obj.uid, data)
                    QtWidgets.QMessageBox.information(
                        self,
                        self.translations["edit_task"],
                        self.translations.get("local_edit_success", "本地任务修改成功")
                    )
                    self.fetchTasks()
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    self.translations["edit_task"],
                    self.translations.get("no_local_task", "未找到本地任务")
                )

    def deleteTask(self):
        selectedItems = self.tableWidget.selectedItems()
        if not selectedItems:
            QtWidgets.QMessageBox.warning(
                self,
                self.translations["delete_task"],
                self.translations["select_task_edit"]
            )
            return
        row = selectedItems[0].row()
        summary = self.tableWidget.item(row, 1).text()
        uid = self.tableWidget.item(row, 1).data(QtCore.Qt.UserRole)
        self.task_handler.delete_task(uid, summary)
        QtWidgets.QMessageBox.information(
            self,
            self.translations["delete_task"],
            self.translations.get("delete_success", "任务删除成功")
        )
        self.fetchTasks()

    def checkLocalServerTasks(self):
        if self.config['offline_mode']:
            QtWidgets.QMessageBox.information(
                self,
                self.translations["sync_task"],
                self.translations["no_offline_mode_sync"]
            )
            return

        def normalize_due_datetime(due):
            if isinstance(due, datetime.datetime):
                return due
            try:
                dt = datetime.datetime.strptime(due, "%Y-%m-%dT%H:%M:%S")
                return dt
            except Exception:
                try:
                    dt = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S")
                    return dt
                except Exception:
                    return None

        def data_is_same(local_data, server_tasks):
            local_data_in = local_data.copy()
            server_tasks_in = server_tasks.copy()
            local_data_in.sort(key=lambda x: x.get("uid", ""))
            server_tasks_in.sort(key=lambda x: x.get("uid", ""))
            if len(local_data) != len(server_tasks):
                return False
            for i, task in enumerate(local_data_in):
                task['due'] = normalize_due_datetime(task.get('due', ''))
                server_tasks_in[i]['due'] = normalize_due_datetime(
                    server_tasks_in[i].get('due', ''))
                if str(task) != str(server_tasks_in[i]):
                    return False
            return True

        try:
            self.nc_client.updateTodos()
            todos = self.nc_client.todos
            self.tasks = [Todo(t.data) for t in todos]
            server_tasks = [task.to_dict() for task in self.tasks]
            local_data = load_local_tasks(self.path_tasks)
            if not data_is_same(local_data, server_tasks):
                msgBox = QtWidgets.QMessageBox(self)
                msgBox.setWindowTitle(self.translations["json_mismatch_title"])
                msgBox.setText(self.translations["json_mismatch_message"])
                btnLocal = msgBox.addButton(
                    self.translations["use_local"], QtWidgets.QMessageBox.AcceptRole)
                btnServer = msgBox.addButton(
                    self.translations["use_server"], QtWidgets.QMessageBox.RejectRole)
                msgBox.exec_()
                if msgBox.clickedButton() == btnLocal:
                    final_tasks = local_data
                    self.syncServerTasks(check=False)
                elif msgBox.clickedButton() == btnServer:
                    final_tasks = server_tasks
                else:
                    raise Exception("msgBox button error")
            else:
                final_tasks = server_tasks
            save_local_tasks(final_tasks, self.path_tasks)
        except Exception as e:
            print(e)
            QtWidgets.QMessageBox.critical(
                self,
                self.translations["fetch_error_title"],
                self.translations["fetch_error_message"].format(e)
            )
        self.refreshTaskTable()

    def syncServerTasks(self, check=True):
        if self.config['offline_mode']:
            QtWidgets.QMessageBox.information(
                self,
                self.translations["sync_task"],
                self.translations["no_offline_mode_sync"]
            )
            return

        if check:
            self.checkLocalServerTasks()
        try:
            self.nc_client.updateTodos()
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self,
                self.translations["sync_task"],
                self.translations["sync_warning"]
            )
            return

        local_tasks = load_local_tasks(self.path_tasks)
        for task in local_tasks:
            try:
                if not task.get("uid"):
                    self.nc_client.addTodo(task["summary"],
                                           priority=task["priority"],
                                           percent_complete=task.get('percent_complete', 0))
                    self.nc_client.updateTodos()
                    uid = self.nc_client.getUidbySummary(task["summary"])
                    self.nc_client.updateTodo(uid,
                                              note=task["description"],
                                              due=task["due"],
                                              priority=task["priority"],
                                              percent_complete=task.get('percent_complete', 0))
                    task["uid"] = uid
                else:
                    self.nc_client.updateTodo(task["uid"],
                                              summary=task["summary"],
                                              note=task.get("description", ""),
                                              due=task["due"],
                                              priority=task["priority"],
                                              percent_complete=task.get('percent_complete', 0))
            except Exception as ex:
                print(
                    f"{task['summary']} \n{self.translations['sync_error']}: {ex}")
                task["sync_error"] = str(ex)

        try:
            self.nc_client.updateTodos()
            todos = self.nc_client.todos
            server_tasks = [Todo(t.data).to_dict() for t in todos]
            save_local_tasks(server_tasks, self.path_tasks)
        except Exception as ex:
            print(f"{self.translations['sync_error']}: {ex}")

        QtWidgets.QMessageBox.information(
            self,
            self.translations["sync_task"],
            self.translations["sync_success"]
        )
        self.fetchTasks()

    def setupDeadlineChecker(self):
        self.deadlineTimer = QtCore.QTimer(self)
        self.deadlineTimer.timeout.connect(self.checkDeadlines)
        self.deadlineTimer.start(self.config["check_interval"] * 1000)

    def checkDeadlines(self):
        now = datetime.datetime.now()
        for task in self.tasks:
            if task.due and (now > (task.due - datetime.timedelta(minutes=10))) and (now < task.due):
                title = self.translations["tray_deadline_title"]
                msg_template = self.translations["tray_deadline_message"]
                msg = msg_template.format(summary=task.summary)
                self.trayIcon.showMessage(
                    title, msg, QtWidgets.QSystemTrayIcon.Warning, 5000)
                if self.config.get('show_ddl_message_box', False):
                    QtWidgets.QMessageBox.warning(self, title, msg)

    def setupServerTasksChecker(self):
        self.serverTimer = QtCore.QTimer(self)
        self.serverTimer.timeout.connect(self.checkServerTasks)
        self.serverTimer.start(self.config["check_interval"] * 1000)

    def checkServerTasks(self):
        self.fetchTasks()

    def showAbout(self):
        aboutDlg = AboutDialog(self.translations, self)
        aboutDlg.exec_()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())
