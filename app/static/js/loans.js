function returnItem(loan) {
  if (!confirm(`Are you sure you want to mark "${loan.item_title}" as returned from ${loan.borrower_name}?`)) {
    return;
  }

  post('/admin/api/end_loan', { loan_id: loan.id })
    .then(() => location.reload())
    .catch(err => alert('Error: ' + err.message));
}
