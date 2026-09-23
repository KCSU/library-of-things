$(document).ready(function() {
  $('#grant-form').on('submit', function(e) {
    e.preventDefault();
    setRole($('#grant-crsid').val().trim().toLowerCase(), $('#grant-role').val());
  });

  $('.role-select').on('change', function() {
    setRole($(this).data('crsid'), $(this).val());
  });
});

function setRole(crsid, role) {
  if (!crsid) {
    alert('Enter a CRSid.');
    return;
  }

  post('/admin/api/set_role', { crsid: crsid, role: parseInt(role) })
    .then(() => location.reload())
    .catch(err => {
      alert('Error: ' + err.message);
      location.reload();
    });
}
