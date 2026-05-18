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
        except Exception:
            return {
                "table_columns": {},
                "relationships": []
            }

        for stmt in statements:
            self.collect_ctes(stmt)
            self.walk_statement(stmt)

        filtered = {}

        for table, cols in self.table_columns.items():
            short = table.split(".")[-1]

            if short in self.cte_names:
                continue

            filtered[table] = sorted(cols)

        filtered_relationships = []

        for rel in self.relationships:
            left_table = rel["left_table"].split(".")[-1]
            right_table = rel["right_table"].split(".")[-1]

            if left_table in self.cte_names:
                continue

            if right_table in self.cte_names:
                continue

            filtered_relationships.append(rel)

        return {
            "table_columns": filtered,
            "relationships": filtered_relationships
        }

    def collect_ctes(self, node):
        for cte in node.find_all(exp.CTE):
            if cte.alias:
                self.cte_names.add(str(cte.alias))

    def walk_statement(self, node):
        alias_map = {}
        self.collect_tables(node, alias_map)
        self.collect_columns(node, alias_map)
        self.collect_relationships(node, alias_map)

    def collect_tables(self, node, alias_map):
        for table in node.find_all(exp.Table):
            table_name = table.name
            schema = table.db

            full = f"{schema}.{table_name}" if schema else table_name

            alias_map[table_name] = full

            if table.alias:
                alias_map[str(table.alias)] = full

            self.table_columns.setdefault(full, set())

    def collect_columns(self, node, alias_map):
        for col in node.find_all(exp.Column):
            name = col.name
            alias = col.table

            if not name:
                continue

            if alias and alias in alias_map:
                self.table_columns[alias_map[alias]].add(name)

            elif len(alias_map) == 1:
                only_table = next(iter(alias_map.values()))
                self.table_columns[only_table].add(name)

    def collect_relationships(self, node, alias_map):
        for eq in node.find_all(exp.EQ):
            left = eq.left
            right = eq.right

            if not isinstance(left, exp.Column):
                continue

            if not isinstance(right, exp.Column):
                continue

            left_alias = left.table
            right_alias = right.table

            if not left_alias or not right_alias:
                continue

            if left_alias not in alias_map:
                continue

            if right_alias not in alias_map:
                continue

            self.relationships.append({
                "left_table": alias_map[left_alias],
                "left_column": left.name,
                "right_table": alias_map[right_alias],
                "right_column": right.name
            })


def parse_sql(sql_text):
    parser = SQLMetadataParser()
    return parser.parse(sql_text)
