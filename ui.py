from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
    QMessageBox,
    QLabel
)

from PySide6.QtCore import Qt

from parser import parse_sql
from exporter import export_csv, export_json
from graph_view import GraphWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.data = {}

        self.setWindowTitle("SQLLineage Desktop")
        self.resize(1600, 950)

        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
                color: #eaeaea;
                font-size: 13px;
            }

            QTextEdit, QTreeWidget {
                background: #252526;
                border: 1px solid #3a3a3a;
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

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Paste SQL here...")
        splitter.addWidget(self.editor)

        right_split = QSplitter(Qt.Vertical)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["SQLLineage Output"])
        right_split.addWidget(self.tree)

        self.graph = GraphWidget()
        right_split.addWidget(self.graph)

        splitter.addWidget(right_split)

        splitter.setSizes([700, 900])
        right_split.setSizes([300, 600])

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

    def parse(self):
        sql = self.editor.toPlainText().strip()

        if not sql:
            QMessageBox.warning(self, "Empty", "Paste SQL first.")
            return

        try:
            self.data = parse_sql(sql)

            self.tree.clear()

            for category in [
                "sources",
                "targets",
                "intermediate",
                "column_lineage"
            ]:
                items = self.data.get(category, [])

                root = QTreeWidgetItem([f"{category} ({len(items)})"])

                for item in items:
                    root.addChild(QTreeWidgetItem([item]))

                root.setExpanded(True)
                self.tree.addTopLevelItem(root)

            self.graph.render_graph(self.data)

            self.status.setText("Parse complete")

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