$(document).ready(function () {
  $('#edit-form').on('submit', function (e) {
    e.preventDefault();
    const overlay = $('.overlay');
    // Get the item ID (Firestore doc ID) from a hidden field
    const itemId = overlay.data('id');
    // Collect form data
    let data = {
      display_id: parseInt($('#item-id').val()),
      title: $('#item-name').val(),
      description: $('#item-description').val(),
      image_url: $('#item-image').val(),
      category: $('#item-category').val(),
      borrow_length: $('#item-loan-duration').val(),
    };

    // todo(lucas): this seems a bit fragile?
    if (!$('#item-location-container').hasClass('hidden')) {
      data.location = $('#item-location').val();
    }

    // If itemId is not set, this is a new item (handle separately if needed)
    if (!itemId) {
      fetch('/api/new_item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data })
      })
        .then(res => res.json())
        .then(result => {
          console.log(result);
          if (result.success) {
            dismissOverlay();
            location.reload(); // Reload to show updated data
          } else {
            alert('Error: ' + (result.error || 'Unknown error'));
          }
        });
    } else {
      // Send update request
      fetch('/api/edit_item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: itemId, data })
      })
        .then(res => res.json())
        .then(result => {
          console.log(result);
          if (result.success) {
            dismissOverlay();
            location.reload(); // Reload to show updated data
          } else {
            alert('Error: ' + (result.error || 'Unknown error'));
          }
        });
    }
  });

  $("#loan-form").on('submit', function (e) {
    e.preventDefault();
    const overlay = $('.overlay');
    const itemId = overlay.data('id');
    const email = $('#loan-email').val().trim();

    fetch('/api/loan_item', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: itemId, email })
    })
      .then(res => res.json())
      .then(result => {
        console.log(result);
        if (result.success) {
          dismissOverlay();
          location.reload(); // Reload to show updated data
        } else {
          alert('Error: ' + (result.error || 'Unknown error'));
        }
      });
  });
});

function showOverlay(item) {
  $('#item-id').prop('placeholder', item.display_id ?? '');
  $('#item-id').prop('value', item.display_id ?? '');

  $('#item-name').prop('placeholder', item.title ?? '');
  $('#item-name').prop('value', item.title ?? '');

  $('#item-description').prop('placeholder', item.description ?? '');
  $('#item-description').prop('value', item.description ?? '');

  $('#item-image').prop('placeholder', item.image_url ?? '');
  $('#item-image').prop('value', item.image_url ?? '');

  $('#item-location').prop('placeholder', item.location ?? '');
  $('#item-location').prop('value', item.location ?? '');

  // Set correct options
  $('#item-loan-duration').val(item.borrow_length ?? 'short');
  $('#item-category').val(item.category ?? 'others');

  console.log(item);

  if (item.borrowed_by) {
    $('.return-item-section').removeClass('hidden');
    $('.loan-item-section').addClass('hidden');
    $('.delete-item-section').removeClass('hidden');
    $('.edit-item-section').removeClass('hidden');
    $('.add-item-section').addClass('hidden');
    $('#item-location-container').addClass('hidden');
  } else if (item.id) {
    $('.return-item-section').addClass('hidden');
    $('.loan-item-section').removeClass('hidden');
    $('.delete-item-section').removeClass('hidden');
    $('.edit-item-section').removeClass('hidden');
    $('.add-item-section').addClass('hidden');
    $('#item-location-container').removeClass('hidden');
  } else {
    $('.return-item-section').addClass('hidden');
    $('.loan-item-section').addClass('hidden');
    $('.delete-item-section').addClass('hidden');
    $('.edit-item-section').addClass('hidden');
    $('.add-item-section').removeClass('hidden');
    $('#item-location-container').removeClass('hidden');
  }

  // Store Firestore doc ID in overlay for later
  const overlay = $('.overlay');
  overlay.data('id', item.id ?? '');
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
  fetch('/api/delete_item', {
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
    });
}

function returnItem() {
  const overlay = $('.overlay');
  const itemId = overlay.data('id');
  if (!itemId) {
    alert('No item selected for returning.');
    return;
  }

  const itemLocation = prompt('Please enter the return location (e.g., Porters\' Lodge):', '');
  if (!itemLocation) return;

  fetch('/api/return_item', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: itemId, location: itemLocation })
  })
    .then(res => res.json())
    .then(result => {
      if (result.success) {
        dismissOverlay();
        location.reload();
      } else {
        alert('Error: ' + (result.error || 'Unknown error'));
      }
    });
}