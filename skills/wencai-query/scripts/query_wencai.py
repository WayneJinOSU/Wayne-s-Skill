#!/usr/bin/env python3
import argparse
import csv
import json
import os
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Tonghuashun Wencai query through pywencai."
    )
    parser.add_argument("query", help="Natural-language Wencai query sentence in Chinese")
    parser.add_argument(
        "--query-type",
        default=os.getenv("WENCAI_QUERY_TYPE", "stock"),
        help="Wencai query type, for example stock, fund, index, hkstock, usstock, future, bond",
    )
    parser.add_argument(
        "--perpage",
        type=int,
        default=int(os.getenv("WENCAI_PERPAGE", "100")),
        help="Rows to request per page",
    )
    parser.add_argument(
        "--page",
        type=int,
        default=int(os.getenv("WENCAI_PAGE", "1")),
        help="Page number to fetch",
    )
    parser.add_argument(
        "--sort-key",
        default=os.getenv("WENCAI_SORT_KEY"),
        help="Column to sort on",
    )
    parser.add_argument(
        "--sort-order",
        choices=("asc", "desc"),
        default=os.getenv("WENCAI_SORT_ORDER", "desc"),
        help="Sort direction",
    )
    parser.add_argument(
        "--find",
        action="append",
        default=[],
        help="Column name to keep. Repeat or use comma-separated names.",
    )
    parser.add_argument(
        "--cookie",
        default=os.getenv("WENCAI_COOKIE"),
        help="Cookie header copied from iwencai.com. Defaults to WENCAI_COOKIE.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Enable pywencai pagination loop if supported by the installed version",
    )
    parser.add_argument(
        "--retry",
        type=int,
        default=int(os.getenv("WENCAI_RETRY", "3")),
        help="Retry count passed through to pywencai",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=20,
        help="Preview rows shown in markdown mode",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Console output format",
    )
    parser.add_argument(
        "--out",
        help="Optional output path ending in .json, .csv, or .tsv",
    )
    return parser


def fail(message: str, exit_code: int = 1) -> int:
    print(message, file=sys.stderr)
    return exit_code


def import_pywencai():
    try:
        import pywencai  # type: ignore
    except ImportError:
        raise SystemExit(
            fail(
                "pywencai is not installed. Install it first, for example: pip install pywencai pandas"
            )
        )
    return pywencai


def normalize_find(values):
    columns = []
    for value in values:
        parts = [part.strip() for part in value.split(",") if part.strip()]
        columns.extend(parts)
    seen = set()
    unique = []
    for column in columns:
        if column not in seen:
            unique.append(column)
            seen.add(column)
    return unique


def is_table(value) -> bool:
    return hasattr(value, "to_dict") and hasattr(value, "columns")


def make_jsonable(value):
    if is_table(value):
        return value.to_dict(orient="records")
    if isinstance(value, dict):
        return {str(key): make_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [make_jsonable(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if value != value:
        return None
    return value


def normalize_result(result):
    if result is None:
        return {"kind": "empty", "row_count": 0, "columns": [], "records": []}

    if is_table(result):
        records = make_jsonable(result.to_dict(orient="records"))
        columns = [str(column) for column in list(result.columns)]
        return {
            "kind": "table",
            "row_count": len(records),
            "columns": columns,
            "records": records,
        }

    if isinstance(result, list):
        columns = []
        if result and isinstance(result[0], dict):
            columns = [str(key) for key in result[0].keys()]
        return {
            "kind": "list",
            "row_count": len(result),
            "columns": columns,
            "records": make_jsonable(result),
        }

    if isinstance(result, dict):
        normalized = make_jsonable(result)
        return {"kind": "dict", "row_count": 1, "columns": list(normalized.keys()), "records": [normalized]}

    return {"kind": type(result).__name__, "row_count": 1, "columns": [], "records": [str(result)]}


def format_cell(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def markdown_table(columns, records, limit):
    if not records:
        return "No rows returned."

    if not columns:
        keys = []
        for record in records:
            if isinstance(record, dict):
                for key in record.keys():
                    if key not in keys:
                        keys.append(str(key))
        columns = keys

    preview = records[:limit]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for record in preview:
        if isinstance(record, dict):
            row = [format_cell(record.get(column, "")) for column in columns]
        else:
            row = [format_cell(record)]
        body.append("| " + " | ".join(row) + " |")
    return "\n".join([header, separator] + body)


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_delimited(path: Path, columns, records, delimiter: str):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter=delimiter)
        writer.writeheader()
        for record in records:
            if isinstance(record, dict):
                writer.writerow({column: format_cell(record.get(column, "")) for column in columns})
            else:
                writer.writerow({columns[0] if columns else "value": format_cell(record)})


def save_output(path_value: str, payload):
    path = Path(path_value).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    records = payload["records"]
    columns = payload["columns"]

    if suffix == ".json":
        write_json(path, payload)
        return path

    if suffix in {".csv", ".tsv"}:
        delimiter = "," if suffix == ".csv" else "\t"
        if not columns and records:
            first = records[0]
            if isinstance(first, dict):
                columns = [str(key) for key in first.keys()]
            else:
                columns = ["value"]
        write_delimited(path, columns, records, delimiter)
        return path

    raise SystemExit(fail("Unsupported output extension. Use .json, .csv, or .tsv"))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.perpage <= 0:
        return fail("--perpage must be greater than 0")
    if args.page <= 0:
        return fail("--page must be greater than 0")
    if args.rows <= 0:
        return fail("--rows must be greater than 0")
    pywencai = import_pywencai()
    find_columns = normalize_find(args.find)

    kwargs = {
        "query": args.query,
        "query_type": args.query_type,
        "perpage": args.perpage,
        "page": args.page,
        "sort_key": args.sort_key,
        "sort_order": args.sort_order,
        "loop": args.loop,
        "cookie": args.cookie,
        "retry": args.retry,
    }
    if find_columns:
        kwargs["find"] = find_columns

    kwargs = {key: value for key, value in kwargs.items() if value not in (None, [], "")}

    try:
        result = pywencai.get(**kwargs)
    except Exception as exc:
        return fail(f"Wencai query failed: {exc}")

    payload = normalize_result(result)
    payload["query"] = args.query
    payload["query_type"] = args.query_type

    if args.out:
        output_path = save_output(args.out, payload)
        print(f"Saved full result to {output_path}")

    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Query: {args.query}")
    print(f"Query type: {args.query_type}")
    print(f"Result kind: {payload['kind']}")
    print(f"Row count: {payload['row_count']}")
    if payload["columns"]:
        print("Columns: " + ", ".join(payload["columns"]))
    if payload["records"]:
        print()
        print(markdown_table(payload["columns"], payload["records"], args.rows))
        if payload["row_count"] > args.rows:
            print()
            print(f"Preview truncated to first {args.rows} rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
