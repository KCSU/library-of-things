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
      category_id: $('#item-category').val(),
      ...loanTermsFromForm(),
      visible: $('#item-visible').is(':checked') ? 1 : 0,
      count: parseInt($('#item-count').val()) || 1,
      location: $('#item-location').val() || null,
      comments: $('#item-comments').val() || null
    };

    // Validate required fields
    if (!data.display_id || !data.title || !data.description) {
      alert('Please fill in all required fields');
      return;
    }

    const endpoint = itemId ? '/admin/api/edit_item' : '/admin/api/new_item';
    const payload = itemId ? { id: itemId, data } : { data };

    post(endpoint, payload)
      // The image is a separate multipart request: it needs an item id,
      // which a new item only has once it has been saved.
      .then(result => uploadImageIfChosen(itemId || result.id))
      .then(() => {
        dismissOverlay();
        location.reload();
      })
      .catch(err => {
        alert(err.message);
      });
  });
});

function showOverlay(item) {
  // Populate form fields
  $('#item-id').val(item.display_id ?? '');
  $('#item-name').val(item.title ?? '');
  $('#item-description').val(item.description ?? '');
  $('#item-count').val(item.count ?? 1);
  $('#item-location').val(item.location ?? '');
  $('#item-comments').val(item.comments ?? '');

  // Set dropdown values
  populateLoanTerms(item);
  showImagePreview(item);
  $('#item-category').val(item.category_id ?? '');
  
  // Set checkbox value
  $('#item-visible').prop('checked', item.visible);

  // Determine which sections to show based on item state
  const isNewItem = !item.id;

  // Show/hide sections appropriately
  $('.add-item-contents').toggleClass('hidden', !isNewItem);
  $('.edit-item-contents').toggleClass('hidden', isNewItem);

  // Store item ID in overlay for later use
  const overlay = $('.overlay');
  overlay.data('id', item.id || '');
  
  revealOverlay();
}

function deleteItem(itemId, title) {
  if (!confirm(`Delete "${title}"? This action is irreversible!`)) {
    return;
  }

  post('/admin/api/delete_item', { id: itemId })
    .then(() => location.reload())
    .catch(err => alert('Error: ' + err.message));
}

function updateLoanModeFields() {
  const mode = $('#item-loan-mode').val();
  $('#loan-duration-field').prop('hidden', mode !== 'duration');
  $('#loan-end-date-field').prop('hidden', mode !== 'end_date');
  $('#item-loan-duration').prop('required', mode === 'duration');
  $('#item-loan-end-date').prop('required', mode === 'end_date');
}

function loanTermsFromForm() {
  const mode = $('#item-loan-mode').val();
  if (mode === 'duration') {
    return { loan_duration_days: parseInt($('#item-loan-duration').val()) || 7,
             loan_end_date: null, loan_end_recurs_annually: false };
  }
  if (mode === 'end_date') {
    return { loan_duration_days: null,
             loan_end_date: $('#item-loan-end-date').val() || null,
             loan_end_recurs_annually: $('#item-loan-recurs').is(':checked') };
  }
  // 'permanent': neither a duration nor an end date.
  return { loan_duration_days: null, loan_end_date: null,
           loan_end_recurs_annually: false };
}

function populateLoanTerms(item) {
  let mode = 'permanent';
  if (item.loan_duration_days != null) mode = 'duration';
  else if (item.loan_end_date) mode = 'end_date';

  $('#item-loan-mode').val(mode);
  $('#item-loan-duration').val(item.loan_duration_days ?? 7);
  $('#item-loan-end-date').val(item.loan_end_date ?? '');
  $('#item-loan-recurs').prop('checked', !!item.loan_end_recurs_annually);
  updateLoanModeFields();
}

function uploadImageIfChosen(itemId) {
  const file = $('#item-image')[0]?.files?.[0];
  if (!file || !itemId) return Promise.resolve();

  const body = new FormData();
  body.append('image', file);

  return fetch(`/admin/api/items/${itemId}/image`, { method: 'POST', body })
    .then(res => res.json().then(result => {
      if (!res.ok || !result.success) {
        throw new Error('Image upload failed: ' +
                        (result.error || res.status));
      }
    }));
}

function showImagePreview(item) {
  const preview = $('#item-image-preview');
  $('#item-image').val('');
  if (item && item.id && item.has_image) {
    preview.attr('src', `/items/${item.id}/image`).prop('hidden', false);
  } else {
    preview.removeAttr('src').prop('hidden', true);
  }
}
