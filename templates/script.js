const submit = document.getElementById("submit");

submit.addEventListener("click", function (e) {
  e.preventDefault();

  const case_no = document.querySelector("#case_number").value;
  const year = document.querySelector("#case_year").value;
  const case_type = document.querySelector("#case_type").value;

  const formData = {
    case_no: case_no,
    case_type: case_type,
    year: year,
  };

  // const spinner = document.getElementById("spinner");
  spinner.classList.remove("hidden"); // Show spinner

  console.log("fetching data");

  fetch("http://127.0.0.1:5000/form", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  })
    .then((res) => res.json())
    .then((data) => {
      spinner.classList.add("hidden"); // Hide spinner

      const table = document.getElementById("resultsTable");
      const body = document.getElementById("resultsBody");
      const msg = document.getElementById("message");

      body.innerHTML = "";
      msg.innerText = "";

      if (!data || data.length === 0) {
        msg.innerText = "No case data found.";
        table.classList.add("hidden");
        return;
      }

      table.classList.remove("hidden");

      data.forEach((item) => {
        const row = document.createElement("tr");

        row.innerHTML = `
    <td class="border px-4 py-2">${item["case_title"] || "-"}</td>
    <td class="border px-4 py-2">${item["status"] || "-"}</td>
    <td class="border px-4 py-2">${item["petitioner"] || "-"}</td>
    <td class="border px-4 py-2">${item["respondent"] || "-"}</td>
    <td class="border px-4 py-2">${item["next_date"] || "-"}</td>
    <td class="border px-4 py-2">${item["last_date"] || "-"}</td>
    <td class="border px-4 py-2">${item["court_no"] || "-"}</td>
    <td class="border px-4 py-2">
      <button 
    class="view-btn bg-blue-500 hover:bg-blue-600 text-white text-sm px-3 py-1 rounded" 
    data-response-id="${item["response_id"]}">
    View
  </button>
    </td>
  `;
        body.appendChild(row);
      });

      document
        .getElementById("resultsBody")
        .addEventListener("click", function (e) {
          if (e.target && e.target.classList.contains("view-btn")) {
            const responseId = e.target.getAttribute("data-response-id");
            console.log(responseId);
            
            fetch("http://127.0.0.1:5000/order", {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify({ response_id: responseId }),
            })
              .then((res) => res.json())
              .then((orders) => {
                const orderTable = document.getElementById("orderTable");
                const orderBody = document.getElementById("orderTableBody");
                orderBody.innerHTML = "";

                if (orders.length === 0) {
                  orderTable.classList.add("hidden");
                  alert("No order details found for this case.");
                  return;
                }

                orders.forEach((order) => {
                  const row = document.createElement("tr");
                  row.innerHTML = `
            <td class="border px-4 py-2">${order["sr_no"]}</td>
            <td class="border px-4 py-2">
              ${
                order["order_link"]
                  ? `<a href="${order["order_link"]}" target="_blank" class="text-blue-600 underline">View</a>`
                  : "-"
              }
            </td>
            <td class="border px-4 py-2">${order["order_date"]}</td>
            <td class="border px-4 py-2">
              ${
                order["corrigendum_link"]
                  ? `<a href="${order["corrigendum_link"]}" target="_blank" class="text-blue-600 underline">View</a>`
                  : "-"
              }
            </td>
            <td class="border px-4 py-2">
              ${
                order["hindi_order"]
                  ? `<a href="${order["hindi_order"]}" target="_blank" class="text-blue-600 underline">View</a>`
                  : "-"
              }
            </td>
          `;
                  orderBody.appendChild(row);
                });

                orderTable.classList.remove("hidden");
              })
              .catch((err) => {
                console.error("Error fetching order details:", err);
                alert("An error occurred while fetching order details.");
              });
          }
        });
    })
    .catch((err) => {
      spinner.classList.add("hidden"); // Hide spinner
      console.error("Error fetching data:", err);
      document.getElementById("message").innerText =
        "An error occurred while searching.";
      document.getElementById("resultsTable").classList.add("hidden");
    });

  // const viewBtn = document.querySelectorAll("a");
  // viewBtn.addEventListener("click", function () {});
});
