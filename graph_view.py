import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
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

        self.label = QLabel("No diagram yet")
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)

    def draw_table_box(self, ax, x, y, width, columns, table_name):
        header_height = 0.8
        row_height = 0.45
        total_height = header_height + (len(columns) * row_height)

        # Outer rectangle
        rect = Rectangle(
            (x, y - total_height),
            width,
            total_height,
            fill=False,
            linewidth=1.5
        )
        ax.add_patch(rect)

        # Header separator
        ax.plot(
            [x, x + width],
            [y - header_height, y - header_height],
            linewidth=1.2
        )

        # Table name
        ax.text(
            x + width / 2,
            y - 0.4,
            table_name,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold"
        )

        # Columns
        for i, col in enumerate(columns):
            cy = y - header_height - (i * row_height) - 0.22

            ax.text(
                x + 0.15,
                cy,
                col,
                ha="left",
                va="center",
                fontsize=9
            )

        return total_height

    def render_graph(self, data):
        table_columns = data.get("table_columns", {})

        if not table_columns:
            self.label.setText("No metadata available")
            self.label.setPixmap(QPixmap())
            return

        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        fig, ax = plt.subplots(figsize=(14, 8))

        ax.axis("off")

        table_names = list(table_columns.keys())
        positions = {}

        x = 1
        y = 10
        spacing_x = 5.5

        # Draw boxes
        for idx, table_name in enumerate(table_names):
            cols = table_columns[table_name]

            if not cols:
                cols = ["(no columns)"]

            px = x + (idx * spacing_x)
            py = y

            positions[table_name] = (px, py)

            self.draw_table_box(
                ax,
                px,
                py,
                4.5,
                cols,
                table_name
            )

        # Draw relationships
        sources = set(data.get("sources", []))
        targets = set(data.get("targets", []))
        intermediates = set(data.get("intermediate", []))

        # source -> target
        for s in sources:
            for t in targets:
                if s in positions and t in positions:
                    sx, sy = positions[s]
                    tx, ty = positions[t]

                    ax.annotate(
                        "",
                        xy=(tx, ty - 1),
                        xytext=(sx + 4.5, sy - 1),
                        arrowprops=dict(arrowstyle="->", linewidth=1.5)
                    )

        # source -> intermediate
        for s in sources:
            for i in intermediates:
                if s in positions and i in positions:
                    sx, sy = positions[s]
                    ix, iy = positions[i]

                    ax.annotate(
                        "",
                        xy=(ix, iy - 1),
                        xytext=(sx + 4.5, sy - 1),
                        arrowprops=dict(arrowstyle="->", linewidth=1.2)
                    )

        # intermediate -> target
        for i in intermediates:
            for t in targets:
                if i in positions and t in positions:
                    ix, iy = positions[i]
                    tx, ty = positions[t]

                    ax.annotate(
                        "",
                        xy=(tx, ty - 1),
                        xytext=(ix + 4.5, iy - 1),
                        arrowprops=dict(arrowstyle="->", linewidth=1.2)
                    )

        ax.set_xlim(0, max(10, len(table_names) * spacing_x + 3))
        ax.set_ylim(0, 12)

        plt.tight_layout()
        plt.savefig(path, dpi=160, bbox_inches="tight")
        plt.close()

        self.current_image = path

        self.label.setPixmap(
            QPixmap(path).scaled(
                1200,
                600,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    def export_image(self, output_path):
        if self.current_image:
            shutil.copyfile(self.current_image, output_path)
