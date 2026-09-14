from flask import Flask, render_template, request, send_file, jsonify
from auto_PO import generate_po
import os
from history_mgmt.usage_history import update_usage_history, standardlize_history
from history_mgmt.inventory_history import update_inventory_history, sync_inventory_usage
import pandas as pd
from utils.data_loader import load_catalog
#from history_mgmt.purchase_history import update_purchase_history
import numpy as np

app = Flask(__name__)


UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/history_manager")
def history_manager():

    return render_template(
        "history_manager.html"
    )
    
@app.route("/update_usage_history", methods=["POST"])
def update_usage_history_route():

    history_usage = request.files.get(
        "history_monthly_usage"
    )

    # -------------------------
    # Usage History
    # -------------------------

    if history_usage and history_usage.filename != "":

        history_usage_path = os.path.join(
            UPLOAD_FOLDER,
            "history_monthly_usage.xlsx"
        )

        history_usage.save(
            history_usage_path
        )

        standardlize_history()
        update_usage_history()

    return jsonify({
        "status": "success",
        "message": "Usage history updated"
    })

USAGE_HISTORY = "history_data/usage_history.xlsx"
@app.route("/usage_history_months")
def usage_history_months():

    usage = pd.read_excel(
        USAGE_HISTORY,
        sheet_name="All"
    )

    periods = (
        usage["Usage Period"]
        .drop_duplicates()
        .sort_values(ascending=False)
        .tolist()
    )

    return jsonify(periods)




@app.route("/update_inventory_history", methods=["POST"])
def update_inventory_history_route():

    restaurant_inventory = request.files.get(
        "restaurant_inventory"
    )

    # -------------------------
    # Inventory History
    # -------------------------

    if restaurant_inventory and restaurant_inventory.filename != "":

        inventory_path = os.path.join(
            UPLOAD_FOLDER,
            "restaurant_inventory.xlsx"
        )

        restaurant_inventory.save(
            inventory_path
        )

        update_inventory_history()
        sync_inventory_usage()

    return jsonify({
        "status": "success",
        "message": "Inventory history updated"
    })

INVENTORY_HISTORY = "history_data/inventory_history.xlsx"
@app.route("/inventory_history_dates")
def inventory_history_dates():

    inventory = pd.read_excel(
        INVENTORY_HISTORY
    )

    inventory["inv_snapshot_date"] = pd.to_datetime(
        inventory["inv_snapshot_date"]
    )

    recent_dates = (
        inventory["inv_snapshot_date"]
        .drop_duplicates()
        .nlargest(5)
    )

    recent = inventory[
        inventory["inv_snapshot_date"].isin(recent_dates)
    ].copy()

    recent = (
        recent
        .groupby("inv_snapshot_date")["Store"]
        .apply(lambda x: ", ".join(x.dropna().astype(str).unique()))
        .reset_index()
    )

    recent["inv_snapshot_date"] = (
        recent["inv_snapshot_date"]
        .dt.strftime("%Y-%m-%d")
    )

    return jsonify(
        recent.to_dict(orient="records")
    )




@app.route("/update_purchase_history", methods=["POST"])
def update_purchase_history_route():

    history_po = request.files.get("history_po")

    # -------------------------
    # Purchase History
    # -------------------------

    if history_po and history_po.filename != "":

        purchase_path = os.path.join(
            UPLOAD_FOLDER,
            "history_po.xlsx"
        )

        history_po.save(
            purchase_path
        )

        update_purchase_history(
            purchase_path
        )

    return jsonify({
        "status": "success",
        "message": "Purchase history updated"
    })




@app.route("/upload_hq_inventory", methods=["POST"])
def upload_hq_inventory():

    file = request.files["file"]

    save_path = "uploads/hq_inventory.xlsx"

    file.save(save_path)

    return jsonify({
        "message": "HQ inventory uploaded."
    })



@app.route("/generate", methods=["POST"])
def generate():

    usage = request.files.get("usage")
    inventory_currentM = request.files.get("inventory_currentM")

    # -------------------------
    # Save usage
    # -------------------------

    usage.save(
        os.path.join(
            UPLOAD_FOLDER,
            "usage.xlsx"
        )
    )

    # -------------------------
    # Save current inventory
    # -------------------------

    if inventory_currentM and inventory_currentM.filename != "":
        inventory_currentM.save(
            os.path.join(
                UPLOAD_FOLDER,
                "inventory_currentM.xlsx"
            )
        )
    
    # -------------------------
    # Save next replenish dates
    # -------------------------
    replenishment_date = request.form.get("replenishment_date")


    # -------------------------
    # Run calculation
    # -------------------------

    generate_po(replenishment_date)

    # -------------------------
    # Remove temp files
    # -------------------------
    for filename in [
        "usage.xlsx",
        "inventory_currentM.xlsx"
    ]:
        path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        if os.path.exists(path):
            os.remove(path)


    # -------------------------
    # Return status
    # -------------------------

    return jsonify({

        "status": "success",

        "files": [

            "PO_by_store.xlsx",

            "PO_result.json"

        ]

    })


@app.route("/download/<filename>")
def download(filename):

    return send_file(

        os.path.join(
            DOWNLOAD_FOLDER,
            filename
        ),

        as_attachment=True

    )








@app.route("/catalog")
def catalog():

    return render_template(
        "catalog.html"
    )

@app.route("/catalog/data")
def catalog_data():

    catalog = load_catalog()

    catalog = catalog.replace({np.nan: None})

    return jsonify(
        catalog.to_dict(orient="records")
    )

@app.route(
    "/catalog/save",
    methods=["POST"]
)
def save_catalog_route():

    data=request.json

    df=pd.DataFrame(data)

    save_catalog(df)

    return jsonify(
        {
            "status":"success"
        }
    )


CATALOG_FILE="history_data/catalog_master.xlsx"

def save_catalog(df):

    df.to_excel(

        CATALOG_FILE,

        index=False

    )


@app.route(
    "/catalog/reset",
    methods=["POST"]
)
def reset_catalog_route():

    reset_catalog()

    return jsonify(
        {
            "status": "success"
        }
    )

CATALOG_FILE = "history_data/catalog_master.xlsx"

DEFAULT_CATALOG = (
    "excel_templates/Mascon_Ingredient_Catalog.xlsx"
)


def reset_catalog():

    default = pd.read_excel(
        DEFAULT_CATALOG
    )


    default.to_excel(
        CATALOG_FILE,
        index=False
    )











if __name__ == "__main__":

    app.run(debug=True)