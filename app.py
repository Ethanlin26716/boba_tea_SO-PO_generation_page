from flask import Flask, render_template, request, send_file, jsonify
from auto_PO import generate_po
import os
from history_manager.usage_history import update_usage_history, standardlize_history
from history_manager.inventory_history import update_inventory_history, sync_inventory_usage
import pandas as pd
#from history_manager.purchase_history import update_purchase_history

app = Flask(__name__)


UPLOAD_FOLDER = "uploads"
DOWNLOAD_FOLDER = "downloads"


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)



@app.route("/")
def index():

    return render_template("index.html")


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


@app.route("/upload_catalog", methods=["POST"])
def upload_catalog():

    catalog = request.files.get("catalog")

    catalog_path = os.path.join(
        "excel_templates",
        "Mascon_Ingredient_Catalog.xlsx"
    )

    if not catalog or catalog.filename == "":
        return jsonify({
            "status": "error",
            "message": "No catalog selected."
        }), 400

    try:
        df = pd.read_excel(catalog)

    except Exception as e:
        print(e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

    required_columns = [
        "Category",
        "Product",
        "Chinese",
        "Order Unit",
        "Shelf Life",
        "Price"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        return jsonify({
            "status": "error",
            "message":
                f"Missing columns: {', '.join(missing)}"
        }), 400

    # 文件已经被read了一遍，要回到开头
    catalog.seek(0)

    catalog.save(catalog_path)

    return jsonify({
        "status": "success",
        "message": "Catalog updated."
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


if __name__ == "__main__":

    app.run(debug=True)