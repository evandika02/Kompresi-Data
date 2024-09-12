import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QTextEdit, QGroupBox,
    QFormLayout, QRadioButton, QButtonGroup
)
import os
import sqlite3
from collections import Counter
import heapq

def lzw_compress(uncompressed):
    dict_size = 256
    dictionary = {chr(i): i for i in range(dict_size)}
    w = ""
    result = []
    for c in uncompressed:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            result.append(dictionary[w])
            dictionary[wc] = dict_size
            dict_size += 1
            w = c

    if w:
        result.append(dictionary[w])
    return result

def lzw_decompress(compressed):
    dict_size = 256
    dictionary = {i: chr(i) for i in range(dict_size)}
    result = []
    w = chr(compressed[0])
    result.append(w)
    for k in compressed[1:]:
        if k in dictionary:
            entry = dictionary[k]
        elif k == dict_size:
            entry = w + w[0]
        else:
            raise ValueError('Kode terkompresi salah: %s' % k)
        result.append(entry)
        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        w = entry
    return "".join(result)

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(data):
    frequency = Counter(data)
    heap = [HuffmanNode(char, freq) for char, freq in frequency.items()]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)
    
    return heap[0]

def build_huffman_codes(root, prefix="", codebook=None):
    if codebook is None:
        codebook = {}
    if root is not None:
        if root.char is not None:
            codebook[root.char] = prefix
        build_huffman_codes(root.left, prefix + "0", codebook)
        build_huffman_codes(root.right, prefix + "1", codebook)
    return codebook

def huffman_compress(data):
    root = build_huffman_tree(data)
    huffman_codes = build_huffman_codes(root)
    compressed_data = "".join(huffman_codes[char] for char in data)
    return compressed_data, huffman_codes

def huffman_decompress(compressed_data, huffman_codes):
    reverse_codes = {v: k for k, v in huffman_codes.items()}
    current_code = ""
    decompressed_data = []
    
    for bit in compressed_data:
        current_code += bit
        if current_code in reverse_codes:
            decompressed_data.append(reverse_codes[current_code])
            current_code = ""
    
    return "".join(decompressed_data)

class CompressionApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Kompresi Media dengan LZW dan Huffman")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Deskripsi LZW dan Huffman
        self.lzw_description = QLabel("LZW (Lempel-Ziv-Welch) dan Huffman adalah algoritma kompresi lossless yang digunakan untuk mengompresi data.")
        self.main_layout.addWidget(self.lzw_description)

        # Group Box untuk Informasi File
        self.file_info_group = QGroupBox("Informasi File")
        self.file_info_layout = QFormLayout()
        self.file_info_group.setLayout(self.file_info_layout)

        self.file_name_label = QLabel("Nama File:")
        self.file_name_value = QLabel("")
        self.file_info_layout.addRow(self.file_name_label, self.file_name_value)

        self.file_size_label = QLabel("Ukuran File:")
        self.file_size_value = QLabel("")
        self.file_info_layout.addRow(self.file_size_label, self.file_size_value)

        self.file_format_label = QLabel("Format File:")
        self.file_format_value = QLabel("")
        self.file_info_layout.addRow(self.file_format_label, self.file_format_value)

        self.main_layout.addWidget(self.file_info_group)

        # Entry dan Tombol untuk Memilih File
        self.file_entry_layout = QHBoxLayout()
        self.file_entry = QLineEdit()
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.open_file)
        self.file_entry_layout.addWidget(self.file_entry)
        self.file_entry_layout.addWidget(self.browse_button)
        self.main_layout.addLayout(self.file_entry_layout)

        # Radio buttons for selecting compression algorithm
        self.compression_selection_group = QGroupBox("Pilih Algoritma Kompresi")
        self.compression_selection_layout = QHBoxLayout()
        self.compression_selection_group.setLayout(self.compression_selection_layout)

        self.lzw_radio = QRadioButton("LZW")
        self.huffman_radio = QRadioButton("Huffman")
        self.lzw_radio.setChecked(True)

        self.compression_selection_layout.addWidget(self.lzw_radio)
        self.compression_selection_layout.addWidget(self.huffman_radio)

        self.main_layout.addWidget(self.compression_selection_group)

        self.compression_button_group = QButtonGroup()
        self.compression_button_group.addButton(self.lzw_radio)
        self.compression_button_group.addButton(self.huffman_radio)

        # Tombol kompresi
        self.compress_button = QPushButton("Kompresi")
        self.compress_button.clicked.connect(self.compress_file)
        self.main_layout.addWidget(self.compress_button)

        # Group Box untuk Preview Hasil Kompresi
        self.preview_group = QGroupBox("Preview Hasil Kompresi")
        self.preview_layout = QVBoxLayout()
        self.preview_group.setLayout(self.preview_layout)
        self.compressed_preview = QTextEdit()
        self.compressed_preview.setReadOnly(True)
        self.preview_layout.addWidget(self.compressed_preview)
        self.main_layout.addWidget(self.preview_group)

        # Tombol untuk menampilkan isi database
        self.show_db_button = QPushButton("Show Database Contents")
        self.show_db_button.clicked.connect(self.show_database_contents)
        self.main_layout.addWidget(self.show_db_button)

        # Text area untuk menampilkan isi database
        self.db_text = QTextEdit()
        self.db_text.setReadOnly(True)
        self.main_layout.addWidget(self.db_text)

        # Koneksi database
        self.conn = sqlite3.connect('multimedia.db')
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS multimedia (
            id INTEGER PRIMARY KEY,
            file_name TEXT,
            file_path TEXT,
            file_type TEXT,
            original_size INTEGER,
            compressed_size INTEGER
        )
        ''')
        self.conn.commit()

    def save_file_metadata(self, file_name, file_path, file_type, original_size, compressed_size):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO multimedia (file_name, file_path, file_type, original_size, compressed_size)
        VALUES (?, ?, ?, ?, ?)
        ''', (file_name, file_path, file_type, original_size, compressed_size))
        self.conn.commit()

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        if file_path:
            self.file_entry.setText(file_path)
            self.file_name_value.setText(os.path.basename(file_path))
            self.file_size_value.setText(f"{os.path.getsize(file_path)} bytes")
            self.file_format_value.setText(file_path.split('.')[-1].lower())

    def compress_file(self):
        file_path = self.file_entry.text()
        if file_path:
            try:
                file_extension = file_path.split('.')[-1].lower()
                with open(file_path, "rb") as f:
                    data = f.read()
                
                if self.lzw_radio.isChecked():
                    compressed_data = lzw_compress(data.decode('latin1'))
                    compressed_data_bytes = bytearray()
                    for num in compressed_data:
                        compressed_data_bytes.extend(num.to_bytes((num.bit_length() + 7) // 8, byteorder='big'))
                    compressed_file_path = file_path[:-len(file_extension)-1] + "_compressed.lzw"
                    with open(compressed_file_path, 'wb') as f:
                        f.write(compressed_data_bytes)
                    algorithm = "LZW"
                    compressed_size = len(compressed_data_bytes)
                else:
                    compressed_data, huffman_codes = huffman_compress(data.decode('latin1'))
                    compressed_file_path = file_path[:-len(file_extension)-1] + "_compressed.huff"
                    with open(compressed_file_path, 'w') as f:
                        f.write(compressed_data)
                    huffman_codes_path = file_path[:-len(file_extension)-1] + "_codes.huff"
                    with open(huffman_codes_path, 'w') as f:
                        f.write(str(huffman_codes))
                    algorithm = "Huffman"
                    compressed_size = len(compressed_data.encode('latin1'))

                self.save_file_metadata(
                    file_name=os.path.basename(file_path),
                    file_path=compressed_file_path,
                    file_type=file_extension,
                    original_size=len(data),
                    compressed_size=compressed_size
                )

                self.compressed_preview.setText(f"File berhasil dikompresi menggunakan {algorithm} menjadi {compressed_file_path}\nUkuran asli: {len(data)} bytes\nUkuran setelah kompresi: {compressed_size} bytes")
                QMessageBox.information(self, "Success", f"File berhasil dikompresi menjadi {compressed_file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal mengompresi file: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Harap pilih file terlebih dahulu")

    def show_database_contents(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM multimedia')
        records = cursor.fetchall()
        
        self.db_text.clear()
        for record in records:
            self.db_text.append(f"{record}")

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompressionApp()
    window.show()
    sys.exit(app.exec_())
