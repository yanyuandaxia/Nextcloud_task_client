# ---------------------------
# 设置对话框（不包含语言项，由语言菜单控制）
# ---------------------------


from translations import TRANSLATIONS


from PyQt5 import QtWidgets


import json


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, conf_path, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.conf_path = conf_path
        self.setWindowTitle(TRANSLATIONS["en"]["settings_title"])
        layout = QtWidgets.QFormLayout(self)

        try:
            with open(conf_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception as e:
            self.config = {}

        self.tasksPathEdit = QtWidgets.QLineEdit(
            self.config.get("tasks_json_path", ""))
        layout.addRow(
            TRANSLATIONS["en"]["tasks_json_path_label"], self.tasksPathEdit)

        self.iconPathEdit = QtWidgets.QLineEdit(
            self.config.get("icon_path", ""))
        layout.addRow(TRANSLATIONS["en"]["icon_path_label"], self.iconPathEdit)

        self.urlEdit = QtWidgets.QLineEdit(self.config.get("url", ""))
        layout.addRow(TRANSLATIONS["en"]["url_label"], self.urlEdit)

        self.usernameEdit = QtWidgets.QLineEdit(
            self.config.get("username", ""))
        layout.addRow(TRANSLATIONS["en"]["username_label"], self.usernameEdit)

        self.passwordEdit = QtWidgets.QLineEdit(
            self.config.get("password", ""))
        self.passwordEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addRow(TRANSLATIONS["en"]["password_label"], self.passwordEdit)

        self.checkIntervalSpin = QtWidgets.QSpinBox()
        self.checkIntervalSpin.setRange(1, 100000)
        self.checkIntervalSpin.setValue(self.config.get("check_interval", 600))
        layout.addRow(
            TRANSLATIONS["en"]["check_interval_label"], self.checkIntervalSpin)

        self.showDDLCheck = QtWidgets.QCheckBox()
        self.showDDLCheck.setChecked(
            self.config.get("show_ddl_message_box", True))
        layout.addRow(TRANSLATIONS["en"]["show_ddl_label"], self.showDDLCheck)

        self.sslVerifyCheck = QtWidgets.QCheckBox()
        self.sslVerifyCheck.setChecked(
            self.config.get("ssl_verify_cert", False))
        layout.addRow(TRANSLATIONS["en"]
                      ["ssl_verify_label"], self.sslVerifyCheck)

        self.offlineModeCheck = QtWidgets.QCheckBox()
        self.offlineModeCheck.setChecked(
            self.config.get("offline_mode", False))
        layout.addRow(
            TRANSLATIONS["en"]["offline_mode_label"], self.offlineModeCheck)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.saveConfig)
        buttonBox.rejected.connect(self.reject)
        layout.addRow(buttonBox)

    def saveConfig(self):
        new_config = {
            "tasks_json_path": self.tasksPathEdit.text(),
            "icon_path": self.iconPathEdit.text(),
            "url": self.urlEdit.text(),
            "username": self.usernameEdit.text(),
            "password": self.passwordEdit.text(),
            "check_interval": self.checkIntervalSpin.value(),
            "show_ddl_message_box": self.showDDLCheck.isChecked(),
            "ssl_verify_cert": self.sslVerifyCheck.isChecked(),
            "offline_mode": self.offlineModeCheck.isChecked(),
            "language": "zh" if self.config.get("language", "en") == "zh" else "en"
        }
        try:
            with open(self.conf_path, "w", encoding="utf-8") as f:
                json.dump(new_config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, TRANSLATIONS["en"]["error"],
                                           TRANSLATIONS["en"]["failed_write_config"].format(e))
            return
        QtWidgets.QMessageBox.information(self, TRANSLATIONS["en"]["settings"],
                                          TRANSLATIONS["en"]["config_saved"])
        # self.accept()
