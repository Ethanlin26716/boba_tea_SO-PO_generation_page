import pandas as pd
import json
from datetime import datetime


def save_by_store_excel(df, file_path):

    with pd.ExcelWriter(
        file_path,
        engine="openpyxl"
    ) as writer:

        # All data
        df.to_excel(
            writer,
            sheet_name="All",
            index=False
        )

        # Store sheets
        for store, store_df in df.groupby("门店名称"):

            store_df.to_excel(
                writer,
                sheet_name=str(store)[:31],
                index=False
            )





PO_OUTPUT_COLUMNS = [
    "设备编号",
    "门店名称",
    "出料时间段",
    "原料名称",
    "rawMaterial_EN",
    "原料代码",
    "Shelf Life (months)",
    "Price ($)",
    "Package_Size_Base",
    "adjusted_usage",
    "target_inventory",
    "Purchased_Amount",
    "month_start_inv",
    "inv_before_replenishment",
    "Inventory_After_PO",
    "replenishment_date",
    "Recommended_Quantity",
    "Recommended_Price"
]


def save_po_excel(store_output, file_path, hq_inventory=None):

    with pd.ExcelWriter(
        file_path,
        engine="openpyxl"
    ) as writer:

        for store, store_df in store_output.groupby("门店名称"):

            store_df.to_excel(
                writer,
                sheet_name=str(store)[:31],
                index=False
            )

        summary = (
            store_output
            .groupby("rawMaterial_EN", as_index=False)
            .agg({
                "Recommended_Quantity": "sum",
                "Price ($)": "first"
            })
        )

        if hq_inventory is not None:

            summary = summary.merge(
                hq_inventory,
                on="rawMaterial_EN",
                how="left"
            )

            summary["HQ_Inventory"] = (
                summary["HQ_Inventory"]
                .fillna(0)
            )

            summary["Final_PO"] = (
                summary["Recommended_Quantity"]
                - summary["HQ_Inventory"]
            ).clip(lower=0)

            summary["Final_PO_Price"] = (
                summary["Final_PO"]
                * summary["Price ($)"]
            )

        summary.to_excel(
            writer,
            sheet_name="Total",
            index=False
        )




def build_po_json(store_output, replenishment_date):

    json_output = {

        "input_contract_version": "1.0.0",

        "output_contract_version": "1.0.0",

        "calculation_engine_code":
            "INFINITEA_PO_ENGINE",

        "calculation_engine_version":
            "1.0.0",

        "generated_at":
            datetime.now().isoformat(),

        "replenishment_date":
            replenishment_date.strftime("%Y-%m-%d"),

        "run_status":
            "SUCCESS",

        "results": {

            "reorder_results": []

        },

        "errors": []

    }


    for _, row in store_output.iterrows():

        record = {

            "restaurant_code":
                row["门店名称"],

            "machine_code":
                row["设备编号"],

            "period":
                row["出料时间段"],

            "ingredient_name":
                row["原料名称"],


            "calculation_input": {

                "adjusted_usage":
                    float(row["adjusted_usage"]),

            },


            "Inventory Information": {

                "target_inventory":
                    float(row["target_inventory"]),

                "month_start_inv":
                    float(row["month_start_inv"]),

                "Inventory_After_PO":
                    float(row["Inventory_After_PO"]),

            },


            "replenish_result": {

                "target_inventory":
                    float(row["target_inventory"]),

                "purchased_amount":
                    float(row["Purchased_Amount"]),

                "Inventory_After_PO":
                    float(row["Inventory_After_PO"]),

                "recommended_quantity":
                    int(row["Recommended_Quantity"]),

                "recommended_price":
                    float(row["Recommended_Price"])

            },


            "package_info": {

                "package_size_base":
                    float(row["Package_Size_Base"]),

                "shelf_life (months)":
                    row["Shelf Life (months)"],

                "price ($)":
                    float(row["Price ($)"])

            }

        }


        json_output["results"]["reorder_results"].append(record)


    return json_output

def save_json(data, file_path):

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


