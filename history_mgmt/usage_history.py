import pandas as pd
import os
import calendar
from datetime import datetime
import re
from utils.standardizer import standardize_data, extract_english, CLEANED
from utils.data_loader import load_usage, load_catalog
from utils.data_saver import save_by_store_excel
from utils.format import validate_usage_period
from history_mgmt.history_manager import history_updater


HISTORY_FOLDER = "history_data"

HISTORY_FILE = os.path.join(
    HISTORY_FOLDER,
    "usage_history.xlsx"
)


def standardlize_history():

    # Combine file, standardlize data
    materialConsumption = load_usage("uploads/history_monthly_usage.xlsx")

    ingredientCatalog = load_catalog()

    merged = materialConsumption.merge(
        ingredientCatalog,
        left_on="rawMaterial_EN",
        right_on="Product",
        how="left"
    )


    # standardization
    merged = standardize_data(merged)

    merged = merged[CLEANED].copy()
   
    save_by_store_excel(merged, "history_data/usage_history-temp.xlsx")

def update_usage_history():
    usage = load_usage("history_data/usage_history-temp.xlsx")

    validate_usage_period(usage,period_type="history")

    # Read history
    if os.path.exists(HISTORY_FILE):
        history = load_usage(HISTORY_FILE)
    else:
        history = pd.DataFrame(columns=usage.columns)


    # Clean, Append, Sort
    history = history_updater(history, usage,"usage")

    history = history[history["门店名称"] != "Mascon"].copy()

    save_by_store_excel(history, HISTORY_FILE)



    
