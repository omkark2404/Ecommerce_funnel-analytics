#!/usr/bin/env python3
"""Compare MySQL query results with a validated reference build of the sample."""

from __future__ import annotations

import argparse
import csv
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

from build_artifacts import ROOT, compute_results


QUERY_FILES = (
    "02_funnel_metrics.sql",
    "03_time_to_convert.sql",
    "04_country_segmentation.sql",
    "05_seven_day_conversion.sql",
)


def mysql_command(mode: str) -> tuple[list[str], dict[str, str]]:
    env = os.environ.copy()
    if mode == "docker":
        if shutil.which("docker") is None:
            raise RuntimeError("Docker Compose is not installed or not available on PATH.")
        command = [
            "docker",
            "compose",
            "exec",
            "-T",
            "mysql",
            "sh",
            "-c",
            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --batch --raw --user=root ecommerce_analytics',
        ]
        return command, env

    mysql_client = shutil.which("mysql")
    if mysql_client is None:
        raise RuntimeError("The MySQL client is not installed or not available on PATH.")
    env["MYSQL_PWD"] = env.get("MYSQL_PWD", env.get("MYSQL_ROOT_PASSWORD", ""))
    if not env["MYSQL_PWD"]:
        raise ValueError("Set MYSQL_PWD (or MYSQL_ROOT_PASSWORD) before connecting to MySQL.")
    command = [
        mysql_client,
        "--batch",
        "--raw",
        "--host",
        env.get("MYSQL_HOST", "127.0.0.1"),
        "--port",
        env.get("MYSQL_PORT", "3306"),
        "--user",
        env.get("MYSQL_USER", "root"),
        "ecommerce_analytics",
    ]
    return command, env


def query_rows(command: list[str], env: dict[str, str], sql_text: str, label: str):
    result = subprocess.run(
        command,
        input=sql_text,
        text=True,
        encoding="utf-8",
        capture_output=True,
        env=env,
        timeout=90,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"MySQL failed for {label} (exit {result.returncode}):\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    rows = list(csv.reader(io.StringIO(result.stdout), delimiter="\t"))
    if not rows:
        raise RuntimeError(f"MySQL returned no rows for {label}")
    return [[("" if value in ("NULL", r"\N") else value) for value in row] for row in rows]


def validate_dataset_in_mysql(command: list[str], env: dict[str, str]) -> None:
    sql = """
USE ecommerce_analytics;
SELECT
    (SELECT COUNT(*) FROM users) AS user_rows,
    (SELECT COUNT(DISTINCT user_id) FROM users) AS unique_users,
    (SELECT COUNT(*) FROM events) AS event_rows,
    (SELECT COUNT(*) FROM events e LEFT JOIN users u ON u.user_id = e.user_id
        WHERE u.user_id IS NULL) AS orphan_events,
    (SELECT COUNT(*) FROM users u WHERE NOT EXISTS (
        SELECT 1 FROM events e
        WHERE e.user_id = u.user_id
          AND e.event_type = 'signup'
          AND e.event_date = u.signup_date
    )) AS signup_date_mismatches,
    (SELECT COUNT(*) FROM users WHERE RIGHT(country, 1) = CHAR(13))
        AS country_trailing_carriage_returns;
"""
    actual = query_rows(command, env, sql, "dataset integrity")
    expected = [
        [
            "user_rows",
            "unique_users",
            "event_rows",
            "orphan_events",
            "signup_date_mismatches",
            "country_trailing_carriage_returns",
        ],
        ["6000", "6000", "19591", "0", "0", "0"],
    ]
    if actual != expected:
        raise ValueError(
            "MySQL dataset integrity check failed.\n"
            f"Expected: {expected}\nActual:   {actual}"
        )
    print("MySQL dataset integrity: passed (6,000 users; 19,591 events; no bad links or CRs).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("host", "docker"),
        default="host",
        help="connect to a host MySQL client or use the local Docker Compose service",
    )
    args = parser.parse_args()
    try:
        metrics = compute_results()
        command, env = mysql_command(args.mode)
        validate_dataset_in_mysql(command, env)
        for filename in QUERY_FILES:
            sql_path = ROOT / "sql" / filename
            result = query_rows(command, env, sql_path.read_text(encoding="utf-8"), filename)
            headers, expected_data = metrics["tables"][filename.replace(".sql", ".csv")]
            expected = [headers, *expected_data]
            if result != expected:
                raise ValueError(
                    f"{filename} does not match the checked-in dataset.\n"
                    f"Expected: {expected}\nActual:   {result}"
                )
            print(f"{filename}: passed ({len(expected_data)} result rows).")
    except (OSError, ValueError, RuntimeError, csv.Error, subprocess.SubprocessError) as exc:
        print(f"Result validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
