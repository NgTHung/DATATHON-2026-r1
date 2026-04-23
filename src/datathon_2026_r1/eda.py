from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
REPORT_TABLES_DIR = PROJECT_ROOT / "reports" / "tables"

TABLES: dict[str, Path] = {
    "sales": RAW_DATA_DIR / "analytical" / "sales.csv",
    "sample_submission": RAW_DATA_DIR / "analytical" / "sample_submission.csv",
    "customers": RAW_DATA_DIR / "master" / "customers.csv",
    "geography": RAW_DATA_DIR / "master" / "geography.csv",
    "products": RAW_DATA_DIR / "master" / "products.csv",
    "promotions": RAW_DATA_DIR / "master" / "promotions.csv",
    "inventory": RAW_DATA_DIR / "operational" / "inventory.csv",
    "web_traffic": RAW_DATA_DIR / "operational" / "web_traffic.csv",
    "order_items": RAW_DATA_DIR / "transaction" / "order_items.csv",
    "orders": RAW_DATA_DIR / "transaction" / "orders.csv",
    "payments": RAW_DATA_DIR / "transaction" / "payments.csv",
    "reviews": RAW_DATA_DIR / "transaction" / "reviews.csv",
    "returns": RAW_DATA_DIR / "transaction" / "returns.csv",
    "shipments": RAW_DATA_DIR / "transaction" / "shipments.csv",
}

DATE_COLUMNS: dict[str, list[str]] = {
    "reviews": ["review_date"],
    "sales": ["Date"],
    "web_traffic": ["date"],
    "customers": ["signup_date"],
    "inventory": ["snapshot_date"],
    "promotions": ["start_date", "end_date"],
    "sample_submission": ["Date"],
    "orders": ["order_date"],
    "returns": ["return_date"],
    "shipments": ["ship_date", "delivery_date"],
}

KEY_COLUMNS: dict[str, list[str]] = {
    "reviews": ["review_id"],
    "customers": ["customer_id"],
    "products": ["product_id"],
    "promotions": ["promo_id"],
    "orders": ["order_id"],
    "returns": ["return_id"],
}


def read_table(name: str, *, parse_dates: bool = True, **read_csv_kwargs) -> pd.DataFrame:
    """Read one named raw table."""
    if name not in TABLES:
        available = ", ".join(sorted(TABLES))
        raise KeyError(f"Unknown table {name!r}. Available tables: {available}")

    kwargs = dict(read_csv_kwargs)
    kwargs.setdefault("low_memory", False)
    if parse_dates and name in DATE_COLUMNS and "parse_dates" not in kwargs:
        kwargs["parse_dates"] = DATE_COLUMNS[name]
    return pd.read_csv(TABLES[name], **kwargs)


def load_all_tables(*, parse_dates: bool = True) -> dict[str, pd.DataFrame]:
    """Load every raw CSV into memory."""
    return {name: read_table(name, parse_dates=parse_dates) for name in TABLES}


def table_summary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return row, column, missingness, duplicate, and memory summaries."""
    records = []
    for name, df in tables.items():
        missing_cells = int(df.isna().sum().sum())
        total_cells = int(df.shape[0] * df.shape[1])
        records.append(
            {
                "table": name,
                "rows": len(df),
                "columns": len(df.columns),
                "missing_cells": missing_cells,
                "missing_pct": missing_cells / total_cells if total_cells else 0,
                "duplicate_rows": int(df.duplicated().sum()),
                "memory_mb": df.memory_usage(deep=True).sum() / 1_048_576,
            }
        )
    return pd.DataFrame(records).sort_values("rows", ascending=False).reset_index(drop=True)


def column_summary(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Return a compact data dictionary with dtype, null, and cardinality stats."""
    records = []
    for table_name, df in tables.items():
        for column in df.columns:
            series = df[column]
            records.append(
                {
                    "table": table_name,
                    "column": column,
                    "dtype": str(series.dtype),
                    "non_null": int(series.notna().sum()),
                    "missing": int(series.isna().sum()),
                    "missing_pct": float(series.isna().mean()),
                    "unique": int(series.nunique(dropna=True)),
                    "sample_values": ", ".join(map(str, series.dropna().head(3).tolist())),
                }
            )
    return pd.DataFrame(records)


def duplicate_key_report(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Check whether expected primary keys are duplicated."""
    records = []
    for table_name, keys in KEY_COLUMNS.items():
        df = tables[table_name]
        duplicate_count = int(df.duplicated(keys).sum())
        records.append(
            {
                "table": table_name,
                "key_columns": ", ".join(keys),
                "rows": len(df),
                "duplicate_key_rows": duplicate_count,
                "duplicate_key_pct": duplicate_count / len(df) if len(df) else 0,
            }
        )
    return pd.DataFrame(records)


def relationship_checks(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Check common foreign-key style links across the raw tables."""
    checks = [
        ("orders.customer_id", tables["orders"]["customer_id"], "customers.customer_id", tables["customers"]["customer_id"]),
        ("orders.zip", tables["orders"]["zip"], "geography.zip", tables["geography"]["zip"]),
        ("order_items.order_id", tables["order_items"]["order_id"], "orders.order_id", tables["orders"]["order_id"]),
        ("order_items.product_id", tables["order_items"]["product_id"], "products.product_id", tables["products"]["product_id"]),
        ("payments.order_id", tables["payments"]["order_id"], "orders.order_id", tables["orders"]["order_id"]),
        ("shipments.order_id", tables["shipments"]["order_id"], "orders.order_id", tables["orders"]["order_id"]),
        ("returns.order_id", tables["returns"]["order_id"], "orders.order_id", tables["orders"]["order_id"]),
        ("returns.product_id", tables["returns"]["product_id"], "products.product_id", tables["products"]["product_id"]),
        ("reviews.order_id", tables["reviews"]["order_id"], "orders.order_id", tables["orders"]["order_id"]),
        ("reviews.product_id", tables["reviews"]["product_id"], "products.product_id", tables["products"]["product_id"]),
        ("inventory.product_id", tables["inventory"]["product_id"], "products.product_id", tables["products"]["product_id"]),
    ]

    records = []
    for left_name, left_values, right_name, right_values in checks:
        missing = ~left_values.dropna().isin(right_values.dropna().unique())
        records.append(
            {
                "left": left_name,
                "right": right_name,
                "checked_rows": len(missing),
                "unmatched_rows": int(missing.sum()),
                "unmatched_pct": float(missing.mean()) if len(missing) else 0,
            }
        )
    return pd.DataFrame(records)


def date_coverage(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Summarize min/max dates for parsed date columns."""
    records = []
    for table_name, date_columns in DATE_COLUMNS.items():
        df = tables[table_name]
        for column in date_columns:
            if column not in df.columns:
                continue
            values = pd.to_datetime(df[column], errors="coerce")
            records.append(
                {
                    "table": table_name,
                    "date_column": column,
                    "min_date": values.min(),
                    "max_date": values.max(),
                    "missing_dates": int(values.isna().sum()),
                }
            )
    return pd.DataFrame(records)


def add_customer_cohort(customers: pd.DataFrame) -> pd.DataFrame:
    """Add a monthly signup cohort date to the customers table."""
    enriched = customers.copy()
    enriched["cohort_date"] = enriched["signup_date"].dt.to_period("M").dt.to_timestamp()
    return enriched


def customer_cohort_summary(customers: pd.DataFrame) -> pd.DataFrame:
    """Summarize new customers by monthly cohort and signup year."""
    enriched = add_customer_cohort(customers)
    cohort = (
        enriched.groupby("cohort_date", as_index=False)
        .agg(new_customers=("customer_id", "nunique"))
        .sort_values("cohort_date")
    )
    cohort["signup_year"] = cohort["cohort_date"].dt.year
    cohort["cumulative_customers"] = cohort["new_customers"].cumsum()
    return cohort


def acquisition_channel_nullness(customers: pd.DataFrame) -> pd.DataFrame:
    """Check nullness and blankness for customer acquisition channel."""
    channel = customers["acquisition_channel"]
    blank = channel.astype("string").str.strip().eq("").fillna(False)
    missing = channel.isna()
    return pd.DataFrame(
        [
            {
                "column": "acquisition_channel",
                "rows": len(customers),
                "missing_rows": int(missing.sum()),
                "blank_rows": int(blank.sum()),
                "missing_or_blank_rows": int((missing | blank).sum()),
                "missing_or_blank_pct": float((missing | blank).mean()),
                "unique_non_null_channels": int(channel.dropna().nunique()),
            }
        ]
    )


def build_order_revenue(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build order-level revenue and COGS from order items and products."""
    order_items = tables["order_items"]
    products = tables["products"]
    orders = tables["orders"]

    items = order_items.merge(products[["product_id", "category", "segment", "cogs"]], on="product_id", how="left")
    items["gross_item_value"] = items["quantity"] * items["unit_price"]
    items["net_item_value"] = items["gross_item_value"] - items["discount_amount"].fillna(0)
    items["item_cogs"] = items["quantity"] * items["cogs"]

    order_revenue = (
        items.groupby("order_id", as_index=False)
        .agg(
            items=("quantity", "sum"),
            gross_revenue=("gross_item_value", "sum"),
            discount=("discount_amount", "sum"),
            net_revenue=("net_item_value", "sum"),
            item_cogs=("item_cogs", "sum"),
        )
    )
    return orders.merge(order_revenue, on="order_id", how="left")


def revenue_seasonality(order_revenue: pd.DataFrame) -> pd.DataFrame:
    """Summarize revenue by calendar month to inspect seasonality."""
    seasonal = order_revenue.copy()
    seasonal["year"] = seasonal["order_date"].dt.year
    seasonal["month"] = seasonal["order_date"].dt.month
    seasonal["month_name"] = seasonal["order_date"].dt.month_name().str.slice(stop=3)

    by_month = (
        seasonal.groupby(["year", "month", "month_name"], as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            revenue=("net_revenue", "sum"),
            cogs=("item_cogs", "sum"),
        )
        .sort_values(["year", "month"])
    )
    by_month["gross_margin"] = by_month["revenue"] - by_month["cogs"]
    return by_month


def product_revenue_seasonality(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Summarize item-derived revenue by product group and calendar month."""
    items = tables["order_items"].merge(
        tables["orders"][["order_id", "order_date"]],
        on="order_id",
        how="left",
    )
    items = items.merge(
        tables["products"][["product_id", "category", "segment", "cogs"]],
        on="product_id",
        how="left",
    )
    items["net_item_value"] = items["quantity"] * items["unit_price"] - items["discount_amount"].fillna(0)
    items["item_cogs"] = items["quantity"] * items["cogs"]
    items["year"] = items["order_date"].dt.year
    items["month"] = items["order_date"].dt.month
    items["month_name"] = items["order_date"].dt.month_name().str.slice(stop=3)

    seasonal = (
        items.groupby(["year", "month", "month_name", "category", "segment"], as_index=False)
        .agg(
            quantity=("quantity", "sum"),
            revenue=("net_item_value", "sum"),
            cogs=("item_cogs", "sum"),
        )
        .sort_values(["year", "month", "category", "segment"])
    )
    seasonal["gross_margin"] = seasonal["revenue"] - seasonal["cogs"]
    return seasonal


def inventory_snapshot_coverage(inventory: pd.DataFrame) -> pd.DataFrame:
    """Check whether monthly inventory snapshots cover the observed product set."""
    observed_months = inventory["snapshot_date"].dt.to_period("M").dropna().sort_values().unique()
    if len(observed_months) == 0:
        return pd.DataFrame(
            columns=[
                "snapshot_month",
                "has_snapshot",
                "snapshot_dates",
                "product_month_rows",
                "unique_products",
                "duplicate_product_snapshot_rows",
            ]
        )

    full_months = pd.period_range(observed_months[0], observed_months[-1], freq="M")
    monthly = (
        inventory.assign(
            snapshot_month=inventory["snapshot_date"].dt.to_period("M").dt.to_timestamp(),
            duplicate_product_snapshot=inventory.duplicated(["product_id", "snapshot_date"]),
        )
        .groupby("snapshot_month", as_index=False)
        .agg(
            snapshot_dates=("snapshot_date", "nunique"),
            product_month_rows=("product_id", "size"),
            unique_products=("product_id", "nunique"),
            duplicate_product_snapshot_rows=("duplicate_product_snapshot", "sum"),
        )
    )
    coverage = pd.DataFrame({"snapshot_month": full_months.to_timestamp()})
    coverage = coverage.merge(monthly, on="snapshot_month", how="left")
    coverage["has_snapshot"] = coverage["product_month_rows"].notna()
    coverage[["snapshot_dates", "product_month_rows", "unique_products", "duplicate_product_snapshot_rows"]] = coverage[
        ["snapshot_dates", "product_month_rows", "unique_products", "duplicate_product_snapshot_rows"]
    ].fillna(0).astype(int)
    return coverage[
        [
            "snapshot_month",
            "has_snapshot",
            "snapshot_dates",
            "product_month_rows",
            "unique_products",
            "duplicate_product_snapshot_rows",
        ]
    ]


def inventory_status_summary(inventory: pd.DataFrame) -> pd.DataFrame:
    """Summarize monthly product-snapshot inventory operations metrics."""
    monthly = inventory.assign(snapshot_month=inventory["snapshot_date"].dt.to_period("M").dt.to_timestamp())
    summary = (
        monthly.groupby("snapshot_month", as_index=False)
        .agg(
            product_month_rows=("product_id", "size"),
            unique_products=("product_id", "nunique"),
            stockout_product_months=("stockout_flag", "sum"),
            overstock_product_months=("overstock_flag", "sum"),
            reorder_product_months=("reorder_flag", "sum"),
            total_stockout_days=("stockout_days", "sum"),
            avg_stockout_days=("stockout_days", "mean"),
            avg_fill_rate=("fill_rate", "mean"),
            median_fill_rate=("fill_rate", "median"),
            avg_days_of_supply=("days_of_supply", "mean"),
            median_days_of_supply=("days_of_supply", "median"),
            avg_sell_through_rate=("sell_through_rate", "mean"),
            avg_stock_on_hand=("stock_on_hand", "mean"),
            total_units_received=("units_received", "sum"),
            total_units_sold=("units_sold", "sum"),
        )
    )
    summary["stockout_product_month_rate"] = summary["stockout_product_months"] / summary["product_month_rows"]
    summary["overstock_product_month_rate"] = summary["overstock_product_months"] / summary["product_month_rows"]
    summary["reorder_product_month_rate"] = summary["reorder_product_months"] / summary["product_month_rows"]
    summary["stockout_days_per_product_month"] = summary["total_stockout_days"] / summary["product_month_rows"]
    return summary


def inventory_schema_quality_checks(inventory: pd.DataFrame, products: pd.DataFrame | None = None) -> pd.DataFrame:
    """Validate inventory against the documented monthly product-snapshot schema."""

    def record(check: str, invalid_mask: pd.Series, description: str) -> dict[str, object]:
        invalid_count = int(invalid_mask.fillna(True).sum())
        return {
            "check": check,
            "passed": invalid_count == 0,
            "rows_checked": int(len(invalid_mask)),
            "invalid_rows": invalid_count,
            "invalid_pct": float(invalid_count / len(invalid_mask)) if len(invalid_mask) else 0.0,
            "description": description,
        }

    records = [
        record(
            "snapshot_date_is_month_end",
            inventory["snapshot_date"] != inventory["snapshot_date"] + pd.offsets.MonthEnd(0),
            "Inventory snapshots should be end-of-month dates.",
        ),
        record(
            "year_matches_snapshot_date",
            inventory["year"] != inventory["snapshot_date"].dt.year,
            "Denormalized year should equal snapshot_date year.",
        ),
        record(
            "month_matches_snapshot_date",
            inventory["month"] != inventory["snapshot_date"].dt.month,
            "Denormalized month should equal snapshot_date month.",
        ),
        record(
            "unique_product_month_snapshot",
            inventory.duplicated(["product_id", "snapshot_date"]),
            "Schema expects one row per product per monthly snapshot.",
        ),
        record(
            "stockout_flag_matches_stockout_days",
            (inventory["stockout_flag"] == 1) != (inventory["stockout_days"] > 0),
            "stockout_flag should indicate whether any stockout days occurred in the month.",
        ),
        record(
            "stockout_days_within_month_length",
            (inventory["stockout_days"] < 0) | (inventory["stockout_days"] > inventory["snapshot_date"].dt.days_in_month),
            "stockout_days should be between 0 and the number of days in the snapshot month.",
        ),
        record(
            "fill_rate_between_0_and_1",
            ~inventory["fill_rate"].between(0, 1, inclusive="both"),
            "fill_rate should be a share between 0 and 1.",
        ),
        record(
            "sell_through_rate_between_0_and_1",
            ~inventory["sell_through_rate"].between(0, 1, inclusive="both"),
            "sell_through_rate should be a share between 0 and 1.",
        ),
        record(
            "nonnegative_quantity_metrics",
            (inventory[["stock_on_hand", "units_received", "units_sold", "days_of_supply"]] < 0).any(axis=1),
            "Inventory quantities and days_of_supply should be nonnegative.",
        ),
    ]

    if products is not None:
        product_attributes = products[["product_id", "product_name", "category", "segment"]]
        compared = inventory[["product_id", "product_name", "category", "segment"]].merge(
            product_attributes,
            on="product_id",
            how="left",
            suffixes=("_inventory", "_product"),
        )
        missing_product = compared["product_name_product"].isna()
        attribute_mismatch = missing_product
        for column in ["product_name", "category", "segment"]:
            attribute_mismatch |= compared[f"{column}_inventory"] != compared[f"{column}_product"]
        records.append(
            record(
                "product_attributes_match_products",
                attribute_mismatch,
                "Denormalized product_name, category, and segment should match products.csv.",
            )
        )

    return pd.DataFrame(records)


def inventory_stockout_units_sold_check(inventory: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible wrapper for the corrected inventory schema checks."""
    return inventory_schema_quality_checks(inventory)


def payment_revenue_proxy_check(order_revenue: pd.DataFrame, payments: pd.DataFrame) -> pd.DataFrame:
    """Compare payment value with item-derived revenue at order level."""
    payment_by_order = payments.groupby("order_id", as_index=False).agg(payment_value=("payment_value", "sum"))
    comparison = order_revenue[["order_id", "net_revenue", "gross_revenue"]].merge(payment_by_order, on="order_id", how="outer")
    comparison["payment_minus_net_revenue"] = comparison["payment_value"] - comparison["net_revenue"]
    comparison["payment_minus_gross_revenue"] = comparison["payment_value"] - comparison["gross_revenue"]
    return comparison


def payment_revenue_proxy_summary(order_revenue: pd.DataFrame, payments: pd.DataFrame, *, tolerance: float = 0.01) -> pd.DataFrame:
    """Summarize whether payment value can proxy item-derived net revenue."""
    comparison = payment_revenue_proxy_check(order_revenue, payments)
    complete = comparison[["payment_value", "net_revenue"]].dropna()
    differences = comparison["payment_minus_net_revenue"]
    return pd.DataFrame(
        [
            {
                "orders_compared": int(len(complete)),
                "corr_payment_net_revenue": float(complete["payment_value"].corr(complete["net_revenue"])),
                "exact_or_near_match_pct": float((differences.abs() <= tolerance).mean()),
                "mean_difference": float(differences.mean()),
                "median_difference": float(differences.median()),
                "max_abs_difference": float(differences.abs().max()),
            }
        ]
    )


def write_eda_reports(tables: dict[str, pd.DataFrame]) -> dict[str, Path]:
    """Write starter EDA tables to reports/tables and return their paths."""
    REPORT_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    customer_cohorts = customer_cohort_summary(tables["customers"])
    order_revenue = build_order_revenue(tables)
    seasonal_revenue = revenue_seasonality(order_revenue)
    seasonal_product_revenue = product_revenue_seasonality(tables)
    inventory_coverage = inventory_snapshot_coverage(tables["inventory"])
    inventory_status = inventory_status_summary(tables["inventory"])
    inventory_quality = inventory_schema_quality_checks(tables["inventory"], tables["products"])
    payment_proxy = payment_revenue_proxy_summary(order_revenue, tables["payments"])

    reports = {
        "eda_table_summary": table_summary(tables),
        "eda_column_summary": column_summary(tables),
        "eda_duplicate_key_report": duplicate_key_report(tables),
        "eda_relationship_checks": relationship_checks(tables),
        "eda_date_coverage": date_coverage(tables),
        "eda_customer_cohorts": customer_cohorts,
        "eda_acquisition_channel_nullness": acquisition_channel_nullness(tables["customers"]),
        "eda_revenue_seasonality": seasonal_revenue,
        "eda_product_revenue_seasonality": seasonal_product_revenue,
        "eda_inventory_snapshot_coverage": inventory_coverage,
        "eda_inventory_status_summary": inventory_status,
        "eda_inventory_schema_quality_checks": inventory_quality,
        "eda_payment_revenue_proxy": payment_proxy,
    }

    paths = {}
    for name, report in reports.items():
        path = REPORT_TABLES_DIR / f"{name}.csv"
        report.to_csv(path, index=False)
        paths[name] = path
    return paths
