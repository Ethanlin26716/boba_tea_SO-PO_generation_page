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













document
.getElementById("generateBtn")
.addEventListener("click", async () => {


    const formData = new FormData();



    // -------------------------
    // Usage
    // -------------------------

    formData.append(

        "usage",

        document
        .getElementById("usage")
        .files[0]

    );

    // -------------------------
    // Current Inventory
    // -------------------------

    const inventoryFile = document
        .getElementById("inventory_currentM")
        .files[0];

    if (inventoryFile) {
        formData.append(
            "inventory_currentM",
            inventoryFile
        );
    }

    // -------------------------
    // next replenishment date
    // -------------------------

    formData.append(
        "replenishment_date",
        document.getElementById("replenishment_date").value
    );



    const response = await fetch(
        "/generate",
        {
            method:"POST",
            body:formData
        }

    );



    if(response.ok){


        const data =
            await response.json();



        if(data.status === "success"){

            document
            .getElementById("status")
            .innerHTML =
            "Success! PO generated.";

            // show buttons

            document
            .getElementById("downloadExcelBtn")
            .style.display =
            "block";

            document
            .getElementById("downloadJsonBtn")
            .style.display =
            "block";
        }



    }

    else{


        document
        .getElementById("status")
        .innerHTML =
        "Failed to generate PO.";

    }



});





// -------------------------
// Download Excel
// -------------------------

document
.getElementById("downloadExcelBtn")
.addEventListener(
"click",
()=>{


    window.location.href =
    "/download/PO_by_store.xlsx";


});

// -------------------------
// Download JSON
// -------------------------

document
.getElementById("downloadJsonBtn")
.addEventListener(
"click",
()=>{


    window.location.href =
    "/download/PO_result.json";


});