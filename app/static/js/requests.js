/**
 * Requests Management JavaScript
 * 
 * Handles the admin requests panel functionality:
 * - Accepting item requests (creating loans)
 * - Refusing/rejecting item requests
 * 
 * API Endpoints used:
 * - POST /admin/api/accept_request - Accept request and create loan
 * - POST /admin/api/refuse_request - Refuse a borrow request
 */

function acceptRequest(requestId) {
  if (!confirm('Are you sure you want to mark the item as delivered?')) {
    return;
  }

  fetch('/admin/api/accept_request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: requestId })
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

// Alias for backward compatibility
function deliverItem(requestId, itemId, email) {
  acceptRequest(requestId);
}

function refuseRequest(requestId) {
  const reason = prompt('Please give your reason for refusing this request:');
  if (!reason) {
    return; // Must give a reason to refuse
  }

  fetch('/admin/api/refuse_request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: requestId, reason: reason })
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