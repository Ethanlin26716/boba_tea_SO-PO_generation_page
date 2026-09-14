from datetime import datetime
import pandas as pd
import calendar


def validate_usage_period(df, period_type="current"):

    period = df["Usage Period"].iloc[0]

    start_str, end_str = [
        x.strip()
        for x in period.split("~")
    ]

    start_date = pd.to_datetime(start_str)
    end_date = pd.to_datetime(end_str)


    # -------------------------
    # Common rule
    # -------------------------

    if start_date.day != 1:
        raise ValueError(
            "Usage period must start on the first day of the month."
        )


    # -------------------------
    # History only
    # -------------------------

    if period_type == "history":

        last_day = calendar.monthrange(
            end_date.year,
            end_date.month
        )[1]

        if start_date.day != 1:
            raise ValueError(
                "Usage period must start on the first day of the month."
            )


        if end_date.day != last_day:
            raise ValueError(
                "History usage period must end on the last day of the month."
            )


        if (
            start_date.year != end_date.year
            or
            start_date.month != end_date.month
        ):
            raise ValueError(
                "History usage period must be within one calendar month."
            )


    return True
