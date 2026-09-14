import pandas as pd
import numpy as np
import re
import os
import json
from datetime import datetime
import calendar
from utils.standardizer import standardize_data
from utils.data_loader import load_usage, load_catalog, load_inventory, load_hq_inventory
from utils.data_saver import save_po_excel, save_json, build_po_json, PO_OUTPUT_COLUMNS
from utils.format import validate_usage_period


USAGE_HISTORY = "history_data/usage_history.xlsx"

def generate_po(replenishment_date):

    replenishment_date = datetime.strptime(
        replenishment_date,
        "%Y-%m-%d"
    )

    materialConsumption = load_usage("uploads/usage.xlsx")

    validate_usage_period(materialConsumption, period_type="current")


    ingredientCatalog = load_catalog()

    merged = materialConsumption.merge(
        ingredientCatalog,
        on="Ingredient",
        how="left"
    )

    # -----------------------------
    # Current / Last month
    # -----------------------------
    usage_history = load_usage(USAGE_HISTORY)

    usage_history["Usage_Month"] = (
        pd.to_datetime(
            usage_history["Usage_Month"]
        ).dt.to_period("M")
    )

    merged["Usage_Start"] = pd.to_datetime(
        merged["Usage Period"].str.split("~").str[0]
    )

    current_month = (
        merged["Usage_Start"]
        .iloc[0]
        .to_period("M")
    )

    last_month = current_month - 1

    last_month_usage = usage_history[
        usage_history["Usage_Month"] == last_month
    ].copy()

    if last_month_usage.empty:
        raise ValueError(
            f"No usage history found for previous month ({last_month}). "
            "Please update usage history first."
        )

    # -----------------------------
    # Inventory source
    # -----------------------------
    inventory_path = "uploads/inventory_currentM.xlsx"

    if os.path.exists(inventory_path):

        restaurant_inv = load_inventory(inventory_path)

        restaurant_inv = restaurant_inv.rename(
            columns={
                "current_inventory": "month_start_inv"
            }
        )

    else:

        restaurant_inv = (
            last_month_usage[
                [
                    "Store",
                    "Ingredient",
                    "Closing_Inventory"
                ]
            ]
            .rename(
                columns={
                    "Closing_Inventory": "month_start_inv"
                }
            )
        )

        restaurant_inv["inv_snapshot_date"] = (
            current_month.start_time
        )

    print(restaurant_inv.head())
    

    merged_inv = merged.merge(
        restaurant_inv,
        on=["Store", "Ingredient"],
        how="left"
    )

    # -------------------------
    # inv standardlization
    # -------------------------
    merged_inv["Inventory_Note"] = ""

    merged_inv["month_start_inv"] = pd.to_numeric(
        merged_inv["month_start_inv"],
        errors="coerce"
    )


    merged_inv.loc[
        merged_inv["month_start_inv"].isna(),
        "Inventory_Note"
    ] = "Invalid or missing inventory"

    # ---------------------------
    # standardlization
    # ---------------------------    
    merged_inv = standardize_data(merged_inv)


    # ---------------------------
    # key dates
    # ---------------------------
    merged_inv["Usage_Start"] = pd.to_datetime(
        merged_inv["Usage Period"].str.split("~").str[0]
    )

    merged_inv["Usage_End"] = pd.to_datetime(
        merged_inv["Usage Period"].str.split("~").str[1]
    )
    

    merged_inv["Month_Start"] = (
        merged_inv["Usage_Start"]
        .dt.to_period("M")
        .dt.start_time
    )

    #days until next replenishment
    merged_inv["days_to_replenishment"] = (
        replenishment_date
        - merged_inv["inv_snapshot_date"]
    ).dt.days

    #days of usage need to check last month
    merged_inv["last_month_usage_days"] = (
        30 - merged_inv["Usage Days"]
    )

    #inv days 
    merged_inv["inv_snapshot_date"] = pd.to_datetime(
        merged_inv["inv_snapshot_date"]
        )

    merged_inv["snapshot_days"] = (
        merged_inv["inv_snapshot_date"].dt.day
    )


    merged_inv["average_daily_usage"] = (
        merged_inv["adjusted_usage"] 
        / merged_inv["Usage Days"]
        )




    if os.path.exists(inventory_path):

        # 上传的是package
        merged_inv["month_start_inv"] *= merged_inv["Package_Size_Base"]

        # 回推月初
        merged_inv["days_elapsed"] = (
            merged_inv["inv_snapshot_date"]
            - merged_inv["Month_Start"]
        ).dt.days

        merged_inv["month_start_inv"] += (
            merged_inv["average_daily_usage"]
            * merged_inv["days_elapsed"]
        )



    # when we need to replenish, how many inv left
    merged_inv["inv_before_replenishment"] = (
        merged_inv["month_start_inv"] 
        - merged_inv["average_daily_usage"] 
        * merged_inv["days_to_replenishment"]
    )


    #merge上月用量
    merged_lastM = merged_inv.merge(

        last_month_usage[
            [
                "Store",
                "Ingredient",
                "adjusted_usage"
            ]
        ].rename(
            columns={
                "adjusted_usage": "Last_Month_Usage"
            }
        ),

        on=[
            "Store",
            "Ingredient"
        ],

        how="left"
    )

    #补货日-当月1号的天数
    merged_lastM["days_from_month_start"] = (
        replenishment_date
        - merged_lastM["Month_Start"]
    ).dt.days

    # ------------------------------
    # calculate PO with inventory
    # ------------------------------

    #target inventory

    merged_lastM["usage_30days"] = (

        merged_lastM["Last_Month_Usage"]
        * merged_lastM["last_month_usage_days"] / 30
        +
        merged_lastM["average_daily_usage"]
        * merged_lastM["days_from_month_start"]
    )

    merged_lastM["target_inventory"] = (
        merged_lastM["usage_30days"]
        * 1.5
    )
        

    merged_lastM["Net_Requirement"] = (
        merged_lastM["target_inventory"]
        - merged_lastM["inv_before_replenishment"]
    ).clip(lower=0)

    merged_lastM["Recommended_Quantity"] = np.ceil(
        merged_lastM["Net_Requirement"]
        / merged_lastM["Package_Size_Base"]
    )

    merged_lastM["Recommended_Price"] = (
        merged_lastM["Recommended_Quantity"]
        * merged_lastM["Price ($)"]
    )

    merged_lastM["Purchased_Amount"] = (
        merged_lastM["Recommended_Quantity"]
        * merged_lastM["Package_Size_Base"]
    )

    merged_lastM["Inventory_After_PO"] = (
        merged_lastM["inv_before_replenishment"]
        + merged_lastM["Purchased_Amount"]
        )

    merged_lastM = merged_lastM[merged_lastM["Recommended_Price"].notna()]

    merged_lastM["replenishment_date"] = replenishment_date.strftime("%Y-%m-%d")
    
    # -------------------------
    # Save_file
    # -------------------------

    store_output = merged_lastM[
        PO_OUTPUT_COLUMNS
    ].copy()

    hq_inv = load_hq_inventory()
    save_po_excel(
        store_output,
        "downloads/PO_by_store.xlsx",
        hq_inv
    )

    json_output = build_po_json(
        store_output,
        replenishment_date
    )

    save_json(
        json_output,
        "downloads/PO_result.json"
    )

    return "Success"
