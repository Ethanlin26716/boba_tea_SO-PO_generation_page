

let catalog = [];

let editing = false;

window.onload = loadCatalog;

// 在 loadCatalog 完成后确保渲染按钮
async function loadCatalog() {
    const response = await fetch("/catalog/data");
    catalog = await response.json();
    renderTable();
    renderButtons(); // 确保加载完数据后渲染按钮
}

// 优化 renderTable：在编辑状态下重新 addRow 时保留已有 input 的值
function renderTable() {
    const tbody = document.querySelector("#catalogTable tbody");

    // 如果处于编辑状态，先提取当前输入框里的最新值，防止 addRow() 重置已有输入
    if (editing && tbody.children.length > 0) {
        const trs = tbody.querySelectorAll("tr");
        trs.forEach((tr, index) => {
            const inputs = tr.querySelectorAll("input");
            if (inputs.length === 4 && catalog[index]) {
                catalog[index]["Ingredient"] = inputs[0].value;
                catalog[index]["Order Unit"] = inputs[1].value;
                catalog[index]["Price ($)"] = inputs[2].value;
                catalog[index]["Shelf Life (months)"] = inputs[3].value;
            }
        });
    }

    tbody.innerHTML = "";

    catalog.forEach((row) => {
        let tr = document.createElement("tr");
        if (editing) {
            tr.innerHTML = `
                <td><input value="${row.Ingredient ?? ''}"></td>
                <td><input value="${row["Order Unit"] ?? 0}"></td>
                <td><input value="${row["Price ($)"] ?? 0}"></td>
                <td><input value="${row["Shelf Life (months)"] ?? 0}"></td>
            `;
        } else {
            tr.innerHTML = `
                <td>${row.Ingredient ?? ''}</td>
                <td>${row["Order Unit"] ?? ''}</td>
                <td>${row["Price ($)"] ?? ''}</td>
                <td>${row["Shelf Life (months)"] ?? ''}</td>
            `;
        }
        tbody.appendChild(tr);
    });
}


function renderButtons(){

    const div=document.getElementById("buttonArea");

    if(editing){

        div.innerHTML=`

        <button onclick="addRow()">
        Add Ingredient
        </button>

        <button onclick="saveCatalog()">
        Save
        </button>

        <button onclick="cancelEdit()">
        Cancel
        </button>

        `;

    }

    else{

        div.innerHTML=`

        <button onclick="changeCatalog()">
        Change
        </button>

        <button onclick="resetCatalog()">
		Reset to Default
		</button>

        `;

    }

}


function changeCatalog(){

    editing=true;

    renderTable();
    renderButtons();
}

function cancelEdit(){

    editing=false;

    loadCatalog();

}

function addRow(){

    catalog.push({

        "Ingredient":"",

        "Order Unit":0,

        "Price ($)":0,

        "Shelf Life (months)":0

    });

    renderTable();

}

async function saveCatalog(){

    let rows=[];

    document.querySelectorAll("#catalogTable tbody tr").forEach(tr=>{

        let inputs=tr.querySelectorAll("input");

        rows.push({

            "Ingredient":inputs[0].value,

            "Order Unit":inputs[1].value,

            "Price ($)":inputs[2].value,

            "Shelf Life (months)":inputs[3].value

        });

    });

    await fetch(

        "/catalog/save",

        {

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify(rows)

        }

    );

    editing=false;

    loadCatalog();

}

async function resetCatalog(){

    if(
        !confirm(
            "Reset catalog to default?"
        )
    ){
        return;
    }


    await fetch(
        "/catalog/reset",
        {
            method:"POST"
        }
    );


    loadCatalog();

}




