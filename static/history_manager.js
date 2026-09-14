document
.getElementById("usage_history_update")
.addEventListener("click", async () => {

    const formData = new FormData();

    const usageHistory =
        document
        .getElementById("history_monthly_usage")
        .files[0];


    if (!usageHistory) {

        document
        .getElementById("status")
        .innerHTML =
        "Please select usage file.";

        return;
    }


    formData.append(
        "history_monthly_usage",
        usageHistory
    );


    const response = await fetch(
        "/update_usage_history",
        {
            method: "POST",
            body: formData
        }
    );


    const data = await response.json();


    document
    .getElementById("status")
    .innerHTML =
    data.message;

});

async function loadUsagePeriods() {

    const response = await fetch(
        "/usage_history_months"
    );

    const months = await response.json();

    const list =
        document.getElementById(
            "usage_history_months"
        );

    list.innerHTML = "";

    months.forEach(month => {

        const li =
            document.createElement("li");

        li.textContent = month;

        list.appendChild(li);

    });

}
loadUsagePeriods();


document
.getElementById("inventory_history_update")
.addEventListener("click", async () => {

    const formData = new FormData();


    const inventory =
        document.getElementById("restaurant_inventory").files[0];


    if (!inventory) {

        document
        .getElementById("status")
        .innerHTML =
        "Please select inventory file.";

        return;
    }

    formData.append(
        "restaurant_inventory",
        inventory
    );

    const response = await fetch(
        "/update_inventory_history",
        {
            method: "POST",
            body: formData
        }
    );


    const data = await response.json();


    document
    .getElementById("status")
    .innerHTML =
    data.message;

});



async function loadInventoryDates() {

    const response = await fetch(
        "/inventory_history_dates"
    );

    const data = await response.json();

    const list =
        document.getElementById(
            "inventory_history_dates"
        );

    list.innerHTML = "";

    data.forEach(row => {

        const li =
            document.createElement("li");

        li.textContent =
            `${row.inv_snapshot_date} — ${row.Store}`;

        list.appendChild(li);

    });
}

loadInventoryDates();











document
.getElementById("catalog_update")
.addEventListener("click", async () => {

    const formData = new FormData();

    const catalog =
        document
        .getElementById("catalog")
        .files[0];

    if (!catalog) {

        document
        .getElementById("status")
        .innerHTML =
        "Please select catalog file.";

        return;

    }

    formData.append(
        "catalog",
        catalog
    );

    const response = await fetch(
        "/upload_catalog",
        {
            method: "POST",
            body: formData
        }
    );

    const data = await response.json();

    document
    .getElementById("status")
    .innerHTML =
    data.message;

});
