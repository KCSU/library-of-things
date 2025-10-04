$(document).ready(() => {
  // server-side render the cards, then replace the html
  $("#cards-container").load("ssr/cards", () => {
    // on finish, load icons asynchronously
    $('span.icon').each((_, el) => {
      const iconName = $(el).data('icon');
      $(el).load("/static/icons/" + iconName + ".svg");
    });
  });
});

let selectedItemId = null;

function showConfirmOverlay(item_name, loan_length, item_id) {
  selectedItemId = item_id; // Store the item ID for later use
  $('.item-title-labels').text(item_name);
  $('.short-loan-labels, .long-loan-labels, .permanent-labels').addClass('hidden');

  if (loan_length === 'short')
    $('.short-loan-labels').removeClass('hidden');
  else if (loan_length === 'long')
    $('.long-loan-labels').removeClass('hidden');
  else if (loan_length === 'permanent')
    $('.permanent-labels').removeClass('hidden');

  const overlay = $('#confirm-overlay');

  overlay.removeClass('hidden');
  overlay[0].offsetHeight; // Force reflow
  overlay.removeClass('opacity-0').addClass('opacity-100');

  $('body').css('overflow', 'hidden'); // Prevent background scrolling
}

function requestItem() {
  if (!selectedItemId) {
    console.error('No item selected');
    return;
  }

  $.ajax({
    url: '/api/request_item',
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({ id: selectedItemId }),
    success: function (response) {
      if (response.success) {
        dismissOverlay();
        // Show success message or redirect
        alert('Item request submitted successfully!');
        location.reload(); // Reload to show updated data
      } else {
        alert('Error: ' + (response.error || 'Unknown error'));
      }
    },
    error: function (xhr, status, error) {
      console.error('Request failed:', error);
      alert('Failed to submit request. Please try again.');
    }
  });
}