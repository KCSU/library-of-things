let selectedItemId = null;
let selectedItemTitle = '';

function showConfirmOverlay(item) {
  selectedItemId = item.id;
  selectedItemTitle = item.title;

  $('.item-title-labels').text(selectedItemTitle);
  // The server renders the terms; the client no longer needs to know the
  // vocabulary of loan policies.
  $('.loan-terms-labels').text(item.loan_terms);
  $('.permanent-labels').toggleClass('hidden', !item.is_permanent);
  $('.returnable-labels').toggleClass('hidden', !!item.is_permanent);

  revealOverlay();
}

function requestItem() {
  if (!selectedItemId) {
    alert('No item selected');
    return;
  }

  post(`/items/${selectedItemId}/request`)
    .then(() => {
      dismissOverlay();
      alert('Item request submitted successfully! Someone will be in touch via email soon.');
      location.reload();
    })
    .catch(err => {
      alert('Error: ' + err.message);
    });
}