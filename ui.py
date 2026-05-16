from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QLabel,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit
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
        self.resize(1800, 1000)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #eaeaea;
                font-size: 13px;
            }

            QTextEdit, QTableWidget, QLineEdit {
                background-color: #252526;
                border: 1px solid #3a3a3a;
                color: #ffffff;
            }

            QHeaderView::section {
                background-color: #333333;
                color: white;
                padding: 8px;
                border: 1px solid #444444;
                font-weight: bold;
            }

            QPushButton {
                background-color: #0e639c;
                border: none;
                padding: 10px;
                border-radius: 6px;
                color: white;
            }

            QPushButton:hover {
                background-color: #1177bb;
            }

            QLineEdit {
                padding: 8px;
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

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Paste SQL here...")
        splitter.addWidget(self.editor)

        right_split = QSplitter(Qt.Vertical)

        top_panel = QWidget()
        top_layout = QVBoxLayout(top_panel)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "Search schema / table / column..."
        )

        top_layout.addWidget(self.search_box)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["Schema", "Table", "Column"]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(True)

        top_layout.addWidget(self.table)

        right_split.addWidget(top_panel)

        self.graph = GraphWidget()
        right_split.addWidget(self.graph)

        splitter.addWidget(right_split)

        splitter.setSizes([700, 1100])
        right_split.setSizes([600, 350])

        root.addWidget(splitter)

        self.status = QLabel("Ready")
        root.addWidget(self.status)

        self.open_btn.clicked.connect(self.open_file)
        self.parse_btn.clicked.connect(self.parse)
        self.csv_btn.clicked.connect(self.save_csv)
        self.json_btn.clicked.connect(self.save_json)
        self.img_btn.clicked.connect(self.save_image)
        self.search_box.textChanged.connect(self.filter_table)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SQL",
            "",
            "SQL Files (*.sql);;All Files (*)"
        )

        if path:
            with open(
                path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as f:
                self.editor.setPlainText(f.read())

            self.status.setText(f"Loaded: {path}")

    def parse(self):
        sql = self.editor.toPlainText().strip()

        if not sql:
            QMessageBox.warning(
                self,
                "Empty",
                "Paste SQL first."
            )
            return

        try:
            self.data = parse_sql(sql)
            self.populate_table()
            self.graph.render_graph(self.data)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Parse Error",
                str(e)
            )

    def populate_table(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        row = 0

        for full_table, columns in self.data.get(
            "table_columns",
            {}
        ).items():

            if "." in full_table:
                schema, table = full_table.split(".", 1)
            else:
                schema = ""
                table = full_table

            if not columns:
                self.table.insertRow(row)

                self.table.setItem(
                    row,
                    0,
                    QTableWidgetItem(schema)
                )
                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(table)
                )
                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem("")
                )

                row += 1
                continue

            for col in columns:
                self.table.insertRow(row)

                self.table.setItem(
                    row,
                    0,
                    QTableWidgetItem(schema)
                )

                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(table)
                )

                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(col)
                )

                row += 1

        self.table.setSortingEnabled(True)

        self.status.setText(
            f"Parse complete — {self.table.rowCount()} rows"
        )

    def filter_table(self, text):
        text = text.lower()

        for row in range(self.table.rowCount()):
            visible = False

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)

                if item and text in item.text().lower():
                    visible = True
                    break

            self.table.setRowHidden(row, not visible)

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
