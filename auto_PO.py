import pandas as pd
import numpy as np
import re
import os
import json
from datetime import datetime
import calendar


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


def generate_po(replenishment_date):

    replenishment_date = datetime.strptime(
        replenishment_date,
        "%Y-%m-%d"
    )

    materialConsumption = pd.read_excel("uploads/usage.xlsx")
    materialConsumption = materialConsumption[materialConsumption["门店名称"] != "Mascon"].copy()

    catalog_path = (
        "uploads/catalog.xlsx"
        if os.path.exists("uploads/catalog.xlsx")
        else "excel_templates/Mascon_Ingredient_Catalog.xlsx"
    )

    ingredientCatalog = pd.read_excel(catalog_path)


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

    inventory_path = "uploads/inventory_currentM.xlsx"
    if os.path.exists(inventory_path):
        # if user uploaded the inventory file
        restaurant_inv = pd.read_excel(inventory_path)

    else:

        usage_history = pd.read_excel(
            "history_data/usage_history.xlsx",
            sheet_name="All"
        )

        usage_history["Usage_Month"] = (
            pd.to_datetime(
                usage_history["Usage_Month"]
            )
            .dt.to_period("M")
        )

        merged["Usage_Start"] = pd.to_datetime(
            merged["出料时间段"].str.split("~").str[0]
        )
        # 当前月份
        current_month = (
            merged["Usage_Start"]
            .iloc[0]
            .to_period("M")
        )

        # 上个月
        last_month = current_month - 1

        last_month_usage = usage_history[
            usage_history["Usage_Month"] == last_month
        ].copy()

        #check if last month history exist
        if last_month_usage.empty:
            raise ValueError(
                f"No usage history found for previous month ({last_month}). "
                "Please update usage history first."
            )

        #create an inv file with history data and snapshot date as Month.1st
        else:
            restaurant_inv = (
                last_month_usage[[
                        "门店名称",
                        "rawMaterial_EN",
                        "Closing_Inventory"
                    ]]
                .rename(
                    columns={"Closing_Inventory": "current_inventory"}
                )
            )

            restaurant_inv["inv_snapshot_date"] = (
                current_month.start_time
            )

    print(restaurant_inv.head())




    

    merged_inv = merged.merge(
        restaurant_inv,
        on=["门店名称", "rawMaterial_EN"],
        how="left"
    )

    # -------------------------
    # Package Size
    # -------------------------
    merged_inv["Package_Size"] = (
        merged_inv["Order Unit"]
        .str.extract(r'(\d+\.?\d*)')
        .astype(float)
    )

    merged_inv["Package_Unit"] = (
        merged_inv["Order Unit"]
        .str.extract(r'([a-zA-Z]+)(?=/)')
    )

    merged_inv["Package_Size_Base"] = merged_inv.apply(
        convert_to_base,
        axis=1
    )

    
    # -------------------------
    # inv standardlization
    # -------------------------
    merged_inv["Inventory_Note"] = ""

    merged_inv["current_inventory"] = pd.to_numeric(
        merged_inv["current_inventory"],
        errors="coerce"
    )

    merged_inv["current_inventory"] = merged_inv["current_inventory"] * merged_inv["Package_Size_Base"]

    merged_inv.loc[
        merged_inv["current_inventory"].isna(),
        "Inventory_Note"
    ] = "Invalid or missing inventory"


    # -------------------------
    # Tea Conversion
    # -------------------------
    merged_inv["adjusted_usage"] = merged_inv["出料总量"]

    tea_mask = merged_inv["rawMaterial_EN"].str.contains(
        "Tea",
        case=False,
        na=False
    )

    merged_inv.loc[tea_mask, "adjusted_usage"] = (
        merged_inv.loc[tea_mask, "出料总量"] * 60 / 2000
    )

    # -------------------------
    # Price
    # -------------------------
    merged_inv["Price"] = (
        merged_inv["Price"].str.replace("$", "", regex=False)
    )

    merged_inv["Price"] = pd.to_numeric(
        merged_inv["Price"],
        errors="coerce"
    )

    # ---------------------------
    # key dates
    # ---------------------------
    merged_inv["Usage_Start"] = pd.to_datetime(
        merged_inv["出料时间段"].str.split("~").str[0]
    )

    merged_inv["Usage_End"] = pd.to_datetime(
        merged_inv["出料时间段"].str.split("~").str[1]
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
        30 - merged_inv["出料时间段天数"]
    )

    #inv days 
    merged_inv["inv_snapshot_date"] = pd.to_datetime(
        merged_inv["inv_snapshot_date"]
        )

    merged_inv["snapshot_days"] = (
        merged_inv["inv_snapshot_date"].dt.day
    )

    # month start inventory
    merged_inv["month_start_inv"] = (
        merged_inv["current_inventory"] 
        + merged_inv["adjusted_usage"] 
        * merged_inv["snapshot_days"]
        / merged_inv["出料时间段天数"]
    )


    merged_inv["average_daily_usage"] = (
        merged_inv["adjusted_usage"] 
        / merged_inv["出料时间段天数"]
        )

    # when we need to replenish, how many inv left
    merged_inv["inv_before_replenishment"] = (
        merged_inv["current_inventory"] 
        - merged_inv["average_daily_usage"] 
        * merged_inv["days_to_replenishment"]
    )
    '''
    merged_inv = merged_inv[
        merged_inv["current_inventory"].notna()
    ]
    '''

    usage_history = pd.read_excel(
        "history_data/usage_history.xlsx",
        sheet_name="All"
    )

    usage_history["Usage_Month"] = (
        pd.to_datetime(
            usage_history["Usage_Month"]
        )
        .dt.to_period("M")
    )

    # 当前月份
    current_month = (
        merged_inv["Usage_Start"]
        .iloc[0]
        .to_period("M")
    )

    # 上个月
    last_month = current_month - 1

    last_month_usage = usage_history[
        usage_history["Usage_Month"] == last_month
    ].copy()

    #check if last month history exist
    if last_month_usage.empty:
        raise ValueError(
            f"No usage history found for previous month ({last_month}). "
            "Please update usage history first."
        )

    '''
    print(type(last_month))

    print(
        type(
            usage_history["Usage_Month"].iloc[0]
        )
    )

    print("current month:", current_month)
    print("last month:", last_month)

    print(
        usage_history["Usage_Month"].unique()
    )

    print("last month rows:", len(last_month_usage))
    print(last_month_usage.columns.tolist())
    print(last_month_usage.head())
    '''

    #merge上月用量
    merged_lastM = merged_inv.merge(

        last_month_usage[
            [
                "门店名称",
                "rawMaterial_EN",
                "adjusted_usage"
            ]
        ].rename(
            columns={
                "adjusted_usage": "Last_Month_Usage"
            }
        ),

        on=[
            "门店名称",
            "rawMaterial_EN"
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
        * merged_lastM["Price"]
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
    '''
    print(merged["门店名称"].unique())
    print(merged_inv["门店名称"].unique())
    print(merged_lastM["门店名称"].unique())
    '''
    #set for total
    all_store_df = []

    with pd.ExcelWriter(
        "downloads/PO_by_store.xlsx",
        engine="openpyxl"
    ) as writer:

        for store, store_df in merged_lastM.groupby("门店名称"):

            
            store_df = store_df.copy()

            output_columns = [
                "设备编号",
                "门店名称",
                "出料时间段",
                "原料名称",
                "原料代码",
                "Shelf Life",
                "Price",
                "Package_Size_Base",
                "adjusted_usage",
                "target_inventory",
                "Purchased_Amount",
                "month_start_inv",
                "Inventory_After_PO",
                "replenishment_date",
                "Recommended_Quantity",
                "Recommended_Price"
            ]
            store_output = store_df[output_columns]
            all_store_df.append(store_output)

            # -------------------------
            # Write one sheet
            # -------------------------
            sheet_name = str(store)[:31]      # Excel sheet名字最长31个字符

            store_output.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )

        all_store_df = pd.concat(all_store_df, ignore_index=True)
        summary = (
            all_store_df
            .groupby("原料名称", as_index=False)
            .agg({
                "Recommended_Quantity": "sum",
                "Recommended_Price": "sum"
            })
        )
        summary.to_excel(
            writer,
            sheet_name="Total",
            index=False
        )


























        '''
        # ============================
        # Generate JSON Output
        # ============================

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


        # convert dataframe to JSON records
        for _, row in all_store_df.iterrows():

            record = {

                "restaurant_code":
                    row["门店名称"],

                "machine_code":
                    row["设备编号"],

                "period":
                    row["出料时间段"],

                "ingredient_code":
                    row["原料代码"],

                "ingredient_name":
                    row["原料名称"],


                "calculation_input": {

                    "adjusted_usage":
                        float(row["adjusted_usage"]),

                    "inventory_snapshot":
                        float(row["Current_Inventory_Cleaned"]),

                    },


                "calculation_result": {

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

                    "shelf_life":
                        row["Shelf Life"],

                    "price":
                        float(row["Price"])

                },

            }


            json_output["results"]["reorder_results"].append(record)



        with open(
            "downloads/PO_result.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                json_output,
                f,
                indent=4,
                ensure_ascii=False
            )
        



        '''

    return "Success"
