# ---------------------------
# 关于对话框（点击菜单直接弹出，可复制内容）
# ---------------------------


from PyQt5 import QtWidgets


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, translations, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle(translations["about_title"])
        self.resize(400, 100)
        layout = QtWidgets.QVBoxLayout(self)
        self.textEdit = QtWidgets.QTextEdit()
        self.textEdit.setReadOnly(True)
        self.textEdit.setPlainText(translations["about_message"])
        layout.addWidget(self.textEdit)
        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Close)
        buttonBox.rejected.connect(self.reject)
        buttonBox.accepted.connect(self.accept)
        layout.addWidget(buttonBox)
