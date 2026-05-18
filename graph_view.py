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

        self.label = QLabel("No ER diagram yet")
        self.label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.label)

    def draw_entity(self, ax, x, y, table_name, columns):
        header_height = 0.7
        row_height = 0.38
        width = 4.8
        total_height = header_height + max(1, len(columns)) * row_height

        rect = Rectangle(
            (x, y - total_height),
            width,
            total_height,
            fill=False,
            linewidth=1.5
        )
        ax.add_patch(rect)

        ax.plot(
            [x, x + width],
            [y - header_height, y - header_height],
            linewidth=1.2
        )

        ax.text(
            x + width / 2,
            y - 0.35,
            table_name,
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold"
        )

        column_positions = {}

        if not columns:
            columns = ["(no columns)"]

        for idx, col in enumerate(columns):
            cy = y - header_height - (idx * row_height) - 0.2

            ax.text(
                x + 0.15,
                cy,
                col,
                ha="left",
                va="center",
                fontsize=8
            )

            column_positions[col] = (x + width, cy)

        return {
            "x": x,
            "y": y,
            "width": width,
            "height": total_height,
            "columns": column_positions
        }

    def render_graph(self, data):
        tables = data.get("table_columns", {})
        relationships = data.get("relationships", [])

        if not tables:
            self.label.setText("No ER metadata available")
            self.label.setPixmap(QPixmap())
            return

        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

        fig, ax = plt.subplots(figsize=(16, 9))
        ax.axis("off")

        layout_positions = {}
        table_names = list(tables.keys())

        spacing_x = 6.5
        spacing_y = 5
        cols_per_row = 3

        for idx, table_name in enumerate(table_names):
            row = idx // cols_per_row
            col = idx % cols_per_row

            x = 1 + col * spacing_x
            y = 11 - row * spacing_y

            layout_positions[table_name] = self.draw_entity(
                ax,
                x,
                y,
                table_name,
                tables[table_name]
            )

        for rel in relationships:
            lt = rel["left_table"]
            lc = rel["left_column"]
            rt = rel["right_table"]
            rc = rel["right_column"]

            if lt not in layout_positions:
                continue

            if rt not in layout_positions:
                continue

            left_info = layout_positions[lt]
            right_info = layout_positions[rt]

            if lc not in left_info["columns"]:
                continue

            if rc not in right_info["columns"]:
                continue

            sx, sy = left_info["columns"][lc]
            tx = right_info["x"]
            ty = right_info["columns"][rc][1]

            ax.annotate(
                "",
                xy=(tx, ty),
                xytext=(sx, sy),
                arrowprops=dict(
                    arrowstyle="->",
                    linewidth=1.3
                )
            )

        ax.set_xlim(0, 22)
        ax.set_ylim(0, 12)

        plt.tight_layout()
        plt.savefig(
            path,
            dpi=160,
            bbox_inches="tight"
        )
        plt.close()

        self.current_image = path

        self.label.setPixmap(
            QPixmap(path).scaled(
                1300,
                650,
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
