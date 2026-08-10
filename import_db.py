import json
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def import_to_db():

    # 1. Connect to PostgreSQL
    conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

    cursor = conn.cursor()

    # 2. Read JSON
    with open(
        "downloads/PO_result.json",
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    records = data["results"]["reorder_results"]

    # 3. Insert records
    for r in records:

        cursor.execute(
            """
            INSERT INTO reorder_results (
                restaurant_code,
                machine_code,
                consumption_period,
                ingredient_code,
                adjusted_usage,
                current_inventory,
                target_inventory,
                purchased_amount,
                inventory_end,
                recommended_quantity,
                recommended_price
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                r["restaurant_code"],
                r["machine_code"],
                r["period"],
                r["ingredient_code"],
                r["calculation_input"]["adjusted_usage"],
                r["calculation_input"]["current_inventory"],
                r["calculation_result"]["target_inventory"],
                r["calculation_result"]["purchased_amount"],
                r["calculation_result"]["inventory_end"],
                r["calculation_result"]["recommended_quantity"],
                r["calculation_result"]["recommended_price"],
            )
        )

    conn.commit()

    cursor.close()
    conn.close()

    print("Import completed.")

if __name__ == "__main__":
    import_to_db()