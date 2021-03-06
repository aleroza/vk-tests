import json
import sys
from os import path

import vk
from PyQt5 import QtGui
from PyQt5.QtCore import QRegExp, QObject, pyqtSignal, QEventLoop
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi

import google_export
import vktests


class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        QMainWindow.__init__(self)
        loadUi('MainWindow.ui', self)

        self.GauthIco.setPixmap(QtGui.QPixmap("ico/question.png"))
        self.vkdialog = VKauthWindow()
        self.gsheetdialog = GSheets()
        self.VKauthExists = False
        self.vkauth = {}
        self.client = []
        self.targetQ = ""
        self.data = []
        self.nums = {}

        # Centering window
        # From https://pythonprogramminglanguage.com/pyqt5-center-window/
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self._stdout = StdoutRedirect()
        self._stdout.start()
        self._stdout.printOccur.connect(lambda x: self._append_text(x))

    def SaveBtn_clicked(self):
        if self.txtCheck.checkState(): vktests.save_to_txt(self.data)
        if self.csvCheck.checkState(): vktests.save_to_csv(self.data)
        if self.googleCheck.checkState(): self.gsheetdialog.show()

    def BtnsDisable(self):
        self.startBtn.setEnabled(False)
        self.saveBtn.setEnabled(False)
        if len(self.targetQLine.text()) > 0:
            self.targetQ = self.targetQLine.text()
            self.startBtn.setEnabled(True)
        if self.txtCheck.checkState() or self.csvCheck.checkState() or self.googleCheck.checkState():
            self.saveBtn.setEnabled(True)

    def StartBtn_clicked(self):
        self.consoleOut.setEnabled(True)
        self.data = []
        self.data = vktests.all_for_msgs(self.vkapi, self.data, self.targetQ, self.vkauth["ADMIN_ID"])
        if len(self.data) == 0:
            print("По запросу не найдено результатов")
            self.outputBox.setEnabled(False)
        else:
            self.outputBox.setEnabled(True)

    def GSheetsExport(self, sheet_name, wsheet_name):
        google_export.main_export(self.client, self.data, sheet_name, wsheet_name)

    def VKauthExists_get(self):
        return self.VKauthExists

    def vkauth_get(self):
        return self.vkauth

    def VKauthBtn_clicked(self):
        self.vkdialog.show()
        self.vkdialog.load()

    def GauthBtn_clicked(self):
        temp = QFileDialog.getOpenFileName(self, None, "", "JSON (*.json)")
        GauthFile = path.basename(temp[0])
        if GauthFile:
            print(f"Выбран {GauthFile}")
            self.GauthTest(GauthFile)

    def GauthTest(self, GauthFile):
        self.client = google_export.login(GauthFile)
        if self.client == -1:
            self.GauthLabel.setText("Файл аутентификации Google не принят")
            self.GauthIco.setPixmap(QtGui.QPixmap("ico/question.png"))
            self.googleCheck.setEnabled(False)
            ErrorMsg(2)
        else:
            self.GauthLabel.setText("Файл аутентификации Google принят")
            self.GauthIco.setPixmap(QtGui.QPixmap("ico/tick.png"))
            self.googleCheck.setEnabled(True)

    def AuthTest(self):
        try:
            with open("vk-auth.json") as f:
                self.vkauth = json.load(f)
            self.VKauthExists = True
            self.vkapi = vktests.login(self.vkauth["TOKEN"])
            self.nums = vktests.starting_info(self.vkapi, self.vkauth["ADMIN_ID"])
            if self.nums['num'] == 0: raise WrongAdmIDEx
            self.auth_UI([0])

        except FileNotFoundError:
            self.VKauthExists = False
            self.auth_UI([1, 0])

        except vk.exceptions.VkAPIError:
            self.auth_UI([1, 1])
            ErrorMsg(0)

        except WrongAdmIDEx:
            self.auth_UI([1, 1])
            ErrorMsg(1)

    def auth_UI(self, mode):
        if mode[0] == 0:
            self.msgsNumLabel.setText(f"Всего сообщений в диалоге — {self.nums['num']}")
            self.VKauthLabel.setText("Файл аутентификации VK принят")
            self.VKauthIco.setPixmap(QtGui.QPixmap("ico/tick.png"))
            self.VKauthBtn.setText("Изменить?")
            self.groupLabel.setText(f"Целевое сообщество — {self.nums['grpname']}")
            self.adminLabel.setText(f"Выбранный администратор — {self.nums['admname']}")
            self.functionBox.setEnabled(True)
        elif mode[0] == 1:
            self.VKauthIco.setPixmap(QtGui.QPixmap("ico/cross.png"))
            self.groupLabel.setText("Целевое сообщество — ?")
            self.adminLabel.setText("Выбранный администратор — ?")
            self.msgsNumLabel.setText("Всего сообщений в диалоге — ?")
            if mode[1] == 0:
                self.VKauthLabel.setText("Файл аутентификации VK не найден")
                self.VKauthBtn.setText("Создать")
            elif mode[1] == 1:
                self.VKauthLabel.setText("Файл аутентификации VK не принят")
                self.VKauthBtn.setText("Изменить")

    def _append_text(self, msg):
        self.consoleOut.moveCursor(QtGui.QTextCursor.End)
        self.consoleOut.insertPlainText(msg)
        # refresh textedit show, refer) https://doc.qt.io/qt-5/qeventloop.html#ProcessEventsFlag-enum
        QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)


# Redirecting stdout/stderr output to QEditLine
# From https://4uwingnet.tistory.com/9
class StdoutRedirect(QObject):
    printOccur = pyqtSignal(str, str, name="print")

    def __init__(self, *param):
        QObject.__init__(self, None)
        self.daemon = True
        self.sysstdout = sys.stdout.write
        self.sysstderr = sys.stderr.write

    def stop(self):
        sys.stdout.write = self.sysstdout
        sys.stderr.write = self.sysstderr

    def start(self):
        sys.stdout.write = self.write
        sys.stderr.write = lambda msg: self.write(msg, color="red")

    def write(self, s, color="black"):
        sys.stdout.flush()
        self.printOccur.emit(s, color)


class GSheets(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        QDialog.__init__(self)
        loadUi('GSheets.ui', self)

    def OKDisable(self):
        self.OKBtn.setEnabled(False)
        if len(self.sheet_name.text()) > 0 and len(self.wsheet_name.text()) > 0:
            self.OKBtn.setEnabled(True)

    def accept(self):
        Window.GSheetsExport(myWindow, self.sheet_name.text(), self.wsheet_name.text())
        self.close()


# Dialog for vk-auth.json file generating
class VKauthWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        QDialog.__init__(self)
        loadUi('VKauthWin.ui', self)

        self.tokenLine.setValidator(QRegExpValidator(QRegExp('([a-z0-9])*')))
        self.adminLine.setValidator(QIntValidator())

    def load(self):
        VKauthExists = Window.VKauthExists_get(myWindow)
        if not VKauthExists:
            self.OKBtn.setEnabled(False)
        else:
            self.tokenLine.setText(Window.vkauth_get(myWindow)["TOKEN"])
            self.adminLine.setText(Window.vkauth_get(myWindow)["ADMIN_ID"])

    def help(self):
        pixmap = QPixmap('help.jpg')
        helpMsg = QMessageBox()
        helpMsg.setWindowTitle("Помощь по аутентификации")
        helpMsg.setIconPixmap(pixmap)
        helpMsg.resize(pixmap.height(), pixmap.width())
        helpMsg.exec_()

    def OKDisable(self):
        self.OKBtn.setEnabled(False)
        if len(self.tokenLine.text()) > 0 and len(self.adminLine.text()) > 0:
            self.OKBtn.setEnabled(True)

    def accept(self):
        auth = {"TOKEN": f"{self.tokenLine.text()}", "ADMIN_ID": f"{self.adminLine.text()}"}
        with open('vk-auth.json', 'w') as outfile:
            json.dump(auth, outfile, indent=4)
        Window.AuthTest(myWindow)
        self.close()


class WrongAdmIDEx(Exception):
    """"Raised when number of messages in dialogue equals 0 | Dialogue not exists"""
    pass


def ErrorMsg(ErrNum):
    msg = QMessageBox()
    msg.setWindowTitle("Ошибка")
    msg.setIcon(QMessageBox.Warning)
    if ErrNum == 0:
        msg.setText("Упс, токен аутентификации VK недействителен.")
    elif ErrNum == 1:
        msg.setText("Упс, введен неправильный ID администратора или диалог пуст.")
    elif ErrNum == 2:
        msg.setText("Упс, проверьте ваш файл аутентификации.")
    msg.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWindow = Window(None)
    myWindow.show()
    myWindow.AuthTest()
    app.exec_()
