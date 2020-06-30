import json
import sys
from os import path

import gspread
import vk
from PyQt5 import QtGui
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.uic import loadUi
from oauth2client.service_account import ServiceAccountCredentials

import vktests


class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        QMainWindow.__init__(self)
        loadUi('MainWindow.ui', self)

        self.vkdialog = VKauthWindow()
        self.VKauthExists = False
        self.vkauth = {}
        self.targetQ=""
        self.data = []
        self.nums = {}

        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def SaveBtn_clicked(self):
        print("lol")

    def BtnsDisable(self):
        self.startBtn.setEnabled(False)
        self.saveBtn.setEnabled(False)
        if len(self.targetQLine.text()) > 0:
            self.targetQ = self.targetQLine.text()
            self.startBtn.setEnabled(True)
        if self.txtCheck.checkState() or self.csvCheck.checkState() or self.googleCheck.checkState():
            self.saveBtn.setEnabled(True)

    def StartBtn_clicked(self):
        self.data = []
        print(self.targetQ)
        self.data = vktests.all_for_msgs(self.vkapi, self.data, self.targetQ, self.vkauth["ADMIN_ID"])
        if len(self.data)==0:
            print("По запросу не найдено результатов")
            self.outputBox.setEnabled(False)
        else:
            self.outputBox.setEnabled(True)


    def VKauthExists_get(self):
        return self.VKauthExists

    def vkauth_get(self):
        return self.vkauth

    def VKauthBtn_clicked(self):
        print("VKauthBtn")
        self.vkdialog.show()
        self.vkdialog.load()

    def GauthBtn_clicked(self):
        print("GauthBtn")
        temp = QFileDialog.getOpenFileName(self, None, "", "JSON (*.json)")
        GauthFile = path.basename(temp[0])
        if GauthFile:
            print(GauthFile)
            self.GauthTest(GauthFile)

    def GauthTest(self, GauthFile):
        scope = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(GauthFile, scope)
            client = gspread.authorize(creds)
            self.GauthLabel.setText("Файл аутентификации Google принят")
            self.GauthIco.setPixmap(QtGui.QPixmap("ico/tick.png"))
            self.googleCheck.setEnabled(True)
        except (Exception):
            self.GauthLabel.setText("Файл аутентификации Google не принят")
            self.GauthIco.setPixmap(QtGui.QPixmap("ico/question.png"))
            self.googleCheck.setEnabled(False)
            ErrorMsg(2)

    def AuthTest(self):
        global f
        try:
            with open("vk-auth.json") as f:
                self.vkauth = json.load(f)
            self.VKauthExists = True
            self.vkapi = vktests.login(self.vkauth["TOKEN"])
            self.nums = vktests.starting_info(self.vkapi, self.vkauth["ADMIN_ID"])
            if self.nums['num'] == 0: raise WrongAdmIDEx
            self.auth_UI([0])

        except IOError:
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
        if VKauthExists == False:
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
