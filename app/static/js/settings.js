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
    
    if (!confirm(`Are you sure you want to update the site settings?`)) {
      return;
    }

    post('/admin/api/update_settings', data)
      .then(() => alert('Settings saved successfully!'))
      .catch(err => alert('Error: ' + err.message));
  });
});

function toggleAnnouncementText() {
  const toggle = $('#announcement-toggle');
  const textarea = $('#announcement-text');
  textarea.prop('disabled', !toggle.prop('checked'));
}