document.addEventListener("DOMContentLoaded", function () {
  const track = document.getElementById("sliderTrack");
  const fill = document.getElementById("rangeFill");
  const thumbMin = document.getElementById("thumbMin");
  const thumbMax = document.getElementById("thumbMax");
  const minVal = document.getElementById("minPriceVal");
  const maxVal = document.getElementById("maxPriceVal");
  const minInput = document.getElementById("minPriceInput");
  const maxInput = document.getElementById("maxPriceInput");

  const minPrice = 0;
  const maxPrice = 30000;
  const stepSize = 100;
  let trackWidth;

  function updateTrackWidth() {
    trackWidth = track.offsetWidth;
  }

  window.addEventListener("resize", updateTrackWidth);
  updateTrackWidth();

  function valueToPosition(value) {
    return ((value - minPrice) / (maxPrice - minPrice)) * trackWidth;
  }

  function positionToValue(pos) {
    const rawValue = (pos / trackWidth) * (maxPrice - minPrice) + minPrice;
    const steppedValue = Math.round(rawValue / stepSize) * stepSize;
    return Math.max(minPrice, Math.min(maxPrice, steppedValue));
  }

  function updateUI(min, max) {
    const minPos = valueToPosition(min);
    let maxPos = valueToPosition(max);
    const handleWidth = 18;
    maxPos = Math.min(maxPos, trackWidth - handleWidth);
    thumbMin.style.left = `${minPos}px`;
    thumbMax.style.left = `${maxPos}px`;

    fill.style.left = `${minPos}px`;
    fill.style.width = `${maxPos - minPos}px`;
    // Show ₹30000+ if max is at the end
    const isMaxOpen = max >= maxPrice;
    maxVal.textContent = isMaxOpen ? `${max}+` : max;

    minVal.textContent = min;
    
    minInput.value = min;
    maxInput.value = isMaxOpen ? "" : max;;
  }

  let minValue =  typeof initialMin !== "undefined" ? initialMin : 0;
  let maxValue =  typeof initialMax !== "undefined" ? initialMax : 30000;

  function dragThumb(thumb, isMin) {
    function onMove(e) {
      const rect = track.getBoundingClientRect();
      let pos = e.clientX - rect.left;
      pos = Math.max(0, Math.min(pos, trackWidth));
      const value = positionToValue(pos);

      if (isMin) {
        minValue = Math.min(value, maxValue);
      } else {
        maxValue = Math.max(value, minValue);
      }

      updateUI(minValue, maxValue);
    }

    function onUp() {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    }

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }

  thumbMin.addEventListener("mousedown", () => dragThumb(thumbMin, true));
  thumbMax.addEventListener("mousedown", () => dragThumb(thumbMax, false));

  updateUI(minValue, maxValue);
});
