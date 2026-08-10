import pandas as pd
import os
import calendar
from datetime import datetime
import re


HISTORY_FOLDER = "history_data"

HISTORY_FILE = os.path.join(
    HISTORY_FOLDER,
    "usage_history.xlsx"
)

def extract_english(text):

    text = str(text)

    english = re.sub(r'[\u4e00-\u9fff]', '', text)
    english = re.sub(r'\(.*?\)', '', english)
    english = re.sub(r'\s+', ' ', english).strip()

    return english if english else None


def convert_to_base(row):

    size = row["Package_Size"]
    unit = row["Package_Unit"]

    if unit == "kg":
        return size * 1000

    elif unit == "g":
        return size

    elif unit == "L":
        return size * 1000

    elif unit == "ml":
        return size

    elif unit == "pcs":
        return size

    return None


def standardlize_history():
    # -----------------------------
    # Combine file, standardlize data
    # -----------------------------
    materialConsumption = pd.read_excel("uploads/history_monthly_usage.xlsx")
    materialConsumption = materialConsumption[materialConsumption["门店名称"] != "Mascon"].copy()

    ingredientCatalog = pd.read_excel(
        "excel_templates/Mascon_Ingredient_Catalog.xlsx"
    )

    ingredientCatalog["Product_Match"] = (
        ingredientCatalog["Product"]
        .str.replace(r"\s*\(Selected\)", "", regex=True)
    )

    materialConsumption["rawMaterial_EN"] = (
        materialConsumption["原料名称"]
        .apply(extract_english)
    )

    merged = materialConsumption.merge(
        ingredientCatalog,
        left_on="rawMaterial_EN",
        right_on="Product_Match",
        how="left"
    )

    # -------------------------
    # Package Size
    # -------------------------
    merged["Package_Size"] = (
        merged["Order Unit"]
        .str.extract(r'(\d+\.?\d*)')
        .astype(float)
    )

    merged["Package_Unit"] = (
        merged["Order Unit"]
        .str.extract(r'([a-zA-Z]+)(?=/)')
    )

    merged["Package_Size_Base"] = merged.apply(
        convert_to_base,
        axis=1
    )

    # -------------------------
    # Tea Conversion
    # -------------------------
    merged["adjusted_usage"] = merged["出料总量"]

    tea_mask = merged["rawMaterial_EN"].str.contains(
        "Tea",
        case=False,
        na=False
    )

    usage = merged.copy()
    usage.loc[tea_mask, "adjusted_usage"] = (
        usage.loc[tea_mask, "出料总量"] * 60 / 2000
    )

    processed = usage.drop(
        columns=[
            'Category',
            'Product',
            'Order Unit',
            'Chinese',
            'Product_Match',
            'Package_Size',
            'Package_Unit'
        ]
    )

    
    processed.to_excel(
        "history_data/usage_history-temp.xlsx",
        index=False
    )




def update_usage_history():
    materialConsumption = pd.read_excel(
        "history_data/usage_history-temp.xlsx"
    )

    usage = materialConsumption.copy()
    # -----------------------------
    # analyse time period
    # -----------------------------
    period = usage["出料时间段"].iloc[0]

    start_str, end_str = [
        x.strip()
        for x in period.split("~")
    ]

    start_date = pd.to_datetime(start_str)
    end_date = pd.to_datetime(end_str)

    # -----------------------------
    # check if input time period is legal
    # -----------------------------
    if start_date.day != 1:
        raise ValueError(
            "Usage period must start on the first day of the month."
        )

    last_day = calendar.monthrange(
        end_date.year,
        end_date.month
    )[1]

    if end_date.day != last_day:
        raise ValueError(
            "Usage period must end on the last day of the month."
        )

    if (
        start_date.year != end_date.year
        or
        start_date.month != end_date.month
    ):
        raise ValueError(
            "Usage period must be within one calendar month."
        )

    # -----------------------------
    # Read history
    # -----------------------------
    if os.path.exists(HISTORY_FILE):

        history = pd.read_excel(HISTORY_FILE)

    else:

        history = pd.DataFrame(columns=usage.columns)


    # -----------------------------
    # Remove old records
    # -----------------------------
    history = history.merge(
        usage[
            [
                "设备编号",
                "出料时间段",
                "原料名称"
            ]
        ],
        on=[
            "设备编号",
            "出料时间段",
            "原料名称"
        ],
        how="left",
        indicator=True
    )

    history = history[
        history["_merge"] == "left_only"
    ].drop(columns="_merge")


    # -----------------------------
    # Append new records
    # -----------------------------
    history = pd.concat(
        [
            history,
            usage
        ],
        ignore_index=True
    )


    # -----------------------------
    # Sort
    # -----------------------------
    history = history.sort_values(
        [
            "出料时间段",
            "门店名称",
            "原料名称"
        ]
    )

    with pd.ExcelWriter(
        "history_data/usage_history.xlsx",
        engine="openpyxl"
    ) as writer:

        # 全部数据
        history.to_excel(
            writer,
            sheet_name="All",
            index=False
        )

        # 按门店名称分 Sheet
        for store, store_df in history.groupby("门店名称"):

            store_df.to_excel(
                writer,
                sheet_name=str(store)[:31],   # Excel sheet 名最长31个字符
                index=False
            )

    '''        
    history.to_excel(
        "history_data/usage_history.xlsx",
        index=False
    )
    '''


    
