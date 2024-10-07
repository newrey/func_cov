import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QTextEdit, QCheckBox, QLineEdit, QFileDialog,
    QTabWidget, QWidget, QGroupBox, QGridLayout, QSizePolicy, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDrag
import configparser
import argparse
import os
import logging

# 初始化日志
logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

original_prefix_entry_default = "harness.U_DUT.XXX.SUB"
target_prefix_entry_default = "harness.U_DUT.HARDENED_TOP.XXX.SUB"

# 添加在类顶部
SIGNAL_DRAG_MODE = '信号拖拽模式'
WAVEFORM_MODE = '波形模式'

class SignalDragLabel(QLabel):
    def __init__(self, title, parent=None, is_drag_out=False):
        super().__init__(title, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: lightgray; 
                border: 2px dashed black;
                font-size: 14px;
                padding: 10px;
                width: 200px;
            }
            QLabel:hover {
                background-color: #d3d3d3;
            }
        """)
        self.setAcceptDrops(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.is_drag_out = is_drag_out
        self.drag_text = ""  # 初始化拖动文本

    def dragEnterEvent(self, event: QDragEnterEvent):
        if self.is_drag_out:
            # 拒绝拖入操作，并显示禁止光标
            event.ignore()
        elif event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if not self.is_drag_out:
            text = event.mimeData().text()
            self.parent().handle_drop(text, self)
            event.acceptProposedAction()
        else:
            # 拒绝拖入操作
            event.ignore()

    def mousePressEvent(self, event):
        if self.is_drag_out and self.drag_text:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.drag_text)
            drag.setMimeData(mime_data)

            # 开始拖动操作
            drop_action = drag.exec_(Qt.CopyAction | Qt.MoveAction)

    def set_drag_text(self, text):
        if self.is_drag_out:
            self.drag_text = text
        # self.setText(text)

class SignalDragMode(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.processed_result = ""  # 初始化处理结果
        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)

        instruction_label = QLabel(f"{SIGNAL_DRAG_MODE}：如果前后仿波形已经打开，将前仿信号拖入，经转换后再拖入后仿波形")
        instruction_label.setWordWrap(True)
        # 统一样式并增加 padding
        instruction_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                padding: 10px;
            }
        """)
        layout.addWidget(instruction_label)

        drag_layout = QHBoxLayout()

        # 拖入区域
        self.drag_in_label = SignalDragLabel("将前仿verdi中的信号拖入这里", self, is_drag_out=False)
        self.drag_in_label.setToolTip("将前仿verdi中的信号拖入这里")
        drag_layout.addWidget(self.drag_in_label)

        # 拖出区域
        self.drag_out_label = SignalDragLabel("将此处信号拖出到后仿verdi中", self, is_drag_out=True)
        self.drag_out_label.setToolTip("将此处信号拖出到后仿verdi中")
        drag_layout.addWidget(self.drag_out_label)

        layout.addLayout(drag_layout)

    def handle_drop(self, text, label):
        if label == self.drag_in_label:
            pre_signal = text
            pre_tail = ""
            if len(pre_signal) > 300:  # 如果输入信号超过300字符，则截断并添加省略号
                pre_tail = " ..."
            self.drag_in_label.setText(f"输入：\n{pre_signal[:300]}{pre_tail}")

            post_signal = self.process_signal(text)
            post_head = ""
            post_tail = ""
            if len(post_signal) > 300:  # 如果输出信号超过300字符，则截断并添加省略号
                post_tail = " ..."
            self.drag_out_label.setText(f"输出：\n{post_signal[:300]}{post_tail}")
        elif label == self.drag_out_label:
            # 这里可以添加拖出信号的处理逻辑
            pass

    def process_signal(self, signal):
        # 添加实际的信号处理逻辑
        # 这里只是简单地返回原始信号，可以根据需求进行修改
        post_signal = 'post ===> ' + signal
        self.drag_out_label.set_drag_text(post_signal)
        return post_signal

class WaveformMode(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        layout = QVBoxLayout(self)
        instruction_label = QLabel(f"{WAVEFORM_MODE}: 配置参数并打开波形")
        instruction_label.setWordWrap(True)
        # 统一样式并增加 padding
        instruction_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                padding: 10px;
            }
        """)
        layout.addWidget(instruction_label)
 
        config_frame = QGroupBox("参数配置")
        config_layout = QGridLayout(config_frame)
        layout.addWidget(config_frame)

        config_layout.addWidget(QLabel("前仿波形（.fsdb）文件路径:"), 0, 0)
        self.pre_waveform_entry = QLineEdit(self)
        self.pre_waveform_entry.setPlaceholderText("请输入前仿波形文件路径")
        config_layout.addWidget(self.pre_waveform_entry, 0, 1)
        browse_pre_waveform_button = QPushButton("浏览")
        browse_pre_waveform_button.clicked.connect(self.browse_pre_waveform)
        config_layout.addWidget(browse_pre_waveform_button, 0, 2)

        config_layout.addWidget(QLabel("前仿信号（.rc）文件路径:"), 1, 0)
        self.pre_signal_entry = QLineEdit(self)
        self.pre_signal_entry.setPlaceholderText("请输入前仿信号文件路径")
        config_layout.addWidget(self.pre_signal_entry, 1, 1)
        browse_pre_signal_button = QPushButton("浏览")
        browse_pre_signal_button.clicked.connect(self.browse_pre_signal)
        config_layout.addWidget(browse_pre_signal_button, 1, 2)

        config_layout.addWidget(QLabel("后仿波形（.fsdb）文件路径:"), 2, 0)
        self.post_waveform_entry = QLineEdit(self)
        self.post_waveform_entry.setPlaceholderText("请输入后仿波形文件路径")
        config_layout.addWidget(self.post_waveform_entry, 2, 1)
        browse_post_waveform_button = QPushButton("浏览")
        browse_post_waveform_button.clicked.connect(self.browse_post_waveform)
        config_layout.addWidget(browse_post_waveform_button, 2, 2)

        open_waveform_button = QPushButton("打开波形")
        open_waveform_button.clicked.connect(self.open_waveform)
        open_waveform_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(open_waveform_button)

    def browse_pre_waveform(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择前仿波形文件")
        if file_path:
            self.pre_waveform_entry.setText(file_path)

    def browse_pre_signal(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择前仿信号文件")
        if file_path:
            self.pre_signal_entry.setText(file_path)

    def browse_post_waveform(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择后仿波形文件")
        if file_path:
            self.post_waveform_entry.setText(file_path)

    def open_waveform(self):
        logging.info("尝试打开波形")
        pre_waveform = self.pre_waveform_entry.text()
        pre_signal = self.pre_signal_entry.text()
        post_waveform = self.post_waveform_entry.text()

        if not pre_waveform or not pre_signal or not post_waveform:
            QMessageBox.warning(self, "输入错误", "请确保所有文件路径已填写。")
            return

        # 验证文件扩展名
        if not pre_waveform.endswith('.fsdb') or not post_waveform.endswith('.fsdb') or not pre_signal.endswith('.rc'):
            QMessageBox.warning(self, "格式错误", "文件格式不正确。请检查文件扩展名。")
            return

        # 验证文件是否可访问
        for file_path in [pre_waveform, pre_signal, post_waveform]:
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "文件不存在", f"文件不存在或无法访问: {file_path}")
                return

        self.parent.save_config()
        QMessageBox.information(self, "成功", "波形已成功打开。")
        logging.info("波形成功打开")
        # 添加打开波形的逻辑

class MultiModeReceiver(QMainWindow):
    def __init__(self, config_file='config.ini'):
        super().__init__()
        self.setWindowTitle("多功能接收窗口")
        self.setGeometry(100, 100, 800, 390)
        self.config_file = config_file
        self.create_widgets()
        self.load_config()
        # 连接选项卡变化信号
        self.notebook.currentChanged.connect(self.on_tab_changed)
    
    def create_widgets(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.create_mapping_frame(layout)
        self.create_notebook(layout)

    def create_mapping_frame(self, layout):
        mapping_frame = QGroupBox("映射关系配置")
        mapping_layout = QGridLayout(mapping_frame)
        layout.addWidget(mapping_frame)

        mapping_layout.addWidget(QLabel("映射文件（.tcl）路径:"), 0, 0)
        self.path_entry = QLineEdit(self)
        self.path_entry.setPlaceholderText("请输入tcl文件夹或文件路径，多个文件用;隔开")
        mapping_layout.addWidget(self.path_entry, 0, 1, 1, 3)
        browse_path_button = QPushButton("浏览文件夹")
        browse_path_button.clicked.connect(self.browse_path)
        mapping_layout.addWidget(browse_path_button, 0, 4)
        browse_files_button = QPushButton("浏览文件")
        browse_files_button.clicked.connect(self.browse_files)
        mapping_layout.addWidget(browse_files_button, 0, 5)

        self.prefix_var = QCheckBox("启用 hdl_path 前缀替换")
        self.prefix_var.stateChanged.connect(self.toggle_prefix_entries)
        mapping_layout.addWidget(self.prefix_var, 1, 0, 1, 6)

        mapping_layout.addWidget(QLabel("原始（前仿）前缀:"), 2, 0)
        self.original_prefix_entry = QLineEdit(self)
        self.original_prefix_entry.setPlaceholderText(original_prefix_entry_default)
        self.original_prefix_entry.setDisabled(True)
        mapping_layout.addWidget(self.original_prefix_entry, 2, 1, 1, 5)

        mapping_layout.addWidget(QLabel("目标（后仿）前缀:"), 3, 0)
        self.target_prefix_entry = QLineEdit(self)
        self.target_prefix_entry.setPlaceholderText(target_prefix_entry_default)
        self.target_prefix_entry.setDisabled(True)
        mapping_layout.addWidget(self.target_prefix_entry, 3, 1, 1, 5)

    def toggle_prefix_entries(self):
        state = not self.original_prefix_entry.isEnabled()
        self.original_prefix_entry.setEnabled(state)
        self.target_prefix_entry.setEnabled(state)

    def create_notebook(self, layout):
        self.notebook = QTabWidget(self)
        layout.addWidget(self.notebook)

        self.signal_drag_mode = SignalDragMode(self)
        self.waveform_mode = WaveformMode(self)

        self.notebook.addTab(self.waveform_mode, WAVEFORM_MODE)
        self.notebook.addTab(self.signal_drag_mode, SIGNAL_DRAG_MODE)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if path:
            self.path_entry.setText(path)

    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择文件")
        if files:
            self.path_entry.setText(';'.join(files))

    def load_config(self):
        config = configparser.ConfigParser()
        config.read(self.config_file)
        if 'Settings' in config:
            self.path_entry.setText(config.get('Settings', 'tcl_path', fallback=''))
            self.waveform_mode.pre_waveform_entry.setText(config.get('Settings', 'pre_waveform', fallback=''))
            self.waveform_mode.pre_signal_entry.setText(config.get('Settings', 'pre_signal', fallback=''))
            self.waveform_mode.post_waveform_entry.setText(config.get('Settings', 'post_waveform', fallback=''))
            self.prefix_var.setChecked(config.getboolean('Settings', 'enable_hdl_path_prefix', fallback=False))
            self.original_prefix_entry.setText(config.get('Settings', 'original_prefix', fallback=original_prefix_entry_default))
            self.target_prefix_entry.setText(config.get('Settings', 'target_prefix', fallback=target_prefix_entry_default))
        # self.toggle_prefix_entries()
    
    def save_config(self):
        config = configparser.ConfigParser()
        config['Settings'] = {
            'tcl_path': self.path_entry.text(),
            'pre_waveform': self.waveform_mode.pre_waveform_entry.text(),
            'pre_signal': self.waveform_mode.pre_signal_entry.text(),
            'post_waveform': self.waveform_mode.post_waveform_entry.text(),
            'enable_hdl_path_prefix': self.prefix_var.isChecked(),
            'original_prefix': self.original_prefix_entry.text(),
            'target_prefix': self.target_prefix_entry.text(),
        }
        with open(self.config_file, 'w') as configfile:
            config.write(configfile)
    
    def on_tab_changed(self, index):
        current_tab = self.notebook.tabText(index)
        if current_tab == SIGNAL_DRAG_MODE:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

def main():
    parser = argparse.ArgumentParser(description="多功能接收窗口")
    parser.add_argument('--config', type=str, default='config.ini', help='配置文件路径')
    args = parser.parse_args()

    app = QApplication(sys.argv)
    main_window = MultiModeReceiver(config_file=args.config)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
