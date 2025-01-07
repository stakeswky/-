import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QTextEdit, QFileDialog,
                            QTabWidget, QGroupBox, QGridLayout,
                            QStyle, QComboBox, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from datetime import datetime
from scraper import GoogleMapsScraper
from data_manager import DataManager
import time

class ScraperThread(QThread):
    progress_updated = pyqtSignal(int)
    log_updated = pyqtSignal(str)
    
    def __init__(self, country, business_type, target_count):
        super().__init__()
        self.country = country
        self.business_type = business_type
        self.target_count = target_count
        self.scraper = GoogleMapsScraper()
        self.is_running = False
        self.is_paused = False

    def run(self):
        self.is_running = True
        try:
            self.scraper.scrape(
                self.business_type,
                self.country,
                self.target_count,
                self.progress_updated.emit,
                self.log_updated.emit
            )
        except Exception as e:
            self.log_updated.emit(f"运行错误: {str(e)}")
        finally:
            self.is_running = False

    def pause(self):
        self.scraper.is_paused = True
        self.is_paused = True
        self.log_updated.emit("爬虫已暂停")

    def resume(self):
        self.scraper.is_paused = False
        self.is_paused = False
        self.log_updated.emit("爬虫继续运行")

    def stop(self):
        self.scraper.is_running = False
        self.is_running = False
        self.log_updated.emit("爬虫已停止")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("外贸获客助手")
        self.setMinimumSize(1000, 800)
        self.scraper_thread = None
        self.setup_ui()

    def setup_ui(self):
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 创建选项卡
        tabs = QTabWidget()
        search_tab = QWidget()
        settings_tab = QWidget()
        data_tab = DataManager(self)  # 使用新的DataManager类
        
        tabs.addTab(search_tab, "搜索")
        tabs.addTab(settings_tab, "设置")
        tabs.addTab(data_tab, "数据管理")
        
        # 设置搜索选项卡
        search_layout = QVBoxLayout(search_tab)
        
        # 搜索条件组
        search_group = QGroupBox("搜索条件")
        search_group_layout = QGridLayout()
        
        # 基本搜索条件
        search_group_layout.addWidget(QLabel("国家:"), 0, 0)
        self.country_input = QLineEdit()
        self.country_input.setPlaceholderText("例如: China, USA, Japan")
        search_group_layout.addWidget(self.country_input, 0, 1)
        
        search_group_layout.addWidget(QLabel("商户行业:"), 0, 2)
        self.business_input = QLineEdit()
        self.business_input.setPlaceholderText("例如: restaurant, hotel")
        search_group_layout.addWidget(self.business_input, 0, 3)
        
        search_group_layout.addWidget(QLabel("目标数量:"), 1, 0)
        self.count_input = QLineEdit()
        self.count_input.setPlaceholderText("请输入数字")
        search_group_layout.addWidget(self.count_input, 1, 1)
        
        search_group.setLayout(search_group_layout)
        search_layout.addWidget(search_group)
        
        # 控制按钮组
        button_group = QGroupBox("操作")
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.pause_button = QPushButton("暂停")
        self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        self.stop_button = QPushButton("停止")
        self.stop_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)
        button_group.setLayout(button_layout)
        search_layout.addWidget(button_group)
        
        # 进度显示组
        progress_group = QGroupBox("进度")
        progress_layout = QVBoxLayout()
        
        # 进度条
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        # 状态显示
        self.status_label = QLabel("就绪")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        search_layout.addWidget(progress_group)
        
        # 日志组
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        search_layout.addWidget(log_group)
        
        # 设置选项卡
        settings_layout = QVBoxLayout(settings_tab)
        
        # 保存设置组
        save_group = QGroupBox("保存设置")
        save_layout = QGridLayout()
        
        save_layout.addWidget(QLabel("保存路径:"), 0, 0)
        self.save_path_input = QLineEdit()
        save_layout.addWidget(self.save_path_input, 0, 1)
        
        self.browse_button = QPushButton("浏览...")
        save_layout.addWidget(self.browse_button, 0, 2)
        
        save_layout.addWidget(QLabel("保存格式:"), 1, 0)
        self.save_format = QComboBox()
        self.save_format.addItems(['CSV', 'Excel', 'JSON'])
        save_layout.addWidget(self.save_format, 1, 1)
        
        save_group.setLayout(save_layout)
        settings_layout.addWidget(save_group)
        
        # 代理设置组
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QGridLayout()
        
        self.use_proxy = QCheckBox("使用代理")
        proxy_layout.addWidget(self.use_proxy, 0, 0)
        
        proxy_layout.addWidget(QLabel("代理地址:"), 1, 0)
        self.proxy_host = QLineEdit()
        self.proxy_host.setEnabled(False)
        proxy_layout.addWidget(self.proxy_host, 1, 1)
        
        proxy_layout.addWidget(QLabel("代理端口:"), 2, 0)
        self.proxy_port = QLineEdit()
        self.proxy_port.setEnabled(False)
        proxy_layout.addWidget(self.proxy_port, 2, 1)
        
        proxy_group.setLayout(proxy_layout)
        settings_layout.addWidget(proxy_group)
        
        # 添加选项卡到主布局
        layout.addWidget(tabs)
        
        # 连接信号
        self.start_button.clicked.connect(self.start_scraping)
        self.pause_button.clicked.connect(self.pause_resume_scraping)
        self.stop_button.clicked.connect(self.stop_scraping)
        self.browse_button.clicked.connect(self.browse_save_path)
        self.use_proxy.toggled.connect(self.toggle_proxy_inputs)

    def browse_save_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存路径")
        if path:
            self.save_path_input.setText(path)
            
    def toggle_proxy_inputs(self, checked):
        self.proxy_host.setEnabled(checked)
        self.proxy_port.setEnabled(checked)

    def start_scraping(self):
        try:
            country = self.country_input.text().strip()
            business_type = self.business_input.text().strip()
            target_count = self.count_input.text().strip()

            if not all([country, business_type, target_count]):
                self.log_text.append("错误：请填写所有必要信息")
                return

            try:
                target_count = int(target_count)
                if target_count <= 0:
                    raise ValueError("目标数量必须大于0")
            except ValueError as e:
                self.log_text.append(f"错误：{str(e)}")
                return

            if self.scraper_thread and self.scraper_thread.isRunning():
                self.log_text.append("错误：爬虫正在运行中")
                return

            # 创建输出目录
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            self.scraper_thread = ScraperThread(country, business_type, target_count)
            self.scraper_thread.progress_updated.connect(self.update_progress)
            self.scraper_thread.log_updated.connect(self.update_log)
            self.scraper_thread.finished.connect(self.on_scraping_finished)
            self.scraper_thread.start()

            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            
        except Exception as e:
            self.log_text.append(f"启动错误：{str(e)}")

    def pause_resume_scraping(self):
        if not self.scraper_thread:
            return

        if self.scraper_thread.is_paused:
            self.scraper_thread.resume()
            self.pause_button.setText("暂停")
        else:
            self.scraper_thread.pause()
            self.pause_button.setText("继续")

    def stop_scraping(self):
        if self.scraper_thread and self.scraper_thread.isRunning():
            self.scraper_thread.stop()

    def on_scraping_finished(self):
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.pause_button.setText("暂停")
        # 自动刷新数据显示
        data_tab = self.findChild(DataManager)
        if data_tab:
            data_tab.refresh_data_view()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_log(self, message):
        self.log_text.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
