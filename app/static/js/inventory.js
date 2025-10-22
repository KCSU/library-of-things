$(document).ready(function () {
  $('#edit-form').on('submit', function (e) {
    e.preventDefault();
    const overlay = $('.overlay');
    const itemId = overlay.data('id');
    
    // Collect form data
    const data = {
      display_id: $('#item-id').val(),
      title: $('#item-name').val(),
      description: $('#item-description').val(),
      image_url: $('#item-image').val(),
      category_id: parseInt($('#item-category').val()),
      loan_policy: $('#item-loan-policy').val(),
      visible: $('#item-visible').is(':checked') ? 1 : 0,
      count: parseInt($('#item-count').val()) ?? 1,
      location: $('#item-location').val() || null,
      comments: $('#item-comments').val() || null
    };

    // Validate required fields
    if (!data.display_id || !data.title || !data.description || !data.image_url) {
      alert('Please fill in all required fields');
      return;
    }

    const endpoint = itemId ? '/admin/api/edit_item' : '/admin/api/new_item';
    const payload = itemId ? { id: itemId, data } : { data };

    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(result => {
        if (result.success) {
          dismissOverlay();
          location.reload();
        } else {
          alert('Error: ' + (result.error || 'Unknown error'));
        }
      })
      .catch(err => {
        alert('Network error: ' + err.message);
      });
  });
});

function showOverlay(item) {
  // Populate form fields
  $('#item-id').val(item.display_id ?? '');
  $('#item-name').val(item.title ?? '');
  $('#item-description').val(item.description ?? '');
  $('#item-image').val(item.image_url ?? '');
  $('#item-count').val(item.count ?? 1);
  $('#item-location').val(item.location ?? '');
  $('#item-comments').val(item.comments ?? '');

  // Set dropdown values
  $('#item-loan-policy').val(item.loan_policy ?? 'seven_days');
  $('#item-category').val(item.category_id ?? 1);
  
  // Set checkbox value
  $('#item-visible').prop('checked', item.visible);

  // Determine which sections to show based on item state
  const isNewItem = !item.id;

  // Show/hide sections appropriately
  $('.add-item-contents').toggleClass('hidden', !isNewItem);
  $('.edit-item-contents').toggleClass('hidden', isNewItem);
  $('.delete-item-contents').toggleClass('hidden', isNewItem);

  // Store item ID in overlay for later use
  const overlay = $('.overlay');
  overlay.data('id', item.id || '');
  
  // Show overlay with fade-in animation
  overlay.removeClass('hidden');
  overlay[0].offsetHeight; // Force reflow
  overlay.removeClass('opacity-0').addClass('opacity-100');
}

function deleteItem() {
  const overlay = $('.overlay');
  const itemId = overlay.data('id');
  
  if (!itemId) {
    alert('No item selected for deletion.');
    return;
  }
  
  if (!confirm('Are you sure you want to delete this item? This action is irreversible!')) {
    return;
  }
  
  fetch('/admin/api/delete_item', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: itemId })
  })
    .then(res => res.json())
    .then(result => {
      if (result.success) {
        dismissOverlay();
        location.reload();
      } else {
        alert('Error: ' + (result.error || 'Unknown error'));
      }
    })
    .catch(err => {
      alert('Network error: ' + err.message);
    });
}
