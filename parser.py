from sqllineage.runner import LineageRunner

def parse_sql(sql_text: str):
    runner = LineageRunner(sql_text)

    data = {
        "sources": sorted(str(t) for t in runner.source_tables),
        "targets": sorted(str(t) for t in runner.target_tables),
        "intermediate": sorted(str(t) for t in getattr(runner, "intermediate_tables", [])),
        "column_lineage": []
    }

    try:
        cols = getattr(runner, "column_lineage", None)
        if cols:
            data["column_lineage"] = [str(c) for c in cols]
    except Exception:
        pass

    return data
