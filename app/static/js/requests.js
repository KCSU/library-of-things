function acceptRequest(req) {
  if (!confirm('Are you sure you want to mark the item as delivered?')) {
    return;
  }

  post('/admin/api/accept_request', { id: req.id })
    .then(() => location.reload())
    .catch(err => alert('Error: ' + err.message));
}

function refuseRequest(req) {
  const reason = prompt('Please give your reason for refusing this request:');
  if (!reason) {
    return; // Must give a reason to refuse
  }

  post('/admin/api/refuse_request', { id: req.id, reason: reason })
    .then(() => location.reload())
    .catch(err => alert('Error: ' + err.message));
}

function toggleLendPanel() {
  $('#lend-panel').toggleClass('hidden');
}

$(document).ready(function() {
  $('#lend-form').on('submit', function(e) {
    e.preventDefault();

    const crsid = $('#lend-crsid').val().trim().toLowerCase();
    if (!crsid) {
      alert('Enter the borrower\'s CRSid.');
      return;
    }

    post('/admin/api/lend', {
      item_id: $('#lend-item').val(),
      crsid: crsid,
      start_time: $('#lend-start').val() || null
    })
      .then(result => {
        alert('Loan recorded for ' + result.borrower + '.');
        location.reload();
      })
      .catch(err => alert('Error: ' + err.message));
  });
});
