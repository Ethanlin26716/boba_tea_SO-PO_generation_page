import pandas as pd
import os
import calendar
import numpy as np

HISTORY_FOLDER = "history_data"

HISTORY_FILE = os.path.join(
    HISTORY_FOLDER,
    "inventory_history.xlsx"
)


def update_inventory_history():

    # -----------------------------
    # Read uploaded inventory
    # -----------------------------
    inventory = pd.read_excel(
        "uploads/restaurant_inventory.xlsx"
    )

    # -----------------------------
    # Convert snapshot date
    # -----------------------------
    inventory["inv_snapshot_date"] = pd.to_datetime(
        inventory["inv_snapshot_date"]
    )

    # -----------------------------
    # Create history folder
    # -----------------------------
    os.makedirs(
        HISTORY_FOLDER,
        exist_ok=True
    )

    # -----------------------------
    # Read history if exists
    # -----------------------------

    if (
        os.path.exists(HISTORY_FILE)
        and os.path.getsize(HISTORY_FILE) > 0
    ):

        history = pd.read_excel(
            HISTORY_FILE,
            sheet_name="All",
            engine="openpyxl"
        )

    else:

        history = inventory.copy()


    # -----------------------------
    # Remove old same records
    # -----------------------------

    if len(history) > 0:

        history = history.merge(
            inventory[
                [
                    "inv_snapshot_date",
                    "门店名称",
                    "rawMaterial_EN"
                ]
            ],
            on=[
                "inv_snapshot_date",
                "门店名称",
                "rawMaterial_EN"
            ],
            how="left",
            indicator=True
        )

        history = history[
            history["_merge"] == "left_only"
        ].drop(
            columns="_merge"
        )


    # -----------------------------
    # Append new inventory
    # -----------------------------
    history = pd.concat(
        [
            history,
            inventory
        ],
        ignore_index=True
    )

    # -----------------------------
    # Sort
    # -----------------------------
    history = history.sort_values(
        [
            "inv_snapshot_date",
            "门店名称",
            "rawMaterial_EN"
        ]
    )

    # -----------------------------
    # Save
    # -----------------------------
    with pd.ExcelWriter(
        HISTORY_FILE,
        engine="openpyxl"
    ) as writer:

        history.to_excel(
            writer,
            sheet_name="All",
            index=False
        )

        for store, store_df in history.groupby("门店名称"):

            store_df.to_excel(
                writer,
                sheet_name=str(store)[:31],
                index=False
            )









USAGE_HISTORY = "history_data/usage_history.xlsx"
INVENTORY_HISTORY = "history_data/inventory_history.xlsx"

def sync_inventory_usage():
    usage = pd.read_excel(
        USAGE_HISTORY,
        sheet_name="All"
    )

    inventory = pd.read_excel(
        INVENTORY_HISTORY,
    )

    inventory["inv_snapshot_date"] = pd.to_datetime(
        inventory["inv_snapshot_date"]
    )
    
    # ---------------------------------
    # Match latest snapshot with month
    # ---------------------------------

    #Find latest usage month
    usage["Usage_Start"] = pd.to_datetime(
        usage["出料时间段"]
        .str.split("~")
        .str[0]
    )

    #Find the larget date of current dataset stored
    usage["Usage_End"] = pd.to_datetime(
        usage["出料时间段"]
        .str.split("~")
        .str[1]
    )
    usage_month_end = usage[
        "Usage_End"
    ].max()

    # find the month for matching
    usage["Usage_Month"] = (
        usage["Usage_Start"]
        .dt.to_period("M")
    )

    candidate_inventory = inventory[
        inventory["inv_snapshot_date"]
        <= usage_month_end
    ].copy()

    latest_snapshot = candidate_inventory[
        "inv_snapshot_date"
    ].max()

    latest_inventory = candidate_inventory[
        candidate_inventory["inv_snapshot_date"]
        == latest_snapshot
    ].copy()

    print(candidate_inventory.empty)
    print(latest_snapshot)
    print(usage["Usage_Month"].unique())

    if candidate_inventory.empty:

        print("No inventory snapshot available for current usage history.")
        return

    #matching month period
    snapshot_month = latest_snapshot.to_period("M")

    # ---------------------------------
    # if no matched month
    # ---------------------------------

    usage_current_month = usage[
        (usage["Usage_Start"].dt.year == latest_snapshot.year)
        & (usage["Usage_Start"].dt.month == latest_snapshot.month)
    ].copy()

    if usage_current_month.empty:
        print("Current month usage not found.")
        return

    #connect it to usage history dataset
    usage_current_month = usage_current_month.merge(

        latest_inventory[
            [
                "门店名称",
                "rawMaterial_EN",
                "current_inventory",
                "inv_snapshot_date"
            ]
        ],
        on=[
            "门店名称",
            "rawMaterial_EN"
        ],

        how="left"
    )

    usage_current_month["current_inventory"] = pd.to_numeric(
        usage_current_month["current_inventory"],
        errors="coerce"
    )

    #Average daily usage
    usage_current_month["daily_usage"] = (
        usage_current_month["adjusted_usage"]
        / usage_current_month["出料时间段天数"]
    )

    #how many days it consumed in this month before inventory count
    days_elapsed = latest_snapshot.day

    # 只保留有库存数据的
    usage_current_month_rest = usage_current_month[
        usage_current_month["current_inventory"].notna()
    ].copy()


    usage_current_month_rest["Opening_Inventory"] = (
        usage_current_month_rest["current_inventory"]
        * usage_current_month_rest["Package_Size_Base"]
        + usage_current_month_rest["daily_usage"]
        * days_elapsed
    )

    usage_current_month_rest[
        "Inventory_Status"
    ] = "Calibrated"

    '''
    # ---------------------------------
    # Estimate Purchase
    # ---------------------------------

    usage_current_month_rest["Net_Requirement"] = (
        usage_current_month_rest["adjusted_usage"] * 1.5
        - usage_current_month_rest["Opening_Inventory"]
    ).clip(lower=0)

    usage_current_month_rest["Purchase_Quantity"] = np.ceil(
        usage_current_month_rest["Net_Requirement"]
        / usage_current_month_rest["Package_Size_Base"]
    )

    usage_current_month_rest["Purchase_Amount"] = (
        usage_current_month_rest["Purchase_Quantity"]
        * usage_current_month_rest["Package_Size_Base"]
    )
    
    usage_current_month_rest["Closing_Inventory"] = (
        usage_current_month_rest["Opening_Inventory"]
        + usage_current_month_rest["Purchase_Amount"]
        - usage_current_month_rest["adjusted_usage"]
    )
    '''

    # ---------------------------------
    # Update previous month's record
    # ---------------------------------

    calibrated = usage_current_month_rest[
        [
            "门店名称",
            "rawMaterial_EN",
            "Usage_Month",
            "Opening_Inventory",
            "Purchase_Amount",
            "Closing_Inventory",
            "Inventory_Status"
        ]
    ].copy()
    


    # ---------------------------------
    # Remove old calibration columns
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


    # ---------------------------------
    # Write new calibration result
    # ---------------------------------

    usage = usage.merge(

        calibrated,

        on=[
            "门店名称",
            "rawMaterial_EN",
            "Usage_Month"
        ],

        how="left"

    )

    # ---------------------------------
    # rolling update later monthes
    # ---------------------------------

    # Creating Closing_Inventory column
    usage["Closing_Inventory"] = None

    months = sorted(
        usage["Usage_Month"].unique()
    )

    for month in months:
        if month < snapshot_month:
            continue

        current = usage[usage["Usage_Month"] == month]

        mask = (usage["Usage_Month"] == month)


        # calculate purchase
        usage.loc[mask,"Net_Requirement"] = (
            usage.loc[mask, "adjusted_usage"] * 1.5
            - usage.loc[mask, "Opening_Inventory"]
        ).clip(lower=0)


        usage.loc[mask, "Purchase_Quantity"] = np.ceil(
            usage.loc[mask, "Net_Requirement"]
            / usage.loc[mask, "Package_Size_Base"]
        )


        usage.loc[mask, "Purchase_Amount"] = (
            usage.loc[mask, "Purchase_Quantity"]
            * usage.loc[mask, "Package_Size_Base"]
        )

        # calculate closing every month
        usage.loc[mask, "Closing_Inventory"] = (
            usage.loc[mask, "Opening_Inventory"]
            + usage.loc[mask, "Purchase_Amount"].fillna(0)
            - usage.loc[mask, "adjusted_usage"]
        )

        if month == months[-1]:
            break

        next_month = months[
            months.index(month)+1
        ]

        # give closing to next month
        current_inventory = usage.loc[
            mask,
            [
                "门店名称",
                "rawMaterial_EN",
                "Closing_Inventory"
            ]
        ]

        for _, row in current_inventory.iterrows():

            next_mask = (

                (usage["Usage_Month"] == next_month)
                &(usage["门店名称"] == row["门店名称"])
                &(usage["rawMaterial_EN"] == row["rawMaterial_EN"])
            )

            usage.loc[
                next_mask,
                "Opening_Inventory"
            ] = row["Closing_Inventory"]

    # ---------------------------------
    # Save
    # ---------------------------------

    with pd.ExcelWriter(
        USAGE_HISTORY,
        engine="openpyxl"
    ) as writer:

        usage.to_excel(
            writer,
            sheet_name="All",
            index=False
        )

        for store, store_df in usage.groupby("门店名称"):

            store_df.to_excel(
                writer,
                sheet_name=str(store)[:31],
                index=False
            )









