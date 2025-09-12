
document.addEventListener("DOMContentLoaded", function () {
  const img = document.getElementById("mainProductImage");
  const result = document.getElementById("zoomResult");
  const lens = document.getElementById("lens");

  if (img && result && lens) {
    const lensSize = 100;

    img.addEventListener("mousemove", function(e) {
      const rect = img.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const xPercent = (x / rect.width) * 100;
      const yPercent = (y / rect.height) * 100;

      // Position lens
      lens.style.display = "block";
      lens.style.left = `${x - lensSize / 2}px`;
      lens.style.top = `${y - lensSize / 2}px`;

      // Show zoom
      result.classList.remove("d-none");
      result.style.backgroundImage = `url(${img.src})`;
      result.style.backgroundPosition = `${xPercent}% ${yPercent}%`;
    });

    img.addEventListener("mouseleave", function () {
      lens.style.display = "none";
      result.classList.add("d-none");
    });
  }
});

