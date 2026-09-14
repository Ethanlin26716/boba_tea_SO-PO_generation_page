import pandas as pd


def calibrate_opening_inventory(
    usage,
    latest_inventory,
    latest_snapshot
):
    # ---------------------------------
    # Current month usage
    # ---------------------------------
    usage_current_month = usage[
        (usage["Usage_Start"].dt.year == latest_snapshot.year)
        & (usage["Usage_Start"].dt.month == latest_snapshot.month)
    ].copy()

    if usage_current_month.empty:
        print("Current month usage not found.")
        return usage

    # ---------------------------------
    # Merge inventory snapshot
    # ---------------------------------
    usage_current_month = usage_current_month.merge(
        latest_inventory[
            [
                "Store",
                "Ingredient",
                "current_inventory",
                "inv_snapshot_date"
            ]
        ],
        on=[
            "Store",
            "Ingredient"
        ],
        how="left"
    )

    usage_current_month["current_inventory"] = pd.to_numeric(
        usage_current_month["current_inventory"],
        errors="coerce"
    )

    # ---------------------------------
    # Daily usage
    # ---------------------------------
    usage_current_month["daily_usage"] = (
        usage_current_month["adjusted_usage"]
        / usage_current_month["Usage Days"]
    )

    days_elapsed = latest_snapshot.day

    usage_current_month = usage_current_month[
        usage_current_month["current_inventory"].notna()
    ].copy()

    usage_current_month["Opening_Inventory"] = (
        usage_current_month["current_inventory"]
        * usage_current_month["Package_Size_Base"]
        + usage_current_month["daily_usage"]
        * days_elapsed
    )

    usage_current_month["Inventory_Status"] = "Calibrated"

    calibrated = usage_current_month[
        [
            "Store",
            "Ingredient",
            "Usage_Month",
            "Opening_Inventory",
            "Inventory_Status"
        ]
    ].copy()

    # ---------------------------------
    # Replace old calibration
    # ---------------------------------
    usage = usage.drop(
        columns=[
            "Opening_Inventory",
            "Purchase_Amount",
            "Closing_Inventory",
            "Inventory_Status"
        ],
        errors="ignore"
    )

    usage = usage.merge(
        calibrated,
        on=[
            "Store",
            "Ingredient",
            "Usage_Month"
        ],
        how="left"
    )

    return usage

    