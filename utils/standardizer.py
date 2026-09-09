import pandas as pd
import re


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



# --------------------------
# Cleaning
# --------------------------

CLEANED = [
"设备编号",
"门店名称",
"出料时间段",
"出料时间段天数",
"原料名称",
"rawMaterial_EN",
"原料代码",
"Shelf Life (months)",
"Price ($)",
"Package_Size_Base",
"adjusted_usage"]



def standardize_data(df):

    # -------------------------
    # Package Size
    # -------------------------
    df["Package_Size"] = (
        df["Order Unit"]
        .str.extract(r'(\d+\.?\d*)')
        .astype(float)
    )

    df["Package_Unit"] = (
        df["Order Unit"]
        .str.extract(r'([a-zA-Z]+)(?=/)')
    )

    df["Package_Size_Base"] = df.apply(
        convert_to_base,
        axis=1
    )

    # -------------------------
    # Tea Conversion
    # -------------------------
    df["adjusted_usage"] = pd.to_numeric(
        df["出料总量"],
        errors="coerce"
    ).astype(float)

    tea_mask = df["rawMaterial_EN"].str.contains(
        "Tea",
        case=False,
        na=False
    )

    df.loc[tea_mask, "adjusted_usage"] = (
        df.loc[tea_mask, "adjusted_usage"]
        * 60/ 2000
    )

    # -------------------------
    # Price
    # -------------------------
    df["Price ($)"] = (
        df["Price ($)"]
        .astype(str)
        .str.replace("$", "", regex=False)
    )

    df["Price ($)"] = pd.to_numeric(
        df["Price ($)"],
        errors="coerce"
    )

    return df