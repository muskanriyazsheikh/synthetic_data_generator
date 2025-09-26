// Fetch dataset samples from backend
async function loadDatasets() {
  try {
    // Fetch real sample dataset
    const realRes = await fetch("http://127.0.0.1:5000/get-sample");
    const realData = await realRes.json();

    // Fetch synthetic dataset
    const synthRes = await fetch("http://127.0.0.1:5000/get-synthetic");
    const synthData = await synthRes.json();

    // ----- RENDER REAL DATASET TABLE -----
    const tableBody = document.getElementById("dataTable");
    tableBody.innerHTML = ""; // clear old rows

    realData.forEach((row, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${idx + 1}</td>
                      <td>${row.name || row.pregnancies}</td>
                      <td>${row.age || row.glucose}</td>
                      <td>${row.class || row.outcome}</td>`;
      tableBody.appendChild(tr);
    });

    // ----- CHARTS -----
    new Chart(document.getElementById("beforeChart"), {
      type: "bar",
      data: {
        labels: Object.keys(realData[0]),
        datasets: [{
          label: "Real Dataset",
          data: Object.values(realData[0]),
          backgroundColor: "#2563eb"
        }]
      }
    });

    new Chart(document.getElementById("afterChart"), {
      type: "bar",
      data: {
        labels: Object.keys(synthData[0]),
        datasets: [{
          label: "Synthetic Dataset",
          data: Object.values(synthData[0]),
          backgroundColor: "#16a34a"
        }]
      }
    });

  } catch (err) {
    console.error("Error loading datasets:", err);
  }
}

// Run on page load
window.onload = loadDatasets;
