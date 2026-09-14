import numpy as np


def rolling_update_inventory(usage, start_month):
    usage = usage.copy()

    usage["Closing_Inventory"] = None

    months = sorted(
        usage["Usage_Month"].unique()
    )

    for month in months:

        if month < start_month:
            continue

        mask = usage["Usage_Month"] == month

        # -----------------------------
        # Purchase
        # -----------------------------
        usage.loc[mask, "Net_Requirement"] = (
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

        # -----------------------------
        # Closing Inventory
        # -----------------------------
        usage.loc[mask, "Closing_Inventory"] = (
            usage.loc[mask, "Opening_Inventory"]
            + usage.loc[mask, "Purchase_Amount"].fillna(0)
            - usage.loc[mask, "adjusted_usage"]
        )

        # 最后一个月不用往后传
        if month == months[-1]:
            continue

        next_month = months[
            months.index(month) + 1
        ]

        current_inventory = usage.loc[
            mask,
            [
                "Store",
                "Ingredient",
                "Closing_Inventory"
            ]
        ]

        for _, row in current_inventory.iterrows():

            next_mask = (
                (usage["Usage_Month"] == next_month)
                & (usage["Store"] == row["Store"])
                & (usage["Ingredient"] == row["Ingredient"])
            )

            usage.loc[
                next_mask,
                "Opening_Inventory"
            ] = row["Closing_Inventory"]

    return usage