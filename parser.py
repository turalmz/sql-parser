from sqllineage.runner import LineageRunner
import sqlglot
from sqlglot import exp


def extract_table_columns(sql_text):
    result = {}

    try:
        tree = sqlglot.parse_one(sql_text)
    except Exception:
        return result

    alias_map = {}

    # Build alias -> table map
    for table in tree.find_all(exp.Table):
        table_name = table.name
        schema = table.db

        full_name = f"{schema}.{table_name}" if schema else table_name

        alias = None
        if table.alias:
            alias = table.alias

        alias_map[alias or table_name] = full_name

        if full_name not in result:
            result[full_name] = set()

    # Extract columns
    for col in tree.find_all(exp.Column):
        col_name = col.name

        if not col_name:
            continue

        table_alias = col.table

        if table_alias:
            if table_alias in alias_map:
                result[alias_map[table_alias]].add(col_name)
        else:
            # single table fallback
            if len(result) == 1:
                only_table = next(iter(result))
                result[only_table].add(col_name)

    return {k: sorted(list(v)) for k, v in result.items()}


def parse_sql(sql_text: str):
    runner = LineageRunner(sql_text)

    data = {
        "sources": [],
        "targets": [],
        "intermediate": [],
        "column_lineage": [],
        "table_columns": {}
    }

    try:
        data["sources"] = sorted(str(t) for t in runner.source_tables)
    except:
        pass

    try:
        data["targets"] = sorted(str(t) for t in runner.target_tables)
    except:
        pass

    try:
        data["intermediate"] = sorted(str(t) for t in runner.intermediate_tables)
    except:
        pass

    try:
        cols = runner.column_lineage
        if cols:
            data["column_lineage"] = [str(c) for c in cols]
    except:
        pass

    data["table_columns"] = extract_table_columns(sql_text)

    return data
