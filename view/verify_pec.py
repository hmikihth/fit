# !/usr/bin/env python3
# -*- coding:utf-8 -*-
######
# -----
# Copyright (c) 2023 FIT-Project
# SPDX-License-Identifier: GPL-3.0-only
# -----
######  
import os
import subprocess

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog

from view.error import Error as ErrorView
from view.menu_bar import MenuBar as MenuBarView

from controller.verify_pec.verify_pec import verifyPec as verifyPecController
from controller.configurations.tabs.network.networkcheck import NetworkControllerCheck

from common.constants.view import verify_pec, general, verify_pdf_timestamp
from common.utility import get_platform, get_ntp_date_and_time



class VerifyPec(QtWidgets.QMainWindow):
    stop_signal = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(VerifyPec, self).__init__(*args, **kwargs)
        self.acquisition_directory = None

    def init(self, case_info, wizard, options=None):
        self.__init__()
        self.wizard = wizard
        self.width = 600
        self.height = 230
        self.setFixedSize(self.width, self.height)
        self.case_info = case_info

        self.setWindowIcon(QtGui.QIcon(os.path.join('assets/svg/', 'FIT.svg')))
        self.setObjectName("verify_pec_window")

        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.centralwidget.setStyleSheet("QWidget {background-color: rgb(255, 255, 255);}")
        self.setCentralWidget(self.centralwidget)

        #### - START MENU BAR - #####
        # Uncomment to disable native menubar on Mac
        self.menuBar().setNativeMenuBar(False)

        #This bar is common on all main window
        self.menu_bar = MenuBarView(self, self.case_info)

        #Add default menu on menu bar
        self.menu_bar.add_default_actions()
        self.setMenuBar(self.menu_bar)
        #### - END MENUBAR - #####

        self.eml_group_box = QtWidgets.QGroupBox(self.centralwidget)
        self.eml_group_box.setEnabled(True)
        self.eml_group_box.setGeometry(QtCore.QRect(50, 20, 500, 160))
        self.eml_group_box.setObjectName("eml_group_box")

        # EML
        self.input_eml = QtWidgets.QLineEdit(self.centralwidget)
        self.input_eml.setGeometry(QtCore.QRect(160, 60, 260, 20))
        self.input_eml.setObjectName("input_eml")
        self.input_eml.setEnabled(False)
        self.input_eml_button = QtWidgets.QPushButton(self.centralwidget)
        self.input_eml_button.setGeometry(QtCore.QRect(450, 60, 75, 20))
        self.input_eml_button.clicked.connect(self.__dialog)

        # EML LABEL
        self.label_eml = QtWidgets.QLabel(self.centralwidget)
        self.label_eml.setGeometry(QtCore.QRect(80, 60, 50, 20))
        self.label_eml.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.label_eml.setObjectName("label_eml")

        # VERIFICATION BUTTON
        self.verification_button = QtWidgets.QPushButton(self)
        self.verification_button.setGeometry(QtCore.QRect(450, 140, 75, 30))
        self.verification_button.clicked.connect(self.__verify)
        self.verification_button.setObjectName("StartAction")
        self.verification_button.setEnabled(False)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

        # DISABLE SCRAPE BUTTON IF FIELDS ARE EMPTY
        self.input_fields = [self.input_eml]
        for input_field in self.input_fields:
            input_field.textChanged.connect(self.__onTextChanged)

    def retranslateUi(self):
        self.setWindowTitle(general.MAIN_WINDOW_TITLE)
        self.eml_group_box.setTitle(verify_pec.EML_SETTINGS)
        self.label_eml.setText(verify_pec.EML_FILE)
        self.verification_button.setText(general.BUTTON_VERIFY)
        self.input_eml_button.setText(general.BROWSE)

    def __onTextChanged(self):
        all_fields_filled = all(input_field.text() for input_field in self.input_fields)
        self.verification_button.setEnabled(all_fields_filled)

    def __verify(self):
        
        ntp = get_ntp_date_and_time(NetworkControllerCheck().configuration["ntp_server"])
        pec = verifyPecController()
        try:
            pec.verify(self.input_eml.text(), self.case_info, ntp)
            msg = QtWidgets.QMessageBox()
            msg.setWindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint | QtCore.Qt.WindowType.WindowTitleHint)
            msg.setWindowTitle(verify_pdf_timestamp.VERIFICATION_COMPLETED)
            msg.setText(verify_pec.VERIFY_PEC_SUCCESS_MSG)
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            msg.setIcon(QtWidgets.QMessageBox.Icon.Information)
            return_value = msg.exec()
            if return_value == QtWidgets.QMessageBox.StandardButton.Yes:
                path = os.path.dirname(str(self.input_eml.text()))
                platform = get_platform()
                if platform == 'win':
                    os.startfile(os.path.join(path, "report_integrity_pec_verification.pdf"))
                elif platform == 'osx':
                    subprocess.call(["open", os.path.join(path, "report_integrity_pec_verification.pdf")])
                else:  # platform == 'lin' || platform == 'other'
                    subprocess.call(["xdg-open", os.path.join(path, "report_integrity_pec_verification.pdf")])
        except Exception as e:
            error_dlg = ErrorView(QtWidgets.QMessageBox.Icon.Critical,
                                    verify_pec.VERIFY_PEC_FAIL,
                                    verify_pec.VERIFY_PEC_FAIL_MGS,
                                    str(e))
            error_dlg.exec()


    def __dialog(self):

        file, check = QFileDialog.getOpenFileName(None, verify_pec.OPEN_EML_FILE, 
                                                    self.__get_acquisition_directory(), verify_pec.EML_FILES)
        if check:
            self.input_eml.setText(file)


    def __get_acquisition_directory(self):
        if not self.acquisition_directory:
            configuration_general = self.menu_bar.configuration_view.get_tab_from_name("configuration_general")
            open_folder = os.path.expanduser(
                os.path.join(configuration_general.configuration['cases_folder_path'], self.case_info['name']))
            return open_folder
        else:
            return self.acquisition_directory
        

    def __back_to_wizard(self):
        self.deleteLater()
        self.wizard.reload_case_info()
        self.wizard.show()
    
    def closeEvent(self, event):
        event.ignore()
        self.__back_to_wizard()
