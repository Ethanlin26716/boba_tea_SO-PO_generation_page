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

    // -------------------------
    // Current HQ Inventory
    // -------------------------

    const hqInventory = document
        .getElementById("hqInventory")
        .files[0];

    if (hqInventory) {
        formData.append(
            "hqInventory",
            hqInventory
        );
    }

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


document.addEventListener(
    "DOMContentLoaded",
    () => {
        loadUsagePeriods();
        loadInventoryDates();
    }
);


