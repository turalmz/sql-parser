from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QFileDialog,
    QSplitter,
    QMessageBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView
)

from PySide6.QtCore import Qt

from parser import parse_sql
from exporter import export_csv, export_json
from graph_view import GraphWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.data = {}

        self.setWindowTitle("SQL Metadata Explorer")
        self.resize(1700, 950)

        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
                color: #eaeaea;
                font-size: 13px;
            }

            QTextEdit, QTableWidget {
                background: #252526;
                border: 1px solid #3a3a3a;
                gridline-color: #3a3a3a;
            }

            QHeaderView::section {
                background: #333333;
                color: white;
                padding: 8px;
                border: 1px solid #444;
                font-weight: bold;
            }

            QPushButton {
                background: #0e639c;
                border: none;
                padding: 10px;
                border-radius: 6px;
            }

            QPushButton:hover {
                background: #1177bb;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)

        toolbar = QHBoxLayout()

        self.open_btn = QPushButton("Open SQL File")
        self.parse_btn = QPushButton("Parse")
        self.csv_btn = QPushButton("Export CSV")
        self.json_btn = QPushButton("Export JSON")
        self.img_btn = QPushButton("Export Graph")

        for btn in [
            self.open_btn,
            self.parse_btn,
            self.csv_btn,
            self.json_btn,
            self.img_btn
        ]:
            toolbar.addWidget(btn)

        root.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)

        # LEFT: SQL editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Paste SQL here...")
        splitter.addWidget(self.editor)

        # RIGHT
        right_split = QSplitter(Qt.Vertical)

        # ORACLE STYLE TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Schema", "Table", "Column"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)

        right_split.addWidget(self.table)

        # GRAPH
        self.graph = GraphWidget()
        right_split.addWidget(self.graph)

        splitter.addWidget(right_split)

        splitter.setSizes([700, 1000])
        right_split.setSizes([500, 400])

        root.addWidget(splitter)

        self.status = QLabel("Ready")
        root.addWidget(self.status)

        self.open_btn.clicked.connect(self.open_file)
        self.parse_btn.clicked.connect(self.parse)
        self.csv_btn.clicked.connect(self.save_csv)
        self.json_btn.clicked.connect(self.save_json)
        self.img_btn.clicked.connect(self.save_image)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SQL",
            "",
            "SQL Files (*.sql);;All Files (*)"
        )

        if path:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                self.editor.setPlainText(f.read())

            self.status.setText(f"Loaded: {path}")

    def split_table_name(self, full_name):
        if "." in full_name:
            parts = full_name.split(".", 1)
            return parts[0], parts[1]
        return "", full_name

    def parse(self):
        sql = self.editor.toPlainText().strip()

        if not sql:
            QMessageBox.warning(self, "Empty", "Paste SQL first.")
            return

        try:
            self.data = parse_sql(sql)

            self.table.setRowCount(0)

            row = 0

            for table_name, columns in self.data.get("table_columns", {}).items():
                schema, table = self.split_table_name(table_name)

                if not columns:
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(schema))
                    self.table.setItem(row, 1, QTableWidgetItem(table))
                    self.table.setItem(row, 2, QTableWidgetItem("(no columns found)"))
                    row += 1
                    continue

                for col in columns:
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(schema))
                    self.table.setItem(row, 1, QTableWidgetItem(table))
                    self.table.setItem(row, 2, QTableWidgetItem(col))
                    row += 1

            self.graph.render_graph(self.data)

            self.status.setText(
                f"Parse complete - {self.table.rowCount()} metadata rows"
            )

        except Exception as e:
            QMessageBox.critical(self, "Parse Error", str(e))
            self.status.setText("Parse failed")

    def save_csv(self):
        if not self.data:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            "",
            "CSV (*.csv)"
        )

        if path:
            export_csv(path, self.data)

    def save_json(self):
        if not self.data:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON",
            "",
            "JSON (*.json)"
        )

        if path:
            export_json(path, self.data)

    def save_image(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PNG",
            "",
            "PNG (*.png)"
        )

        if path:
            self.graph.export_image(path)
