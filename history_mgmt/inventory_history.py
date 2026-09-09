import pandas as pd
import os
import calendar
import numpy as np
from utils.data_loader import load_inventory_history, load_inventory, load_usage
from utils.data_saver import save_by_store_excel
from history_mgmt.history_manager import history_updater
from history_mgmt.inv_rolling import rolling_update_inventory
from history_mgmt.calibration import calibrate_opening_inventory


HISTORY_FOLDER = "history_data"

HISTORY_FILE = os.path.join(
    HISTORY_FOLDER,
    "inventory_history.xlsx"
)

USAGE_HISTORY = "history_data/usage_history.xlsx"
INVENTORY_HISTORY = "history_data/inventory_history.xlsx"
UPLOADED_INVENTORY = "uploads/restaurant_inventory.xlsx"


def update_inventory_history():

    # -----------------------------
    # Load inventory
    # -----------------------------
    inventory = load_inventory(UPLOADED_INVENTORY)

    # -----------------------------
    # Create history folder
    # -----------------------------
    os.makedirs(HISTORY_FOLDER, exist_ok=True)

    # -----------------------------
    # Read history if exists
    # -----------------------------
    history = load_inventory_history()
    if history is None:
        history = inventory.copy()

    history = history_updater(history, inventory, "inventory") 

    # -----------------------------
    # Save
    # -----------------------------
    save_by_store_excel(history, HISTORY_FILE)





def sync_inventory_usage():
    #usage = load_usage_history()
    usage = load_usage(USAGE_HISTORY)

    inventory = load_inventory(INVENTORY_HISTORY)
    
    
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

    usage_month_end = usage["Usage_End"].max()

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

    snapshot_month = latest_snapshot.to_period("M")

    if candidate_inventory.empty:

        print("No inventory snapshot available for current usage history.")
        return

    # ---------------------------
    # Calibration
    # ---------------------------
    usage = calibrate_opening_inventory(
        usage,
        latest_inventory,
        latest_snapshot
    )

    # ---------------------------------
    # Rolling updates
    # ---------------------------------
    usage = rolling_update_inventory(usage, snapshot_month)

    # ---------------------------------
    # Save
    # ---------------------------------
    save_by_store_excel(usage, USAGE_HISTORY)









