
function toggleEditForm(orderId) {
  const form = document.getElementById('edit-form-' + orderId);
  form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

