#!/usr/bin/env python3
"""Validate the bundled dataset and build reproducible CSV and PNG artifacts."""

from __future__ import annotations

import argparse
import csv
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
FIGURE_DIR = OUTPUT_DIR / "figures"
DASHBOARD_PATH = ROOT / "dashboard" / "dashboard.png"
EVENT_TYPES = {"signup", "login", "view_product", "add_to_cart", "purchase"}
EXPECTED_USER_ROWS = 6000
EXPECTED_EVENT_ROWS = 19591
EXPECTED_EVENT_COUNTS = {
    "signup": 6000,
    "login": 5396,
    "view_product": 4320,
    "add_to_cart": 2577,
    "purchase": 1298,
}

NAVY = "#15243A"
INK = "#1D2B3A"
MUTED = "#66788A"
BLUE = "#3978C5"
BLUE_LIGHT = "#DCEBFA"
GREEN = "#17856B"
GREEN_LIGHT = "#DDF3EC"
PURPLE = "#7659B4"
PURPLE_LIGHT = "#EEE8FA"
AMBER = "#B77719"
AMBER_LIGHT = "#FFF1D7"
BACKGROUND = "#F3F6FA"
WHITE = "#FFFFFF"
LINE = "#E1E7EF"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.00"
    value = Decimal(numerator * 100) / Decimal(denominator)
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def load_data():
    for path in (
        DATA_DIR / "product_users_clean.csv",
        DATA_DIR / "product_events_clean.csv",
    ):
        if b"\r" in path.read_bytes():
            raise ValueError(
                f"{path.name} must use LF line endings; see .gitattributes and sql/01_load_data.sql"
            )
    users_rows = read_rows(DATA_DIR / "product_users_clean.csv")
    event_rows = read_rows(DATA_DIR / "product_events_clean.csv")
    users: dict[str, dict[str, object]] = {}
    events_by_user: dict[str, dict[str, list[date]]] = defaultdict(
        lambda: defaultdict(list)
    )
    event_counts: Counter[str] = Counter()

    for row in users_rows:
        user_id = row.get("user_id", "").strip()
        if not user_id or user_id in users:
            raise ValueError(f"Missing or duplicate user_id in users data: {user_id!r}")
        if not row.get("country", "").strip():
            raise ValueError(f"Missing country for user {user_id}")
        users[user_id] = {
            "signup_date": date.fromisoformat(row["signup_date"]),
            "country": row["country"].strip(),
        }

    for row in event_rows:
        user_id = row.get("user_id", "").strip()
        event_type = row.get("event_type", "").strip()
        if user_id not in users:
            raise ValueError(f"Event refers to unknown user_id {user_id!r}")
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unexpected event type {event_type!r}")
        event_date = date.fromisoformat(row["event_date"])
        if event_date < users[user_id]["signup_date"]:
            raise ValueError(f"Event occurs before signup for user {user_id}")
        events_by_user[user_id][event_type].append(event_date)
        event_counts[event_type] += 1

    if len(users_rows) != EXPECTED_USER_ROWS:
        raise ValueError(f"Expected {EXPECTED_USER_ROWS} users; found {len(users_rows)}")
    if len(event_rows) != EXPECTED_EVENT_ROWS:
        raise ValueError(f"Expected {EXPECTED_EVENT_ROWS} events; found {len(event_rows)}")
    if dict(event_counts) != EXPECTED_EVENT_COUNTS:
        raise ValueError(f"Unexpected event counts: {dict(event_counts)}")

    for user_id, user in users.items():
        signup_dates = events_by_user[user_id]["signup"]
        if not signup_dates:
            raise ValueError(f"User {user_id} has no signup event")
        if min(signup_dates) != user["signup_date"]:
            raise ValueError(f"Signup date mismatch for user {user_id}")

    for events in events_by_user.values():
        for event_type in events:
            events[event_type].sort()

    return users, events_by_user, event_counts


def earliest_on_or_after(candidates: list[date], boundary: date | None) -> date | None:
    if boundary is None:
        return None
    return next((candidate for candidate in candidates if candidate >= boundary), None)


def compute_results():
    users, events_by_user, event_counts = load_data()
    funnel_counts = [0, 0, 0, 0, 0]
    first_qualified_purchase: dict[str, date] = {}
    latest_event_date = max(
        event_date
        for events in events_by_user.values()
        for dates in events.values()
        for event_date in dates
    )
    stage_labels = [
        "1_signup",
        "2_login",
        "3_view_product",
        "4_add_to_cart",
        "5_purchase",
    ]
    stage_event_types = ["signup", "login", "view_product", "add_to_cart", "purchase"]

    for user_id, user in users.items():
        events = events_by_user[user_id]
        signup_date = min(events["signup"])
        login_date = earliest_on_or_after(events["login"], signup_date)
        view_date = earliest_on_or_after(events["view_product"], login_date)
        cart_date = earliest_on_or_after(events["add_to_cart"], view_date)
        purchase_date = earliest_on_or_after(events["purchase"], cart_date)
        valid_dates = [signup_date, login_date, view_date, cart_date, purchase_date]
        for index, stage_date in enumerate(valid_dates):
            if stage_date is not None:
                funnel_counts[index] += 1
        qualified_purchase = earliest_on_or_after(events["purchase"], signup_date)
        if qualified_purchase is not None:
            first_qualified_purchase[user_id] = qualified_purchase

    signups = funnel_counts[0]
    funnel_rows = []
    for index, (label, users_at_stage) in enumerate(zip(stage_labels, funnel_counts)):
        previous_users = "" if index == 0 else str(funnel_counts[index - 1])
        step_rate = "100.00" if index == 0 else pct(users_at_stage, funnel_counts[index - 1])
        cumulative_rate = pct(users_at_stage, signups)
        funnel_rows.append(
            [
                label,
                str(users_at_stage),
                previous_users,
                step_rate,
                cumulative_rate,
            ]
        )

    bucket_definitions = [
        ("0_Same_Day", lambda days: days == 0),
        ("1_Next_Day", lambda days: days == 1),
        ("2_Within_Week", lambda days: 2 <= days <= 7),
        ("3_More_Than_Week", lambda days: days > 7),
    ]
    elapsed_days = {
        user_id: (purchase_date - users[user_id]["signup_date"]).days
        for user_id, purchase_date in first_qualified_purchase.items()
    }
    observed_purchaser_count = len(elapsed_days)
    timing_rows = []
    for bucket, predicate in bucket_definitions:
        count = sum(predicate(days) for days in elapsed_days.values())
        timing_rows.append(
            [
                bucket,
                str(count),
                pct(count, observed_purchaser_count),
            ]
        )

    country_totals: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for user_id, user in users.items():
        country = str(user["country"])
        country_totals[country][0] += 1
        purchase_dates = events_by_user[user_id]["purchase"]
        if earliest_on_or_after(purchase_dates, user["signup_date"]) is not None:
            country_totals[country][1] += 1
    country_rows = [
        [
            country,
            str(total_users),
            str(purchases),
            pct(purchases, total_users),
        ]
        for country, (total_users, purchases) in sorted(
            country_totals.items(),
            key=lambda item: (
                -Decimal(pct(item[1][1], item[1][0])),
                item[0],
            ),
        )
    ]

    observation_cutoff = latest_event_date - timedelta(days=7)
    mature_users = {
        user_id: user
        for user_id, user in users.items()
        if user["signup_date"] <= observation_cutoff
    }
    mature_converters = sum(
        1
        for user_id, user in mature_users.items()
        if any(
            user["signup_date"] <= purchase_date <= user["signup_date"] + timedelta(days=7)
            for purchase_date in events_by_user[user_id]["purchase"]
        )
    )
    mature_rows = [
        [
            observation_cutoff.isoformat(),
            latest_event_date.isoformat(),
            "7",
            str(len(mature_users)),
            str(mature_converters),
            pct(mature_converters, len(mature_users)),
        ]
    ]

    tables = {
        "02_funnel_metrics.csv": (
            [
                "stage",
                "users",
                "previous_stage_users",
                "step_conversion_pct",
                "cumulative_conversion_pct",
            ],
            funnel_rows,
        ),
        "03_time_to_convert.csv": (
            [
                "time_bucket",
                "observed_purchasers",
                "percentage_of_observed_purchasers",
            ],
            timing_rows,
        ),
        "04_country_segmentation.csv": (
            ["country", "total_users", "valid_purchases", "conversion_rate_pct"],
            country_rows,
        ),
        "05_seven_day_conversion.csv": (
            [
                "signup_cutoff",
                "observed_through",
                "follow_up_days",
                "eligible_users",
                "purchasers_within_7_days",
                "conversion_rate_pct",
            ],
            mature_rows,
        ),
    }
    metrics = {
        "users": users,
        "events_by_user": events_by_user,
        "event_counts": event_counts,
        "latest_event_date": latest_event_date,
        "funnel_counts": funnel_counts,
        "timing_rows": timing_rows,
        "country_rows": country_rows,
        "mature_rows": mature_rows,
        "tables": tables,
    }
    return metrics


def write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def _font(size: int) -> ImageFont.ImageFont:
    return ImageFont.load_default(size=size)


def _text(draw: ImageDraw.ImageDraw, xy, value, size=20, fill=INK, anchor=None):
    draw.text(xy, str(value), font=_font(size), fill=fill, anchor=anchor)


def _panel(draw: ImageDraw.ImageDraw, box, title: str, subtitle: str | None = None):
    draw.rounded_rectangle(box, radius=18, fill=WHITE, outline=LINE, width=2)
    x1, y1, _, _ = box
    _text(draw, (x1 + 24, y1 + 20), title, 25, NAVY)
    if subtitle:
        _text(draw, (x1 + 24, y1 + 54), subtitle, 15, MUTED)


def _bar_chart(
    path: Path,
    title: str,
    subtitle: str,
    rows: list[tuple[str, int, str]],
    bar_color: str,
    footer: str,
    scale_max: int | None = None,
) -> None:
    image = Image.new("RGB", (1200, 700), BACKGROUND)
    draw = ImageDraw.Draw(image)
    _text(draw, (56, 42), title, 35, NAVY)
    _text(draw, (58, 94), subtitle, 18, MUTED)
    draw.rounded_rectangle((48, 142, 1152, 620), radius=18, fill=WHITE, outline=LINE, width=2)
    max_value = scale_max or max((row[1] for row in rows), default=1) or 1
    x0, max_width = 330, 670
    top = 188
    row_gap = 94
    for index, (label, value, right_label) in enumerate(rows):
        y = top + index * row_gap
        _text(draw, (74, y + 8), label, 19, INK)
        draw.rounded_rectangle(
            (x0, y, x0 + max_width, y + 34),
            radius=10,
            fill="#EDF1F6",
        )
        width = int(max_width * value / max_value) if value > 0 else 0
        if width:
            draw.rounded_rectangle(
                (x0, y, x0 + max(width, 12), y + 34),
                radius=10,
                fill=bar_color,
            )
        _text(draw, (x0 + max_width + 18, y + 5), right_label, 18, NAVY)
    _text(draw, (58, 646), footer, 16, MUTED)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)


def render_artifacts(metrics, output_root: Path) -> None:
    output_figures = output_root / "outputs" / "figures"
    dashboard_path = output_root / "dashboard" / "dashboard.png"
    funnel_counts = metrics["funnel_counts"]
    funnel_rows = []
    step_rows = []
    stage_names = [
        "Signup",
        "Login",
        "Product view",
        "Add to cart",
        "Purchase",
    ]
    for index, (label, count) in enumerate(zip(stage_names, funnel_counts)):
        cumulative = pct(count, funnel_counts[0])
        funnel_rows.append((label, count, f"{count:,} users  |  {cumulative}% of signups"))
        if index:
            step_rows.append(
                (
                    f"{stage_names[index - 1]} -> {label}",
                    int(Decimal(pct(count, funnel_counts[index - 1])) * 100),
                    f"{pct(count, funnel_counts[index - 1])}%",
                )
            )
    timing_labels = ["Same day", "Next day", "2-7 days", "Over 7 days"]
    timing_rows = [
        (label, int(row[1]), f"{row[2]}%  ({int(row[1]):,})")
        for label, row in zip(timing_labels, metrics["timing_rows"])
    ]
    _bar_chart(
        output_figures / "funnel_chart.png",
        "E-commerce funnel: users by stage",
        "A user advances only after the preceding stage; same-day order is assumed.",
        funnel_rows,
        BLUE,
        "Cumulative percentages use signups as the denominator.",
    )
    _bar_chart(
        output_figures / "dropoff_chart.png",
        "Step conversion by funnel transition",
        "Step conversion = users at the next stage divided by users at the prior stage.",
        step_rows,
        GREEN,
        "Largest observed percentage drop: add to cart -> purchase (49.63%).",
        scale_max=10000,
    )
    _bar_chart(
        output_figures / "time_to_convert.png",
        "Time to first purchase after signup",
        "Distribution among observed purchasers only; this is not a cohort conversion rate.",
        timing_rows,
        PURPLE,
        f"Events observed through {metrics['latest_event_date'].isoformat()}; recent cohorts have shorter follow-up.",
        scale_max=10000,
    )
    _render_dashboard(metrics, dashboard_path)


def _render_dashboard(metrics, path: Path) -> None:
    image = Image.new("RGB", (1440, 1080), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 1440, 170), fill=NAVY)
    _text(draw, (52, 38), "E-commerce funnel analytics", 38, WHITE)
    _text(draw, (54, 98), "User progression, observed purchase timing, and descriptive country rates", 18, "#D6E2F0")

    counts = metrics["funnel_counts"]
    mature = metrics["mature_rows"][0]
    kpis = [
        ("SIGNUPS", f"{counts[0]:,}", BLUE_LIGHT, BLUE),
        ("PURCHASES", f"{counts[-1]:,}", GREEN_LIGHT, GREEN),
        ("OVERALL CONVERSION", f"{pct(counts[-1], counts[0])}%", PURPLE_LIGHT, PURPLE),
        ("MATURE 7-DAY CONVERSION", f"{mature[5]}%", AMBER_LIGHT, AMBER),
    ]
    card_y = 200
    card_w, gap = 318, 25
    for index, (label, value, tint, accent) in enumerate(kpis):
        x = 48 + index * (card_w + gap)
        draw.rounded_rectangle((x, card_y, x + card_w, card_y + 120), radius=16, fill=WHITE, outline=LINE, width=2)
        draw.rounded_rectangle((x, card_y, x + 8, card_y + 120), radius=4, fill=accent)
        _text(draw, (x + 24, card_y + 20), label, 14, MUTED)
        _text(draw, (x + 24, card_y + 54), value, 32, accent)
        if label == "MATURE 7-DAY CONVERSION":
            _text(draw, (x + 24, card_y + 94), f"{mature[4]} of {mature[3]} users", 14, MUTED)

    left = (48, 350, 830, 710)
    right = (855, 350, 1392, 710)
    _panel(draw, left, "Funnel progression", "Counts and cumulative share of all signups")
    _panel(draw, right, "Observed purchase timing", "Share of purchasers with a recorded purchase")

    bar_x, bar_width = 255, 370
    max_count = max(counts)
    names = ["Signup", "Login", "Product view", "Add to cart", "Purchase"]
    for index, (name, count) in enumerate(zip(names, counts)):
        y = 435 + index * 48
        _text(draw, (74, y + 4), name, 17, INK)
        draw.rounded_rectangle((bar_x, y, bar_x + bar_width, y + 28), radius=8, fill="#EDF1F6")
        width = max(8, int(bar_width * count / max_count))
        draw.rounded_rectangle((bar_x, y, bar_x + width, y + 28), radius=8, fill=BLUE)
        _text(draw, (642, y + 4), f"{count:,}  ({pct(count, counts[0])}%)", 15, NAVY)
    _text(draw, (74, 678), "Largest step drop: add to cart -> purchase (49.63%).", 15, GREEN)

    times = metrics["timing_rows"]
    timing_names = ["Same day", "Next day", "2-7 days", "Over 7 days"]
    max_pct = max((Decimal(row[2]) for row in times), default=Decimal(1)) or Decimal(1)
    for index, (name, row) in enumerate(zip(timing_names, times)):
        y = 438 + index * 54
        value = Decimal(row[2])
        _text(draw, (880, y + 4), name, 16, INK)
        track_x, track_w = 1000, 245
        draw.rounded_rectangle((track_x, y, track_x + track_w, y + 28), radius=8, fill="#EDF1F6")
        width = int(track_w * value / max_pct) if value > 0 else 0
        if width:
            draw.rounded_rectangle((track_x, y, track_x + max(8, width), y + 28), radius=8, fill=PURPLE)
        _text(draw, (1260, y + 4), f"{row[2]}%  ({row[1]})", 14, NAVY)
    _text(draw, (880, 678), "Observed purchaser distribution; recent signups have", 13, MUTED)
    _text(draw, (880, 696), "less than seven days of follow-up.", 13, MUTED)

    country_box = (48, 735, 770, 1006)
    mature_box = (795, 735, 1392, 1006)
    _panel(draw, country_box, "Country conversion", "Descriptive account-level rates; no significance test")
    _panel(draw, mature_box, "Seven-day cohort measure", "Only users with a complete seven-day observation window")
    country_headers = [("Country", 74), ("Users", 344), ("Purchases", 455), ("Rate", 590)]
    for label, x in country_headers:
        _text(draw, (x, 808), label, 14, MUTED)
    for index, row in enumerate(metrics["country_rows"]):
        y = 841 + index * 25
        _text(draw, (74, y), row[0], 15, INK)
        _text(draw, (344, y), row[1], 15, INK)
        _text(draw, (455, y), row[2], 15, INK)
        _text(draw, (590, y), f"{row[3]}%", 15, NAVY)
    _text(draw, (824, 832), f"{mature[4]} / {mature[3]} users converted within seven days.", 18, NAVY)
    _text(draw, (824, 872), f"Eligible signups on or before {mature[0]}.", 15, MUTED)
    _text(draw, (824, 901), f"Events observed through {mature[1]}.", 15, MUTED)
    _text(draw, (824, 944), "Country gaps are descriptive and do not identify causes.", 14, MUTED)
    _text(draw, (824, 970), "The bundled dataset is date-only and appears synthetic.", 14, MUTED)

    draw.rectangle((0, 1032, 1440, 1080), fill="#E8EDF4")
    _text(
        draw,
        (48, 1045),
        "Same-day funnel order is assumed. No session, product, price, or experimental data is included.",
        14,
        MUTED,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)


def compare_csv(path: Path, headers: list[str], rows: list[list[str]]) -> bool:
    expected = [headers, *rows]
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            actual = list(csv.reader(handle))
    except FileNotFoundError:
        return False
    return actual == expected


def check_existing_images(metrics) -> None:
    with tempfile.TemporaryDirectory(prefix=".artifact-check-", dir=ROOT) as tmp:
        generated_root = Path(tmp)
        render_artifacts(metrics, generated_root)
        paths = [
            (generated_root / "outputs" / "figures" / name, FIGURE_DIR / name)
            for name in ("funnel_chart.png", "dropoff_chart.png", "time_to_convert.png")
        ]
        paths.append((generated_root / "dashboard" / "dashboard.png", DASHBOARD_PATH))
        for generated, tracked in paths:
            if not tracked.exists():
                raise ValueError(f"Missing generated image: {tracked.relative_to(ROOT)}")
            with Image.open(generated) as expected_image, Image.open(tracked) as actual_image:
                expected_image.load()
                actual_image.load()
                if expected_image.size != actual_image.size:
                    raise ValueError(
                        f"{tracked.relative_to(ROOT)} has size {actual_image.size}; "
                        f"expected {expected_image.size}"
                    )
                if ImageChops.difference(expected_image.convert("RGB"), actual_image.convert("RGB")).getbbox():
                    raise ValueError(
                        f"{tracked.relative_to(ROOT)} is stale; regenerate with "
                        "python scripts/build_artifacts.py"
                    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare tracked CSV and PNG artifacts with a fresh data-driven build",
    )
    args = parser.parse_args()
    try:
        metrics = compute_results()
        if args.check:
            for filename, (headers, rows) in metrics["tables"].items():
                path = OUTPUT_DIR / filename
                if not compare_csv(path, headers, rows):
                    raise ValueError(
                        f"{path.relative_to(ROOT)} is stale or malformed; "
                        "regenerate with python scripts/build_artifacts.py"
                    )
            check_existing_images(metrics)
            print("Dataset checks passed; tracked CSVs and PNGs match the reproducible build.")
        else:
            for filename, (headers, rows) in metrics["tables"].items():
                write_csv(OUTPUT_DIR / filename, headers, rows)
            render_artifacts(metrics, ROOT)
            print("Validated source data and regenerated CSV and PNG artifacts.")
        print(
            "Counts: users=6000, events=19591, stages="
            + "/".join(str(value) for value in metrics["funnel_counts"])
        )
        print(
            "Seven-day mature cohort: "
            f"{metrics['mature_rows'][0][4]}/{metrics['mature_rows'][0][3]} "
            f"({metrics['mature_rows'][0][5]}%)"
        )
    except (OSError, ValueError, KeyError, csv.Error) as exc:
        print(f"Artifact validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
