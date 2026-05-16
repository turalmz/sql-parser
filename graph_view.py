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

        self.label = QLabel("No lineage graph yet")
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)

    def render_graph(self, data):
        graph = nx.DiGraph()

        sources = data.get("sources", [])
        targets = data.get("targets", [])
        intermediates = data.get("intermediate", [])

        all_nodes = set(sources + targets + intermediates)

        if not all_nodes:
            self.label.setText("No lineage graph available")
            self.label.setPixmap(QPixmap())
            return

        for node in all_nodes:
            graph.add_node(node)

        if targets:
            for s in sources:
                for t in targets:
                    graph.add_edge(s, t)

        if intermediates:
            for s in sources:
                for i in intermediates:
                    graph.add_edge(s, i)

            for i in intermediates:
                for t in targets:
                    graph.add_edge(i, t)

        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        plt.figure(figsize=(12, 7))

        if len(graph.nodes) == 1:
            pos = {list(graph.nodes)[0]: (0, 0)}
        else:
            pos = nx.spring_layout(
                graph,
                seed=42,
                k=2.5
            )

        nx.draw(
            graph,
            pos,
            with_labels=True,
            arrows=True,
            node_size=6000,
            font_size=9,
            width=2
        )

        plt.tight_layout()
        plt.savefig(
            path,
            dpi=150,
            bbox_inches="tight"
        )
        plt.close()

        self.current_image = path

        self.label.setPixmap(
            QPixmap(path).scaled(
                1000,
                500,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    def export_image(self, output_path):
        if self.current_image:
            shutil.copyfile(
                self.current_image,
                output_path
            )
