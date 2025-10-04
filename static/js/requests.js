function deliverItem(itemId, email) {
  const confirmed = confirm('Are you sure you want to mark this item as delivered?');
  if (!confirmed) return;
  fetch('/api/loan_item', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: itemId, email })
  })
    .then(res => res.json())
    .then(result => {
      console.log(result);
      if (result.success) {
        location.reload(); // Reload to show updated data
      } else {
        alert('Error: ' + (result.error || 'Unknown error'));
      }
    });
}

function refuseRequest(itemId) {
  const reason = prompt('Please give your reason for refusing this request:');
  fetch('/api/refuse_request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: itemId, reason })
  })
    .then(res => res.json())
    .then(result => {
      console.log(result);
      if (result.success) {
        location.reload(); // Reload to show updated data
      } else {
        alert('Error: ' + (result.error || 'Unknown error'));
      }
    });
}