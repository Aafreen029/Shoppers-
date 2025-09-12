$(document).ready(function () {
  console.log("quantity.js loaded and DOM ready");

  function updateCartCount() {
    $.ajax({
      url: "/get_cart_count/",
      type: "GET",
      dataType: "json",
      success: function (data) {
        $("#count").text(data.count);
      },
      error: function () {
        console.error("Error fetching cart count.");
      },
    });
  }

  updateCartCount();

  document.querySelectorAll(".quantity").forEach((quantityContainer, index) => {
    console.log(`Processing quantity block #${index}`);
    
    const minusBtn = quantityContainer.querySelector(".minus");
    const plusBtn = quantityContainer.querySelector(".plus");
    const inputBox = quantityContainer.querySelector(".input-box");
    const productId = quantityContainer.dataset.productId;

    const max = parseInt(inputBox.max) || 10;

    updateButtonStates();

    quantityContainer.addEventListener("click", handleButtonClick);

    function updateButtonStates() {
      const value = parseInt(inputBox.value);
      minusBtn.disabled = value <= 1;
      plusBtn.disabled = value >= max;
    }

    function handleButtonClick(event) {
      if (event.target.classList.contains("minus")) {
        updateQuantity("decrease");
      } else if (event.target.classList.contains("plus")) {
        updateQuantity("increase");
      }
    }

    function updateQuantity(action) {
      const csrftoken = getCookie("csrftoken");
      const sizeId = quantityContainer.dataset.sizeId;
      const colourId = quantityContainer.dataset.colourId;

      fetch(`/update_quantity/${productId}/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ 
          action,
          size_id: sizeId,
          colour_id: colourId
         }),
      })
        .then((response) => {
          if (!response.ok) throw new Error("Network error");
          return response.json();
        })
        .then((data) => {
          console.log(" Update response:", data);

          if (data.success) {
            inputBox.value = data.quantity;
            updateButtonStates();

            const itemTotal = quantityContainer.querySelector(".item-total");
            if (itemTotal) {
              itemTotal.textContent = data.item_total.toFixed(2);
            }

            document.querySelector("#total-price").textContent = data.total_price.toFixed(2);
            document.querySelector("#shipping_charge").textContent = data.shipping_charge.toFixed(2);
            document.querySelector("#grand-total").textContent = data.grand_total.toFixed(2);
          } else {
            alert(data.message || "Update failed.");
          }
        })
        .catch((error) => {
          console.error("AJAX error:", error);
        });
    }

    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
          const trimmed = cookie.trim();
          if (trimmed.startsWith(name + "=")) {
            cookieValue = decodeURIComponent(trimmed.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
  });
});
