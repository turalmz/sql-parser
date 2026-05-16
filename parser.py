from sqllineage.runner import LineageRunner
import re


def extract_columns(sql_text):
    sql = re.sub(r"\s+", " ", sql_text.strip(), flags=re.MULTILINE)

    alias_map = {}
    table_columns = {}

    # FROM / JOIN alias mapping
    alias_pattern = re.finditer(
        r"(FROM|JOIN)\s+([a-zA-Z0-9_.]+)(?:\s+([a-zA-Z0-9_]+))?",
        sql,
        re.IGNORECASE
    )

    tables = []

    for match in alias_pattern:
        table = match.group(2)
        alias = match.group(3)

        tables.append(table)

        if alias:
            alias_map[alias] = table

        table_columns.setdefault(table, [])

    # Extract SELECT ... FROM
    select_match = re.search(
        r"SELECT\s+(.*?)\s+FROM\s",
        sql,
        re.IGNORECASE
    )

    if not select_match:
        return table_columns

    select_part = select_match.group(1)
    columns = [c.strip() for c in select_part.split(",")]

    for col in columns:
        # remove aliases
        col = re.sub(r"\s+AS\s+.+$", "", col, flags=re.IGNORECASE)

        # alias.column
        if "." in col:
            alias, column = col.split(".", 1)

            alias = alias.strip()
            column = column.strip()

            if alias in alias_map:
                table_columns[alias_map[alias]].append(column)

        else:
            # single table fallback
            if len(tables) == 1:
                table_columns[tables[0]].append(col)

    return table_columns


def parse_sql(sql_text: str):
    runner = LineageRunner(sql_text)

    data = {
        "sources": sorted(str(t) for t in runner.source_tables),
        "targets": sorted(str(t) for t in runner.target_tables),
        "intermediate": [],
        "column_lineage": [],
        "table_columns": {}
    }

    try:
        data["intermediate"] = sorted(
            str(t) for t in runner.intermediate_tables
        )
    except:
        pass

    try:
        cols = runner.column_lineage
        if cols:
            data["column_lineage"] = [str(c) for c in cols]
    except:
        pass

    data["table_columns"] = extract_columns(sql_text)

    return data
