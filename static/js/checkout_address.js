
document.addEventListener('DOMContentLoaded', function () {
  const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

  // Handle radio button (set default) change
  document.querySelectorAll('.set-default-address').forEach(radio => {
    radio.addEventListener('change', function () {
      const addressId = this.dataset.addressId;

      fetch(`/checkout/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest"
        },
        body: new URLSearchParams({
          set_default: "true",
          address_id: addressId
        })
      })
      .then(response => {
        if (!response.ok) throw new Error("Request failed");

        // Hide all address blocks except the selected one
        document.querySelectorAll('.address-block').forEach(block => {
          if (block.querySelector('.set-default-address').dataset.addressId === addressId) {
            block.style.display = '';
            block.querySelector('label.form-check-label').textContent = "Default Address";
            block.querySelector('.set-default-address').checked = true;
          } else {
            block.style.display = 'none';
          }
        });
      })
      .catch(error => {
        console.error("Error:", error);
      });
    });
  });

  // Handle "Change Address" button
  const changeBtn = document.querySelector('form button[type="submit"].btn-outline-dark:nth-of-type(2)');
  if (changeBtn) {
    changeBtn.addEventListener('click', function (e) {
      // This lets the server show all addresses again on POST
      // But we also show them immediately for smoother UX
      document.querySelectorAll('.address-block').forEach(block => {
        block.style.display = '';
      });
    });
  }
});

