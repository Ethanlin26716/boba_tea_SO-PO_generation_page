import os
import pandas as pd
from utils.standardizer import extract_english

USAGE_HISTORY = "history_data/usage_history.xlsx"
INVENTORY_HISTORY = "history_data/inventory_history.xlsx"

CATALOG_UPLOAD = "uploads/catalog.xlsx"
CATALOG_DEFAULT_TEMPLATE = "excel_templates/Mascon_Ingredient_Catalog.xlsx"

def load_usage(file_path):

    usage = pd.read_excel(file_path)

    usage = usage[usage["门店名称"] != "Mascon"].copy()

    usage["rawMaterial_EN"] = (
        usage["原料名称"]
        .apply(extract_english)
    )

    return usage


CATALOG_FILE = "history_data/catalog_master.xlsx"


def load_catalog():

    if os.path.exists(CATALOG_FILE):
        catalog = pd.read_excel(CATALOG_FILE)
    else:
        catalog = pd.read_excel(CATALOG_DEFAULT_TEMPLATE)
        catalog.to_excel(CATALOG_FILE,index=False)

    catalog["Product"] = (catalog["Product"].str.replace(r"\s*\(Selected\)","",regex=True)
    )

    return catalog


def load_inventory(file_path):
    inventory = pd.read_excel(file_path)

    # Convert snapshot date
    inventory["inv_snapshot_date"] = pd.to_datetime(
        inventory["inv_snapshot_date"]
    )
    return inventory


def load_inventory_history():
    INVENTORY_HISTORY = "history_data/inventory_history.xlsx"
    if (
        os.path.exists(INVENTORY_HISTORY)
        and os.path.getsize(INVENTORY_HISTORY) > 0
    ):

        return pd.read_excel(
            INVENTORY_HISTORY,
            sheet_name="All",
            engine="openpyxl"
        )

    return None

HQ_INVENTORY = "uploads/hq_inventory.xlsx"

def load_hq_inventory():

    if not os.path.exists(HQ_INVENTORY):
        return None

    return pd.read_excel(HQ_INVENTORY)
