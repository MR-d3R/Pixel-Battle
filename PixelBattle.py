import pickle, sys
import socket
from threading import Thread, Lock
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QGridLayout


class MyWindow(QMainWindow, QWidget):
    signal = pyqtSignal(str)
    colorChanged = pyqtSignal(object)

    def __init__(
            self,
            sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            address=("26.222.82.150", 5361),
            BUFFER_SIZE=4096,
            lock=Lock(),
    ):
        super().__init__()
        self.sock = sock
        self.address = address
        self.BUFFER_SIZE = BUFFER_SIZE
        self.lock = lock
        self.stop_call = False
        self._color = None
        self.DURATION_INT = 10
        self.time_left_int = self.DURATION_INT
        self.color_picker_locked = False

        self.run()

    def run(self):
        self.setWindowTitle('Pixel Battle')
        layout = QGridLayout()
        size = 60
        self.btn_matrix = [[None] * size for _ in range(size)]

        # Creating elements on layout
        for x in range(size):
            for y in range(size):
                btn = QPushButton(self)
                layout.addWidget(btn, x, y)
                btn.setFixedSize(15, 15)

                btn.clicked.connect(
                    lambda state, X=x, Y=y: self.handler_btn(X, Y))
                self.btn_matrix[x][y] = btn

        self.time_passed_qll = QtWidgets.QLabel(
            f"Секунд до следующего пикселя: {str(self.time_left_int)}")
        layout.addWidget(self.time_passed_qll, size, 0, size // 2, size)

        layout.setSpacing(0)

        # self.signal.connect(self.new_message_from_server)

        self.setFixedSize(901, 950)

        widget = QWidget()
        widget.setLayout(layout)
        widget.setStyleSheet("background-color : rgb(0, 0, 0);")
        self.setCentralWidget(widget)

        # self.signal.emit('Connecting...')
        self.sock.connect(self.address)
        # self.signal.emit(f"Connected to {self.address}\n")

        self.name = self.sock.getsockname()
        # self.signal.emit(f"Your name is {self.name}\n")

        receive_msg = Thread(target=self.recv_msg, daemon=True)
        receive_msg.start()

        # self.send_data()

        self.show()

        # self.stop_call = True
        # receive_msg.join()

    @pyqtSlot(str)
    def new_message_from_server(self, text: str):
        self.text_output.append(text)
        self.text_output.append('\n')

    def handler_sumbit(self):
        # show
        msg = self.text_input.text()
        message = {
            "type": "text",
            "data": f"{msg}",
            "optional": "",
        }
        self.text_input.clear()
        #send
        self.sock.send(pickle.dumps(message))
        # show on GUI
        # self.text_output.append(msg)
        # self.text_output.append('\n')

    def handler_btn(self, x: int, y: int):
        if not self.color_picker_locked:

            dlg = QtWidgets.QColorDialog(self)
            if self._color:
                dlg.setCurrentColor(QtGui.QColor(self._color))

            if dlg.exec():
                self.setColor(dlg.currentColor().name(), x, y)

            self.color_picker_locked = True
            self.my_qtimer = QtCore.QTimer(self)
            self.my_qtimer.timeout.connect(self.timer_timeout)
            self.my_qtimer.start(1000)

        else:
            return False

    def timer_timeout(self):
        self.time_left_int -= 1

        if self.time_left_int == 0:
            self.color_picker_locked = False
            self.time_left_int = self.DURATION_INT
            self.my_qtimer.stop()

        self.update_timer()

    def update_timer(self):
        self.time_passed_qll.setText(
            f"Секунд до следующего пикселя: {str(self.time_left_int)}")

    def setColor(self, color, x, y):
        # If the color is different from the current color,
        # emit the colorChanged signal and set the new color.
        if color != self._color:
            self._color = color
            self.colorChanged.emit(color)

        # If a color is selected, set the style sheet of the corresponding
        # button to the selected color and send a message to the server.
        if self._color:
            # if self.btn_matrix[x][y] != None:
            self.btn_matrix[x][y].setStyleSheet("background-color: %s;" %
                                                self._color)

            # Create a list containing the selected
            # color and the coordinates of the button.
            preMessage = [self._color, x, y]
            # Convert the list to a byte string using pickle.
            message = pickle.dumps(preMessage)
            # Send the message to the server.
            self.sock.send(message)

            # Extract the RGB values from the selected color and check
            # if the luminance is greater than 60. If so, set the color.
            # Otherwise, set the color to white.
            _colorValue = self._color.lstrip('#')
            r, g, b = (int(_colorValue[i:i + 2], 16) for i in (0, 2, 4))
            if r > 60 or g > 60 or b > 60:
                self.time_passed_qll.setStyleSheet(
                    "font-size: 30px; color: %s;" % self._color)
            else:
                self.time_passed_qll.setStyleSheet(
                    "font-size: 30px; color: white;")

        # If no color is selected, clear the style sheet of the corresponding button.
        else:
            self.time_left_int = 0
            self.color_picker_locked = False
            self.btn_matrix[x][y].setStyleSheet("")

    def recv_msg(self):
        try:
            while not self.stop_call:

                res = self.sock.recv(self.BUFFER_SIZE)
                try:
                    res = pickle.loads(res)

                    # Loop through the coordinates in the message and
                    # set the style sheet of the corresponding button
                    # to the corresponding color.
                    if res[0] == "matrix":
                        for x in range(len(res)):
                            for y in range(len(res[x])):
                                if res[1][x][y] is not None:
                                    self.btn_matrix[x][y].setStyleSheet(
                                        "background-color: %s;" % res[1][x][y])
                                else:
                                    self.btn_matrix[x][y].setStyleSheet("")

                    elif res[0] == "button":
                        x, y, color = res[1], res[2], res[3]
                        self.btn_matrix[x][y].setStyleSheet(
                            "background-color: %s;" % color)

                except (ConnectionResetError):
                    break

        except (ConnectionResetError):
            return

    def keyPressEvent(self, keyEvent):
        # print(keyEvent.key())      # Used for debugging purposes
        if keyEvent.key() == 16777216:  # 'Escape' key pressed
            sys.exit()


if __name__ == '__main__':
    # client = Client()
    # client.run()
    app = QApplication([])
    window = MyWindow()
    app.exec()
