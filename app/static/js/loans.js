function returnItem(loan) {
  if (!confirm(`Are you sure you want to mark "${loan.item_title}" as returned from ${loan.borrower_name}?`)) {
    return;
  }

  fetch('/admin/api/end_loan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ loan_id: loan.id })
  })
    .then(res => res.json())
    .then(result => {
      if (result.success) {
        location.reload();
      } else {
        throw new Error(result.error || 'Failed to return item');
      }
    })
    .catch(err => {
      alert('Error: ' + err.message);
    });
}
