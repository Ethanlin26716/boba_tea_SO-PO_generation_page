import pandas as pd


def history_updater(
    history,
    new_data,
    history_type
):

    if history_type == "inventory":

        key_columns = [
            "inv_snapshot_date",
            "Store",
            "Ingredient"
        ]

    elif history_type == "usage":

        key_columns = [
            "Usage Period",
            "Store",
            "Ingredient"
        ]

    else:
        raise ValueError(
            "Unsupported history type"
        )


    # -----------------------------
    # Remove old duplicated records
    # -----------------------------
    if history is not None and len(history) > 0:

        history = history.merge(
            new_data[key_columns],
            on=key_columns,
            how="left",
            indicator=True
        )

        history = history[
            history["_merge"] == "left_only"
        ].drop(
            columns="_merge"
        )

    else:

        history = new_data.iloc[0:0].copy()


    # -----------------------------
    # Append
    # -----------------------------
    history = pd.concat(
        [
            history,
            new_data
        ],
        ignore_index=True
    )


    # -----------------------------
    # Sort
    # -----------------------------
    history = history.sort_values(
        key_columns
    )


    return history


