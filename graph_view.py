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

        self.label = QLabel("Lineage graph will appear here")
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)

    def render_graph(self, data):
        graph = nx.DiGraph()

        sources = data.get("sources", [])
        targets = data.get("targets", [])
        intermediates = data.get("intermediate", [])

        for node in sources + targets + intermediates:
            graph.add_node(node)

        if targets:
            for s in sources:
                for t in targets:
                    graph.add_edge(s, t)

        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        plt.figure(figsize=(10, 6))

        if graph.nodes:
            pos = nx.kamada_kawai_layout(graph)

            nx.draw(
                graph,
                pos,
                with_labels=True,
                arrows=True,
                node_size=5000,
                font_size=9
            )

        plt.tight_layout()
        plt.savefig(path, dpi=150)
        plt.close()

        self.current_image = path

        self.label.setPixmap(
            QPixmap(path).scaled(
                900,
                600,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    def export_image(self, output_path):
        if self.current_image:
            shutil.copyfile(self.current_image, output_path)