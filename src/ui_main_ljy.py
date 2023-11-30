# -*- coding: utf-8 -*-
"""
AFCOM - Serial Communication GUI Program
Cannot be used directly, it is a part of main.py
"""

__author__ = 'Mehmet Cagri Aksoy - github.com/mcagriaksoy'
__annotations__ = 'AFCOM - Serial Communication GUI Program'

# IMPORTS
import sys
import glob
import os
import time
import datetime as dt
import matplotlib.pyplot as plt

from PyQt6.QtGui import QPixmap

# Runtime Type Checking
PROGRAM_TYPE_DEBUG = 1
PROGRAM_TYPE_RELEASE = 0

try:
    import serial
    import serial.tools.list_ports
    from serial import SerialException
    from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
    from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox

    if (PROGRAM_TYPE_DEBUG):
        from PyQt6.uic import loadUi
    else: # PROGRAM_TYPE_RELEASE
        from ui_config import Ui_main_window
except ImportError as e:
    print("Import Error! Please install the required libraries: " + str(e))
    sys.exit(1)

# GLOBAL VARIABLES
# SERIAL_INFO = serial.Serial()
PORTS = []

def get_serial_port():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
            print(port)
        except (OSError, serial.SerialException):
            pass
    return result

# MULTI-THREADING
class Worker(QThread):
    """ Worker Thread """
    finished = pyqtSignal()
    serial_data = pyqtSignal(object)

    @pyqtSlot()
    def __init__(self,SERIAL_INFO):
        super(Worker, self).__init__()
        self.working = True
        self.ser = SERIAL_INFO
    
    def run(self):
        """ Read data from serial port """
        while self.working:
            try:
                # print("ser"+str(ser.is_open))
                # char = ser.read()
                # h = char.hex()
                # # h = char.decode()
                # print(h)
                # self.sleep(1)
                h = self.ser.readline()
                # h=ser.read_until(expected='\n') 	#读取一帧数据 ，读到\n为止。 
                                                    #你也可以read_line啥的，因为发送过来的一帧数据可能太长，会读取不完整，所以一条数据读到\n这里正好。
                h.decode()	#很多人会在这里报错，或者得到的解析数据不是自己想要的结果，
			                #是因为比特率设置的频率小于硬件设备的比特率，你可以随便设置一个很大的数字即可成功
                self.serial_data.emit(h)
                
                # QThread.sleep(1)
            except SerialException:
                # Emit last error message before die!
                self.serial_data.emit(b"ERROR_SERIAL_EXCEPTION")
                self.working = False
                self.finished.emit()

class MainWindow(QMainWindow):
    """ Main Window """
    def __init__(self):
        """ Initialize Main Window """
        QMainWindow.__init__(self)

        self.PORTS = get_serial_port()
        self.SERIAL_INFO = serial.Serial()
        self.thread = None
        self.worker = None
        self.list_freq = []
        self.list_x = []
        self.list_y = []
        # self.start_button.clicked.connect(self.start_loop)
        # self.comboBox_3.addItems(PORTS)
    def getPorts(self):
        return self.PORTS
    def print_message_on_screen(self, text):
        """ Print the message on the screen """
        msg = QMessageBox()
        msg.setWindowTitle("Warning!")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(text)
        msg.exec()

    def establish_serial_communication(self):
        """ Establish serial communication """
        port = self.comboBox_3.currentText()
        baudrate = self.comboBox_1.currentText()
        timeout = self.comboBox.currentText()
        length = self.comboBox_2.currentText()
        parity = self.comboBox_4.currentText()
        stopbits = self.comboBox_5.currentText()
        self.SERIAL_INFO = serial.Serial(port=str(port),
                                    baudrate=int(baudrate, base=10),
                                    timeout=float(timeout),
                                    bytesize=int(length, base=10),
                                    parity = parity[0], #get first character
                                    stopbits = float(stopbits)
                                    )
        # SERIAL_INFO = serial.Serial('COM5', 9600,timeout=0.5)
        
        

    def start_loop(self):
        """ Start the loop """
        try:
            self.establish_serial_communication()
        except SerialException:
            self.print_message_on_screen(
                "Exception occured while trying establish serial communication!")

        try:
            self.worker = Worker(self.SERIAL_INFO)   # a new worker to perform those tasks
            # self.thread = QThread()  # a new thread to run our background tasks in
            # move the worker into the thread, do this first before connecting the signals
            # self.worker.moveToThread(self.thread)
            # begin our worker object's loop when the thread starts running
            self.worker.serial_data.connect(self.read_data_from_thread)
            self.worker.serial_data.connect(self.plot_picture_from_thread)

            
            # stop the loop on the stop button click
            self.end_button.clicked.connect(self.stop_loop)
            # tell the thread it's time to stop running
            self.worker.finished.connect(self.worker.quit)
            # have worker mark itself for deletion
            self.worker.finished.connect(self.worker.deleteLater)
            # have thread mark itself for deletion
            # self.thread.finished.connect(self.thread.deleteLater)
            # 
            # 
            # 
            # .connect(self.worker.work(self.SERIAL_INFO))
            self.worker.start()
            
        except RuntimeError:
            self.print_message_on_screen("Exception in Worker Thread!")

    def stop_loop(self):
        """ Stop the loop """
        self.worker.working = False
        self.textEdit.setText('Stopped!')

    def read_data_from_thread(self, serial_data):
        """ Write the result to the text edit box"""
        # self.textEdit_3.append("{}".format(i))
        if b"ERROR_SERIAL_EXCEPTION" in serial_data:
            self.print_message_on_screen("Serial Exception! Please check the serial port")
            self.label_5.setText("NOT CONNECTED!")
            self.label_5.setStyleSheet('color: red')
        else:
            self.comboBox.setEnabled(False)
            self.comboBox_1.setEnabled(False)
            self.comboBox_2.setEnabled(False)
            self.comboBox_3.setEnabled(False)
            self.comboBox_4.setEnabled(False)
            self.comboBox_5.setEnabled(False)
            self.save_button.setEnabled(False)
            self.start_button.setEnabled(False)

            self.textEdit.setText('Data Gathering...')
            self.label_5.setText("CONNECTED!")
            self.label_5.setStyleSheet('color: green')
            str1 = str(serial_data, encoding = "utf-8")
            self.textEdit_3.insertPlainText("{}".format(str1))

    def plot_picture_from_thread(self, serial_data):
        # self.label.setText('Picture Gathering...')
        a = str(serial_data, encoding = "utf-8")
        index = a.find("Freq")
        if index != -1:
            index_0 = a.index("(",6)
            freq = float(a[6:index_0-1])
            self.list_freq.append(freq)
            index_start = a.index("=")
            index_mid = a.index(",",index_start+3)
            x = float(a[index_start+3:index_mid-1])
            self.list_x.append(x)
            index_end = a.index(",", index_mid+2)
            y = float(a[index_mid+2:index_end-1])
            self.list_y.append(y)
        if len(self.list_x) > 150:
            print("get in")
            # self.imagelabel.setText('EIS检测曲线')
            # self.imagelabel.setPixmap(QPixmap(""))
            fig, ax = plt.subplots(figsize=(8, 8))
            scatter1 = ax.scatter(self.list_x, self.list_y, c='purple', alpha=0.5)
            # plt.legend()
            plt.xlabel("real")
            plt.ylabel("image")
            save_time = dt.datetime.now().strftime('%Y%m%d-%H%M%S')
            result_img_path = '../result_img/{}.jpg'.format(save_time)
            plt.savefig(result_img_path) 
            self.imagelabel.setScaledContents(True)       
            self.imagelabel.setPixmap(QPixmap(result_img_path))
            self.list_freq.clear()
            self.list_x.clear()
            self.list_y.clear()
    # Save the settings
    def on_save_button_clicked(self):
        """ Save the settings """
        if self.x != 0:
            self.textEdit.setText('Settings Saved!')
        else:
            self.textEdit.setText('Please enter port and speed!')

    def on_save_txt_button_clicked(self):
        """ Save the values to the TXT file"""
        with open('Output.txt', 'w', encoding='utf-8') as f:
            my_text = self.textEdit_3.toPlainText()
            f.write(my_text)
            f.close()

    def on_end_button_clicked(self):
        """ Stop the process """
        self.textEdit.setText('Stopped!')
        self.comboBox.setEnabled(True)
        self.comboBox_1.setEnabled(True)
        self.comboBox_2.setEnabled(True)
        self.comboBox_3.setEnabled(True)
        self.comboBox_4.setEnabled(True)
        self.comboBox_5.setEnabled(True)
        self.save_button.setEnabled(True)
        self.start_button.setEnabled(True)

    def on_send_data_button_clicked(self):
        """ Send data to serial port """
        mytext = self.textEdit_2.toPlainText()
        print(mytext.encode())
        self.SERIAL_INFO.write(mytext.encode())

def start_ui_design():
    """ Start the UI Design """
    app = QApplication(sys.argv)
    window_object = MainWindow()

    if PROGRAM_TYPE_RELEASE:
        ui = Ui_main_window()
        ui.setupUi(window_object)
        # ui.start_button.clicked.connect(window_object.start_loop())
        # ui.comboBox_3.addItems(window_object.getPorts())
    elif PROGRAM_TYPE_DEBUG:
        file_path = os.path.join("../ui/main_window.ui")
        if not os.path.exists(file_path):
            print("UI File Not Found!")
            sys.exit(1)
        # file_path = 
        loadUi(file_path, window_object)

    
    window_object.start_button.clicked.connect(window_object.start_loop)
    window_object.comboBox_3.addItems(window_object.getPorts())
    window_object.show()
    # self.comboBox_3.addItems(PORTS)
    # window_object.start_loop()
    sys.exit(app.exec())