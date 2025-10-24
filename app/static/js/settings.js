$(document).ready(function() {
  // Initialize textarea state based on toggle
  toggleAnnouncementText();
  
  // Handle form submission
  $('#settings-form').on('submit', function(e) {
    e.preventDefault();
    
    const data = {
      announcement: {
        text: $('#announcement-text').val(),
        enabled: $('#announcement-toggle').prop('checked')
      },
      read_only: $('#read-only-toggle').prop('checked')
    };
    
    fetch('/admin/api/update_settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
      .then(res => res.json())
      .then(result => {
        if (result.success) {
          alert('Settings saved successfully!');
        } else {
          alert('Error: ' + (result.error || 'Unknown error'));
        }
      })
      .catch(err => {
        alert('Network error: ' + err.message);
      });
  });
});

function toggleAnnouncementText() {
  const toggle = $('#announcement-toggle');
  const textarea = $('#announcement-text');
  textarea.prop('disabled', !toggle.prop('checked'));
}