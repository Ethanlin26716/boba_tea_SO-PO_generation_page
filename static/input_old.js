// app.js

// 全局 Pyodide 对象
let pyodide = null;

// 页面加载完成
window.addEventListener("DOMContentLoaded", async () => {

    document.getElementById("status").textContent =
        "Loading Python environment...";

    // 初始化 Pyodide
    pyodide = await loadPyodide();

    // 安装需要的 package
    await pyodide.loadPackage([
        "numpy",
        "pandas",
        "micropip"
    ]);

    await pyodide.runPythonAsync(`
import micropip
await micropip.install("openpyxl")
`);

    document.getElementById("status").textContent =
        "Ready";

    // Generate 按钮
    document
        .getElementById("generateBtn")
        .addEventListener("click", runPython);

});


//====================================================
// 保存 Excel 到 Pyodide 文件系统
//====================================================

async function saveExcel(file, filename) {

    const buffer = await file.arrayBuffer();

    pyodide.FS.writeFile(
        filename,
        new Uint8Array(buffer)
    );

}


//====================================================
// 主程序
//====================================================

async function runPython() {

    // ---------- 取得文件 ----------

    const usageFile =
        document.getElementById("usage").files[0];

    const catalogFile =
        document.getElementById("catalog").files[0];

    const invRestFile =
        document.getElementById("inv_rest").files[0];

    const invHQFile =
        document.getElementById("inv_HQ").files[0];


    // ---------- 检查 ----------

    if (!usageFile) {
        alert("Please upload Usage file.");
        return;
    }

    if (!catalogFile) {
        alert("Please upload Catalog file.");
        return;
    }


    document.getElementById("status").textContent =
        "Uploading Excel files...";


    // ---------- 写入 Pyodide ----------

    await saveExcel(
        usageFile,
        "usage.xlsx"
    );

    await saveExcel(
        catalogFile,
        "catalog.xlsx"
    );

    if (invRestFile) {

        await saveExcel(
            invRestFile,
            "inv_rest.xlsx"
        );

    }

    if (invHQFile) {

        await saveExcel(
            invHQFile,
            "inv_HQ.xlsx"
        );

    }


    // ---------- Debug ----------

    console.log("Files inside Pyodide:");

    await pyodide.runPythonAsync(`
import os
print(os.listdir())
    `);


    document.getElementById("status").textContent =
        "Excel files loaded.";


    
    const workerCode =
        await fetch("auto_PO.py")
            .then(r => r.text());

    await pyodide.runPythonAsync(workerCode);


console.log(
    await pyodide.runPythonAsync(`
import os
print(os.listdir())
`)
);


// download

// download

console.log("JS FS files:");

console.log(
    pyodide.FS.readdir("/home/pyodide")
);

console.log(
    pyodide.FS.analyzePath("/home/pyodide/PO_by_store.xlsx")
);

const data = pyodide.FS.readFile(
    "/home/pyodide/PO_by_store.xlsx"
);

const blob = new Blob(
    [data],
    {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
);

const url = URL.createObjectURL(blob);

const a = document.createElement("a");

a.href = url;
a.download = "PO_by_store.xlsx";

document.body.appendChild(a);

a.click();

a.remove();

URL.revokeObjectURL(url);

}