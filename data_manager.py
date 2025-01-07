import os
import pandas as pd
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QTableWidget, 
                            QTableWidgetItem, QComboBox, QLineEdit,
                            QFileDialog, QMessageBox,QGroupBox,QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QStyle

class DataManager(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # 保存父窗口引用以访问日志等功能
        self.current_file = None  # 当前加载的文件路径
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 文件选择组
        file_group = QGroupBox("文件操作")
        file_layout = QHBoxLayout()
        
        self.file_combo = QComboBox()
        self.file_combo.setMinimumWidth(300)
        file_layout.addWidget(QLabel("选择文件:"))
        file_layout.addWidget(self.file_combo)
        
        self.load_file_button = QPushButton("加载文件")
        self.load_file_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        file_layout.addWidget(self.load_file_button)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 搜索和筛选组
        search_filter_group = QGroupBox("搜索和筛选")
        search_filter_layout = QGridLayout()
        
        # 搜索框
        search_filter_layout.addWidget(QLabel("搜索:"), 0, 0)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索...")
        self.search_input.textChanged.connect(self.filter_data)
        search_filter_layout.addWidget(self.search_input, 0, 1, 1, 2)
        
        # 筛选选项
        search_filter_layout.addWidget(QLabel("评分筛选:"), 1, 0)
        self.rating_filter = QComboBox()
        self.rating_filter.addItems(['全部', '4.5+', '4.0+', '3.5+', '3.0+'])
        self.rating_filter.currentTextChanged.connect(self.filter_data)
        search_filter_layout.addWidget(self.rating_filter, 1, 1)
        
        search_filter_layout.addWidget(QLabel("字段筛选:"), 1, 2)
        self.field_filter = QComboBox()
        self.field_filter.addItems(['全部字段', '商户名称', '地址', '电话', '评分'])
        search_filter_layout.addWidget(self.field_filter, 1, 3)
        
        search_filter_group.setLayout(search_filter_layout)
        layout.addWidget(search_filter_group)
        
        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setSortingEnabled(True)  # 启用排序功能
        self.data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # 整行选择
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)  # 允许双击编辑
        self.data_table.itemChanged.connect(self.on_item_changed)  # 添加编辑监听
        layout.addWidget(self.data_table)
        
        # 数据操作按钮
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        
        self.save_button = QPushButton("保存更改")
        self.save_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        
        self.export_button = QPushButton("导出")
        self.export_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        
        self.delete_button = QPushButton("删除")
        self.delete_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.delete_button)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        self.refresh_button.clicked.connect(self.refresh_data_view)
        self.save_button.clicked.connect(self.save_changes)
        self.export_button.clicked.connect(self.export_data)
        self.delete_button.clicked.connect(self.delete_data)
        self.load_file_button.clicked.connect(self.load_selected_file)
        
        # 初始化文件列表
        self.update_file_list()
        
    def update_file_list(self):
        """更新文件下拉列表"""
        try:
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            if not os.path.exists(output_dir):
                return
                
            # 获取所有CSV文件
            files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
            if not files:
                return
                
            # 按修改时间排序
            files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
            
            # 更新下拉列表
            self.file_combo.clear()
            self.file_combo.addItems(files)
            
        except Exception as e:
            self.log_message(f"更新文件列表失败：{str(e)}")
            
    def load_selected_file(self):
        """加载选中的文件"""
        try:
            selected_file = self.file_combo.currentText()
            if not selected_file:
                return
                
            output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
            file_path = os.path.join(output_dir, selected_file)
            
            if not os.path.exists(file_path):
                self.log_message("选中的文件不存在")
                return
                
            self.load_data_file(file_path)
            
        except Exception as e:
            self.log_message(f"加载文件失败：{str(e)}")
            
    def load_data_file(self, file_path):
        """加载指定的数据文件"""
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 设置表格列数和列标题
            self.data_table.setColumnCount(len(df.columns))
            self.data_table.setHorizontalHeaderLabels(df.columns)
            
            # 设置表格行数
            self.data_table.setRowCount(len(df))
            
            # 填充数据
            for i in range(len(df)):
                for j in range(len(df.columns)):
                    item = QTableWidgetItem(str(df.iloc[i, j]))
                    # 如果是评分列，设置为数字类型以便正确排序
                    if df.columns[j] == 'rating':
                        try:
                            rating_text = str(df.iloc[i, j])
                            if isinstance(df.iloc[i, j], (int, float)):
                                rating_value = float(df.iloc[i, j])
                            else:
                                rating_value = float(rating_text.split()[0])
                            item.setData(Qt.ItemDataRole.DisplayRole, rating_value)
                        except (ValueError, IndexError):
                            item.setData(Qt.ItemDataRole.DisplayRole, 0.0)
                    self.data_table.setItem(i, j, item)
            
            # 调整列宽
            self.data_table.resizeColumnsToContents()
            
            # 保存当前文件路径
            self.current_file = file_path
            
            # 更新状态
            self.update_status(f"已加载数据文件：{os.path.basename(file_path)}")
            self.log_message(f"成功加载数据文件：{os.path.basename(file_path)}")
            
            # 重置筛选
            self.search_input.clear()
            self.rating_filter.setCurrentText('全部')
            self.field_filter.setCurrentText('全部字段')
            
        except Exception as e:
            self.log_message(f"加载数据失败：{str(e)}")
            
    def on_item_changed(self, item):
        """处理单元格编辑事件"""
        try:
            row = item.row()
            col = item.column()
            new_value = item.text()
            
            # 如果是评分列，验证输入
            if self.data_table.horizontalHeaderItem(col).text() == 'rating':
                try:
                    rating = float(new_value.split()[0])
                    if not (0 <= rating <= 5):
                        raise ValueError("评分必须在0-5之间")
                except ValueError:
                    self.log_message("错误：评分格式无效，请输入0-5之间的数字")
                    # 恢复原值
                    item.setText(self.data_table.item(row, col).text())
                    return
                    
            self.log_message(f"已修改第 {row+1} 行 {col+1} 列的数据")
            
        except Exception as e:
            self.log_message(f"编辑数据时出错：{str(e)}")
            
    def save_changes(self):
        """保存更改到当前文件"""
        try:
            if not self.current_file:
                self.log_message("错误：没有加载的文件")
                return
                
            # 收集表格数据
            data = []
            headers = []
            
            # 获取列标题
            for j in range(self.data_table.columnCount()):
                headers.append(self.data_table.horizontalHeaderItem(j).text())
            
            # 获取数据
            for i in range(self.data_table.rowCount()):
                row_data = []
                for j in range(self.data_table.columnCount()):
                    item = self.data_table.item(i, j)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # 创建DataFrame并保存
            df = pd.DataFrame(data, columns=headers)
            df.to_csv(self.current_file, index=False, encoding='utf-8-sig')
            
            self.log_message(f"更改已保存到文件：{os.path.basename(self.current_file)}")
            
        except Exception as e:
            self.log_message(f"保存更改失败：{str(e)}")
            
    def refresh_data_view(self):
        """刷新数据视图"""
        self.update_file_list()  # 更新文件列表
        
        if self.current_file and os.path.exists(self.current_file):
            self.load_data_file(self.current_file)
        else:
            # 如果没有当前文件，加载最新的文件
            try:
                output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
                if not os.path.exists(output_dir):
                    self.log_message("提示：暂无数据文件")
                    return
                    
                files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
                if not files:
                    self.log_message("提示：暂无数据文件")
                    return
                    
                latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
                self.load_data_file(os.path.join(output_dir, latest_file))
                
            except Exception as e:
                self.log_message(f"刷新数据失败：{str(e)}")
            
    def log_message(self, message):
        """向主窗口发送日志消息"""
        if self.parent and hasattr(self.parent, 'log_text'):
            self.parent.log_text.append(message)
            
    def update_status(self, message):
        """更新主窗口状态栏"""
        if self.parent and hasattr(self.parent, 'status_label'):
            self.parent.status_label.setText(message)
            
    def export_data(self):
        try:
            # 检查是否有数据
            if self.data_table.rowCount() == 0:
                self.log_message("错误：没有可导出的数据")
                return
                
            # 获取保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "导出数据",
                "",
                "CSV 文件 (*.csv);;Excel 文件 (*.xlsx);;JSON 文件 (*.json)"
            )
            
            if not file_path:
                return
                
            # 将表格数据转换为DataFrame
            data = []
            headers = []
            
            # 获取列标题
            for j in range(self.data_table.columnCount()):
                headers.append(self.data_table.horizontalHeaderItem(j).text())
            
            # 获取数据
            for i in range(self.data_table.rowCount()):
                row_data = []
                for j in range(self.data_table.columnCount()):
                    item = self.data_table.item(i, j)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # 创建DataFrame
            df = pd.DataFrame(data, columns=headers)
            
            # 根据文件扩展名选择保存格式
            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            elif file_path.endswith('.json'):
                df.to_json(file_path, orient='records', force_ascii=False)
                
            self.log_message(f"数据已成功导出到：{file_path}")
            
        except Exception as e:
            self.log_message(f"导出数据失败：{str(e)}")
            
    def delete_data(self):
        try:
            # 获取选中的行
            selected_rows = set(item.row() for item in self.data_table.selectedItems())
            
            if not selected_rows:
                self.log_message("请先选择要删除的数据行")
                return
                
            # 从后向前删除选中的行（避免索引变化）
            for row in sorted(selected_rows, reverse=True):
                self.data_table.removeRow(row)
                
            self.log_message(f"已删除 {len(selected_rows)} 行数据")
            
        except Exception as e:
            self.log_message(f"删除数据失败：{str(e)}")
            
    def filter_data(self):
        try:
            # 获取搜索关键词和筛选条件
            search_text = self.search_input.text().lower()
            rating_filter = self.rating_filter.currentText()
            field_filter = self.field_filter.currentText()
            
            # 遍历所有行
            for row in range(self.data_table.rowCount()):
                show_row = True
                
                # 评分筛选
                if rating_filter != '全部':
                    rating_cell = self.data_table.item(row, 3)  # 假设评分在第4列
                    if rating_cell:
                        try:
                            rating = float(rating_cell.text().split()[0])  # 提取评分数字
                            min_rating = float(rating_filter.replace('+', ''))
                            if rating < min_rating:
                                show_row = False
                        except (ValueError, IndexError):
                            show_row = False
                
                # 关键词搜索
                if search_text and show_row:
                    row_matches = False
                    if field_filter == '全部字段':
                        # 搜索所有列
                        for col in range(self.data_table.columnCount()):
                            cell = self.data_table.item(row, col)
                            if cell and search_text in cell.text().lower():
                                row_matches = True
                                break
                    else:
                        # 搜索特定列
                        col_map = {'商户名称': 0, '地址': 1, '电话': 2, '评分': 3}
                        col = col_map.get(field_filter, 0)
                        cell = self.data_table.item(row, col)
                        if cell and search_text in cell.text().lower():
                            row_matches = True
                    
                    show_row = row_matches
                
                # 显示或隐藏行
                self.data_table.setRowHidden(row, not show_row)
                
        except Exception as e:
            self.log_message(f"筛选数据时出错：{str(e)}") 