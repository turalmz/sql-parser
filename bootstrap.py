import os
import textwrap

files = {
    "requirements.txt": """
PySide6
sqllineage
networkx
matplotlib
""",

    "parser.py": """
from sqllineage.runner import LineageRunner

def parse_sql(sql_text: str):
    runner = LineageRunner(sql_text)

    data = {
        "sources": sorted(str(t) for t in runner.source_tables),
        "targets": sorted(str(t) for t in runner.target_tables),
        "intermediate": sorted(str(t) for t in getattr(runner, "intermediate_tables", [])),
        "column_lineage": []
    }

    try:
        cols = getattr(runner, "column_lineage", None)
        if cols:
            data["column_lineage"] = [str(c) for c in cols]
    except Exception:
        pass

    return data
""",

    "exporter.py": """
import csv
import json

def export_csv(path, data):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "value"])

        for key in ["sources", "targets", "intermediate", "column_lineage"]:
            for item in data.get(key, []):
                writer.writerow([key, item])

def export_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
""",

    "graph_view.py": """
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx
import tempfile
import shutil
import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.current_image = None

        layout = QVBoxLayout(self)

        self.label = QLabel("No graph yet")
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)

    def render_graph(self, data):
        graph = nx.DiGraph()

        for source in data.get("sources", []):
            graph.add_node(source)

        for target in data.get("targets", []):
            graph.add_node(target)

        for source in data.get("sources", []):
            for target in data.get("targets", []):
                graph.add_edge(source, target)

        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        plt.figure(figsize=(9, 6))

        if graph.nodes:
            pos = nx.spring_layout(graph, seed=42)
            nx.draw(graph, pos, with_labels=True, arrows=True)

        plt.tight_layout()
        plt.savefig(path)
        plt.close()

        self.current_image = path

        self.label.setPixmap(
            QPixmap(path).scaled(
                800,
                500,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    def export_image(self, output_path):
        if self.current_image:
            shutil.copyfile(self.current_image, output_path)
""",

    "ui.py": """
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
    QMessageBox
)

from parser import parse_sql
from exporter import export_csv, export_json
from graph_view import GraphWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.data = {}

        self.setWindowTitle("SQLLineage Desktop")
        self.resize(1400, 900)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        top = QHBoxLayout()

        self.open_btn = QPushButton("Open SQL")
        self.parse_btn = QPushButton("Parse")
        self.csv_btn = QPushButton("Export CSV")
        self.json_btn = QPushButton("Export JSON")
        self.img_btn = QPushButton("Export Graph PNG")

        for btn in [
            self.open_btn,
            self.parse_btn,
            self.csv_btn,
            self.json_btn,
            self.img_btn
        ]:
            top.addWidget(btn)

        layout.addLayout(top)

        splitter = QSplitter()

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Paste SQL here...")

        splitter.addWidget(self.editor)

        right = QSplitter()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["SQLLineage Results"])

        self.graph = GraphWidget()

        right.addWidget(self.tree)
        right.addWidget(self.graph)

        splitter.addWidget(right)

        layout.addWidget(splitter)

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

    def parse(self):
        sql = self.editor.toPlainText().strip()

        if not sql:
            QMessageBox.warning(self, "Empty", "Paste SQL first.")
            return

        self.data = parse_sql(sql)

        self.tree.clear()

        for category in [
            "sources",
            "targets",
            "intermediate",
            "column_lineage"
        ]:
            root = QTreeWidgetItem([category])

            for item in self.data.get(category, []):
                root.addChild(QTreeWidgetItem([item]))

            root.setExpanded(True)
            self.tree.addTopLevelItem(root)

        self.graph.render_graph(self.data)

    def save_csv(self):
        if self.data:
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save CSV",
                "",
                "CSV (*.csv)"
            )

            if path:
                export_csv(path, self.data)

    def save_json(self):
        if self.data:
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
""",

    "main.py": """
import sys
from PySide6.QtWidgets import QApplication
from ui import MainWindow

app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())
""",

    "build_windows.bat": """
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --windowed --name SQLLineageDesktop main.py
""",

    "build_mac.sh": """
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller
pyinstaller --windowed --name SQLLineageDesktop main.py
"""
}

for filename, content in files.items():
    with open(filename, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).strip() + "\n")

print("Project created successfully.")