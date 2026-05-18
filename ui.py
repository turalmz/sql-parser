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
    QLineEdit,
    QFrame
)

from PySide6.QtCore import Qt

from parser import parse_sql
from sql_highlighter import SQLHighlighter


class MetricCard(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setStyleSheet("""
            QFrame {
                background-color: #252526;
                border: 1px solid #3a3a3a;
                border-radius: 10px;
            }

            QLabel {
                color: white;
            }
        """)

        layout = QVBoxLayout(self)

        self.title = QLabel(title)
        self.title.setStyleSheet("""
            font-size: 11px;
            color: #aaaaaa;
        """)

        self.value = QLabel("0")
        self.value.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
        """)

        layout.addWidget(self.title)
        layout.addWidget(self.value)

    def set_value(self, value):
        self.value.setText(str(value))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.data = None

        self.setWindowTitle("SQL Metadata Explorer")
        self.resize(1800, 1000)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
                font-size: 13px;
            }

            QTextEdit, QTableWidget, QLineEdit {
                background-color: #252526;
                border: 1px solid #3a3a3a;
                color: white;
                border-radius: 8px;
            }

            QPushButton {
                background-color: #0e639c;
                border: none;
                padding: 12px;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #1177bb;
            }

            QHeaderView::section {
                background-color: #333333;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)

        # SIDEBAR
        sidebar = QFrame()
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #161616;
                border-right: 1px solid #2d2d2d;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(16)

        title = QLabel("SQL Metadata Explorer")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
        """)

        sidebar_layout.addWidget(title)

        self.open_btn = QPushButton("Open SQL File")
        self.parse_btn = QPushButton("Parse SQL")

        sidebar_layout.addWidget(self.open_btn)
        sidebar_layout.addWidget(self.parse_btn)

        search_label = QLabel("Search")
        search_label.setStyleSheet("""
            font-size: 14px;
            color: #aaaaaa;
        """)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "schema / table / column..."
        )

        sidebar_layout.addWidget(search_label)
        sidebar_layout.addWidget(self.search)

        summary = QLabel("Summary")
        summary.setStyleSheet("""
            font-size: 14px;
            color: #aaaaaa;
        """)

        sidebar_layout.addWidget(summary)

        self.tables_card = MetricCard("Tables")
        self.columns_card = MetricCard("Columns")
        self.relations_card = MetricCard("Relationships")

        sidebar_layout.addWidget(self.tables_card)
        sidebar_layout.addWidget(self.columns_card)
        sidebar_layout.addWidget(self.relations_card)

        sidebar_layout.addStretch()

        root.addWidget(sidebar)

        # MAIN CONTENT
        content = QSplitter(Qt.Vertical)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Paste SQL here...")
        SQLHighlighter(self.editor.document())

        content.addWidget(self.editor)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Schema",
            "Table",
            "Column",
            "Related To"
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)

        content.addWidget(self.table)

        content.setSizes([450, 500])

        root.addWidget(content)

        self.open_btn.clicked.connect(self.open_file)
        self.parse_btn.clicked.connect(self.parse)
        self.search.textChanged.connect(self.filter_rows)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open SQL",
            "",
            "SQL Files (*.sql)"
        )

        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())

    def parse(self):
        sql = self.editor.toPlainText()

        if not sql.strip():
            QMessageBox.warning(
                self,
                "Empty",
                "Paste SQL first."
            )
            return

        self.data = parse_sql(sql)

        if self.data["error"]:
            QMessageBox.critical(
                self,
                "Parse Error",
                self.data["error"]
            )
            return

        self.populate()

    def populate(self):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        relationships = self.data["relationships"]
        relation_lookup = {}

        for rel in relationships:
            relation_lookup[
                (rel["left_table"], rel["left_column"])
            ] = (
                f'{rel["right_table"]}.{rel["right_column"]}'
            )

        row = 0

        for full_table, cols in self.data["tables"].items():
            if "." in full_table:
                schema, table = full_table.split(".", 1)
            else:
                schema = ""
                table = full_table

            for col in cols:
                self.table.insertRow(row)

                related = relation_lookup.get(
                    (full_table, col),
                    ""
                )

                self.table.setItem(
                    row, 0, QTableWidgetItem(schema)
                )
                self.table.setItem(
                    row, 1, QTableWidgetItem(table)
                )
                self.table.setItem(
                    row, 2, QTableWidgetItem(col)
                )
                self.table.setItem(
                    row, 3, QTableWidgetItem(related)
                )

                row += 1

        self.table.setSortingEnabled(True)

        self.tables_card.set_value(len(self.data["tables"]))
        self.columns_card.set_value(self.table.rowCount())
        self.relations_card.set_value(len(relationships))

    def filter_rows(self, text):
        text = text.lower()

        for row in range(self.table.rowCount()):
            visible = False

            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)

                if item and text in item.text().lower():
                    visible = True
                    break

            self.table.setRowHidden(row, not visible)
