// ----------------- LOGIN -----------------
async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  const response = await fetch("http://127.0.0.1:5000/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();
  console.log(data);

  if (data.status === "success") {
    alert("✅ Login successful");
    window.location.href = "index.html"; // redirect to home page
  } else {
    alert("❌ Invalid credentials");
  }
}

// ----------------- SYNTHETIC DATA GENERATION -----------------
document.getElementById("dataForm")?.addEventListener("submit", async function(event) {
  event.preventDefault();

  const rows = document.getElementById("rowsInput").value;

  const response = await fetch("http://127.0.0.1:5000/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rows: rows })
  });

  const result = await response.json();
  console.log(result);

  document.getElementById("responseMessage").innerText =
    `✅ Generated ${rows} rows of synthetic data. Check dataset page!`;
});
