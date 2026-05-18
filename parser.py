from collections import defaultdict
import sqlglot
from sqlglot import exp


class SQLMetadataParser:
    def __init__(self):
        self.table_columns = defaultdict(set)
        self.relationships = []
        self.cte_names = set()

    def parse(self, sql_text):
        self.table_columns.clear()
        self.relationships.clear()
        self.cte_names.clear()

        try:
            statements = sqlglot.parse(sql_text)
        except Exception as e:
            return {
                "tables": {},
                "relationships": [],
                "error": str(e)
            }

        for stmt in statements:
            self._collect_ctes(stmt)
            self._walk(stmt)

        filtered_tables = {}

        for table, cols in self.table_columns.items():
            short = table.split(".")[-1]
            if short in self.cte_names:
                continue
            filtered_tables[table] = sorted(cols)

        filtered_relationships = []

        for rel in self.relationships:
            lt = rel["left_table"].split(".")[-1]
            rt = rel["right_table"].split(".")[-1]

            if lt in self.cte_names:
                continue
            if rt in self.cte_names:
                continue

            filtered_relationships.append(rel)

        return {
            "tables": filtered_tables,
            "relationships": filtered_relationships,
            "error": None
        }

    def _collect_ctes(self, node):
        for cte in node.find_all(exp.CTE):
            if cte.alias:
                self.cte_names.add(str(cte.alias))

    def _walk(self, node):
        alias_map = {}
        self._collect_tables(node, alias_map)
        self._collect_columns(node, alias_map)
        self._collect_relationships(node, alias_map)

    def _collect_tables(self, node, alias_map):
        for table in node.find_all(exp.Table):
            table_name = table.name
            schema = table.db

            full_name = f"{schema}.{table_name}" if schema else table_name

            alias_map[table_name] = full_name

            if table.alias:
                alias_map[str(table.alias)] = full_name

            self.table_columns.setdefault(full_name, set())

    def _collect_columns(self, node, alias_map):
        for col in node.find_all(exp.Column):
            if not col.name:
                continue

            alias = col.table

            if alias and alias in alias_map:
                self.table_columns[alias_map[alias]].add(col.name)

            elif len(alias_map) == 1:
                only_table = next(iter(alias_map.values()))
                self.table_columns[only_table].add(col.name)

    def _collect_relationships(self, node, alias_map):
        for eq in node.find_all(exp.EQ):
            left = eq.left
            right = eq.right

            if not isinstance(left, exp.Column):
                continue

            if not isinstance(right, exp.Column):
                continue

            if not left.table or not right.table:
                continue

            if left.table not in alias_map:
                continue

            if right.table not in alias_map:
                continue

            rel = {
                "left_table": alias_map[left.table],
                "left_column": left.name,
                "right_table": alias_map[right.table],
                "right_column": right.name
            }

            if rel not in self.relationships:
                self.relationships.append(rel)


def parse_sql(sql_text):
    parser = SQLMetadataParser()
    return parser.parse(sql_text)
