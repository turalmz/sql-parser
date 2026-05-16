from collections import defaultdict
from sqllineage.runner import LineageRunner
import sqlglot
from sqlglot import exp


def normalize_table_name(table_expr):
    schema = table_expr.db
    table = table_expr.name

    if schema:
        return schema, table, f"{schema}.{table}"

    return "", table, table


def collect_aliases(statement):
    alias_map = {}
    tables = {}

    for table in statement.find_all(exp.Table):
        schema, table_name, full_name = normalize_table_name(table)

        alias = None
        if table.alias:
            alias = str(table.alias)

        tables[full_name] = {
            "schema": schema,
            "table": table_name
        }

        alias_map[table_name] = full_name

        if alias:
            alias_map[alias] = full_name

    return alias_map, tables


def collect_columns(statement, alias_map, tables):
    result = defaultdict(set)

    for col in statement.find_all(exp.Column):
        col_name = col.name

        if not col_name:
            continue

        table_alias = col.table

        if table_alias:
            if table_alias in alias_map:
                full_table = alias_map[table_alias]
                result[full_table].add(col_name)

        else:
            if len(tables) == 1:
                only_table = next(iter(tables.keys()))
                result[only_table].add(col_name)

    return result


def extract_table_columns(sql_text):
    merged = defaultdict(set)

    try:
        statements = sqlglot.parse(sql_text)
    except Exception:
        return {}

    for statement in statements:
        alias_map, tables = collect_aliases(statement)

        cols = collect_columns(statement, alias_map, tables)

        for table_name, columns in cols.items():
            merged[table_name].update(columns)

        for table_name in tables:
            merged.setdefault(table_name, set())

    final = {}

    for table_name, columns in merged.items():
        final[table_name] = sorted(columns)

    return final


def parse_sql(sql_text: str):
    data = {
        "sources": [],
        "targets": [],
        "intermediate": [],
        "column_lineage": [],
        "table_columns": {}
    }

    try:
        runner = LineageRunner(sql_text)

        try:
            data["sources"] = sorted(
                str(t) for t in runner.source_tables
            )
        except Exception:
            pass

        try:
            data["targets"] = sorted(
                str(t) for t in runner.target_tables
            )
        except Exception:
            pass

        try:
            data["intermediate"] = sorted(
                str(t) for t in runner.intermediate_tables
            )
        except Exception:
            pass

        try:
            cols = runner.column_lineage
            if cols:
                data["column_lineage"] = [
                    str(c) for c in cols
                ]
        except Exception:
            pass

    except Exception:
        pass

    data["table_columns"] = extract_table_columns(sql_text)

    return data
