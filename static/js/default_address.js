
  document.addEventListener('DOMContentLoaded', function () {
    const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    const radios = document.querySelectorAll('.set-default-address');

    radios.forEach(function (radio) {
      radio.addEventListener('change', function () {
        const addressId = this.dataset.addressId;

        fetch(`/address/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrftoken
          },
          body: new URLSearchParams({
            set_default: "true",
            address_id: addressId
          })
        })
        .then(response => {
          if (!response.ok) throw new Error("Request failed");

         
          radios.forEach(r => {
            const label = r.closest('.form-check')?.querySelector('label.form-check-label');
            if (label) label.textContent = 'Set as Default';
          });

          const selectedLabel = this.closest('.form-check')?.querySelector('label.form-check-label');
          if (selectedLabel) selectedLabel.textContent = 'Default Address';
        })
        .catch(error => {
          console.error("Error:", error);
        });
      });
    });
  });

