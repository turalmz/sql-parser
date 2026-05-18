from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PySide6.QtCore import QRegularExpression


class SQLHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#4FC1FF"))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))

        self.rules = []

        keywords = [
            "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "FULL",
            "OUTER", "INNER", "ON", "GROUP", "BY", "HAVING", "ORDER",
            "UNION", "WITH", "AS", "INSERT", "INTO", "VALUES",
            "UPDATE", "DELETE", "MERGE", "USING", "WHEN", "THEN",
            "CASE", "END", "EXISTS", "IN", "AND", "OR", "NOT"
        ]

        for word in keywords:
            pattern = QRegularExpression(rf"\b{word}\b")
            self.rules.append((pattern, keyword_format))

        self.rules.append(
            (QRegularExpression(r"'[^']*'"), string_format)
        )

        self.rules.append(
            (QRegularExpression(r"--[^\n]*"), comment_format)
        )

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)

            while it.hasNext():
                match = it.next()
                self.setFormat(
                    match.capturedStart(),
                    match.capturedLength(),
                    fmt
                )
