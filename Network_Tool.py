import sys
import platform
import subprocess
import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, \
    QTextEdit, QSpinBox, QHBoxLayout
from PySide6.QtCore import Qt, QThread, Signal
import locale


class PingThread(QThread):
    finished = Signal()

    def __init__(self, address, test_count):
        super().__init__()
        self.address = address
        self.test_count = test_count
        self.process = None
        self.running = True  # 控制线程的标志

    def run(self):
        system = platform.system().lower()
        command = f"ping -n {self.test_count} {self.address}" if "windows" in system else f"ping -c {self.test_count} {self.address}"

        log_filename = f"{self.address}_test_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            log_file.write(f"开始测试 {self.address}，测试次数: {self.test_count}\n")
            self.process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            encoding = locale.getpreferredencoding()
            for line in iter(self.process.stdout.readline, b''):
                if not self.running:
                    self.process.terminate()
                    break

                output_decoded = line.decode(encoding, errors="replace")
                log_file.write(output_decoded)
                log_file.flush()

            self.process.stdout.close()
            self.process.wait()

            log_file.write(f"测试结束 {self.address}\n")
        self.finished.emit()

    def stop(self):
        self.running = False


class NetworkStabilityApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Tool By.Gnay")
        self.setGeometry(300, 300, 600, 500)

        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)

        self.address_inputs = []
        self.ping_threads = []
        self.finished_count = 0  # 用于记录已完成的线程数量
        self.init_ui()

        self.setCentralWidget(self.central_widget)

    def init_ui(self):
        self.main_layout.addWidget(QLabel("NUCTECH-IG6000系统 网络测试工具"))

        # 测试次数输入框
        self.test_count_input = QSpinBox(self)
        self.test_count_input.setRange(1, 999)
        self.test_count_input.setValue(10)
        self.test_count_input.setPrefix("测试次数: ")
        self.main_layout.addWidget(self.test_count_input)

        # 添加IP地址输入框的按钮
        add_address_button = QPushButton("添加IP地址", self)
        add_address_button.clicked.connect(self.add_address_input)
        self.main_layout.addWidget(add_address_button)

        # 按钮布局
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("开始测试", self)
        self.start_button.clicked.connect(self.start_test)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("停止测试", self)
        self.stop_button.clicked.connect(self.stop_test)
        button_layout.addWidget(self.stop_button)

        self.main_layout.addLayout(button_layout)  # 将按钮布局添加到主布局

        # 输出显示区域
        self.output_display = QTextEdit(self)
        self.output_display.setReadOnly(True)
        self.main_layout.addWidget(QLabel("测试结果："))
        self.main_layout.addWidget(self.output_display)

        self.add_address_input()  # 添加第一个IP地址输入框

    def add_address_input(self):
        address_layout = QHBoxLayout()

        address_input = QLineEdit(self)
        address_input.setPlaceholderText("输入IP地址或域名")
        address_layout.addWidget(address_input)

        remove_button = QPushButton("删除", self)
        remove_button.clicked.connect(lambda: self.remove_address_input(address_input, address_layout))
        address_layout.addWidget(remove_button)

        self.address_inputs.append(address_input)
        self.main_layout.insertLayout(self.main_layout.count() - 3, address_layout)

    def remove_address_input(self, address_input, address_layout):
        self.address_inputs.remove(address_input)
        for i in reversed(range(address_layout.count())):
            widget = address_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def start_test(self):
        addresses = [address_input.text().strip() for address_input in self.address_inputs if address_input.text().strip()]
        test_count = self.test_count_input.value()
        if not addresses:
            self.output_display.append("请输入至少一个有效的IP地址或域名")
            return

        self.output_display.clear()  # 清空之前的输出
        self.finished_count = 0  # 重置已完成的计数

        for address in addresses:
            self.output_display.append(f"正在测试 {address}...")
            thread = PingThread(address, test_count)
            thread.finished.connect(self.test_finished)
            self.ping_threads.append(thread)
            thread.start()

    def test_finished(self):
        self.finished_count += 1  # 增加已完成的线程计数
        # 检查是否所有线程都完成
        if self.finished_count == len(self.ping_threads):
            self.output_display.append("所有测试结束。")

    def stop_test(self):
        for thread in self.ping_threads:
            thread.stop()  # 使用 stop 方法安全地终止
        self.ping_threads.clear()
        self.output_display.append("所有测试已停止。")

    def closeEvent(self, event):
        """处理关闭事件以安全停止所有线程"""
        self.stop_test()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NetworkStabilityApp()
    window.show()
    sys.exit(app.exec())