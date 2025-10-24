function acceptRequest(req) {
  if (!confirm('Are you sure you want to mark the item as delivered?')) {
    return;
  }

  fetch('/admin/api/accept_request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: req.id })
  })
    .then(res => res.json())
    .then(result => {
      if (result.success) {
        location.reload();
      } else {
        throw new Error(result.error || 'Failed to accept request');
      }
    })
    .catch(err => {
      alert('Error: ' + err.message);
    });
}

function refuseRequest(req) {
  const reason = prompt('Please give your reason for refusing this request:');
  if (!reason) {
    return; // Must give a reason to refuse
  }

  fetch('/admin/api/refuse_request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: req.id, reason: reason })
  })
    .then(res => res.json())
    .then(result => {
      if (result.success) {
        location.reload();
      } else {
        alert('Error: ' + (result.error || 'Unknown error'));
      }
    })
    .catch(err => {
      alert('Network error: ' + err.message);
    });
}