import sys
import os
import zlib
import lzma
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox, QTextEdit

def compress_deflate(data):
    return zlib.compress(data)

def decompress_deflate(data):
    return zlib.decompress(data)

def compress_lzma(data):
    return lzma.compress(data)

def decompress_lzma(data):
    return lzma.decompress(data)

def measure_compression(func, data):
    start_time = time.time()
    compressed_data = func(data)
    end_time = time.time()
    duration = end_time - start_time
    size = len(compressed_data)
    return compressed_data, size, duration

def save_compressed_file(data, filename):
    with open(filename, 'wb') as file:
        file.write(data)

class CompressionApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.selected_file_path = ""
        self.compressed_deflate = None
        self.compressed_lzma = None
        self.original_size = 0
        self.file_name = ""
        self.file_ext = ""

    def initUI(self):
        self.setWindowTitle('Compression Comparison')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.open_button = QPushButton('Open File', self)
        self.open_button.clicked.connect(self.open_file)
        layout.addWidget(self.open_button)

        self.file_label = QLabel('No file selected', self)
        layout.addWidget(self.file_label)

        self.compress_button = QPushButton('Compress', self)
        self.compress_button.clicked.connect(self.compress_file)
        layout.addWidget(self.compress_button)

        self.result_text = QTextEdit(self)
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        self.save_button = QPushButton('Save Compressed Files', self)
        self.save_button.clicked.connect(self.save_files)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def open_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)", options=options)
        if file_path:
            self.file_label.setText(f"Selected file: {file_path}")
            self.selected_file_path = file_path

    def compress_file(self):
        if not self.selected_file_path:
            QMessageBox.critical(self, "Error", "No file selected!")
            return
        
        try:
            with open(self.selected_file_path, 'rb') as file:
                data = file.read()
            
            self.original_size = len(data)
            
            self.compressed_deflate, size_deflate, time_deflate = measure_compression(compress_deflate, data)
            self.compressed_lzma, size_lzma, time_lzma = measure_compression(compress_lzma, data)
            
            result = f"Original Size: {self.original_size} bytes\n\n"
            result += f"DEFLATE: Compressed Size = {size_deflate} bytes, Time = {time_deflate:.5f} seconds\n"
            result += f"LZMA: Compressed Size = {size_lzma} bytes, Time = {time_lzma:.5f} seconds"
            self.result_text.setPlainText(result)
            
            self.file_name, self.file_ext = os.path.splitext(os.path.basename(self.selected_file_path))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_files(self):
        if not self.compressed_deflate or not self.compressed_lzma:
            QMessageBox.critical(self, "Error", "No compressed data to save!")
            return
        
        try:
            if not os.path.exists('results'):
                os.makedirs('results')
            
            deflate_path = os.path.join('results', f'compressed_deflate_{self.file_name}{self.file_ext}')
            lzma_path = os.path.join('results', f'compressed_lzma_{self.file_name}{self.file_ext}')
            
            save_compressed_file(self.compressed_deflate, deflate_path)
            save_compressed_file(self.compressed_lzma, lzma_path)
            
            QMessageBox.information(self, "Success", f"Files saved as:\n{deflate_path}\n{lzma_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CompressionApp()
    ex.show()
    sys.exit(app.exec_())
