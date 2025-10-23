$(document).ready(() => {
  // Get category from URL query parameters
  const urlParams = new URLSearchParams(window.location.search);
  const category = urlParams.get('category');
  
  // Build the SSR endpoint URL with optional category filter
  const ssrUrl = category ? `ssr/cards?category=${encodeURIComponent(category)}` : 'ssr/cards';
  
  // Server-side render the cards, then replace the HTML
  $("#cards-container").load(ssrUrl, () => {
    // Once finished, load icons asynchronously
    $('#cards-container span.icon').each((_, el) => {
      const iconName = $(el).data('icon');
      $(el).load("/static/icons/" + iconName + ".svg");
    });
  });
});

let selectedItemId = null;
let selectedItemTitle = '';
let selectedLoanPolicy = '';

function showConfirmOverlay(item) {
  // Store item details
  selectedItemId = item.id;
  selectedItemTitle = item.title;
  selectedLoanPolicy = item.loan_policy;

  // Update overlay text
  $('.item-title-labels').text(selectedItemTitle);
  
  // Hide all loan type labels first
  $(".short-loan-labels, .medium-loan-labels, .long-loan-labels, .permanent-labels").addClass('hidden');
  
  // Show appropriate labels based on loan policy
  if (selectedLoanPolicy === 'seven_days') {
    $('.short-loan-labels').removeClass('hidden');
  } else if (selectedLoanPolicy === 'thirty_days') {
    $('.medium-loan-labels').removeClass('hidden');
  } else if (selectedLoanPolicy === 'academic_year_end') {
    $('.long-loan-labels').removeClass('hidden');
  } else if (selectedLoanPolicy === 'permanent') {
    $('.permanent-labels').removeClass('hidden');
  }
  
  // Show overlay with fade-in animation
  const overlay = $('#confirm-overlay');
  overlay.removeClass('hidden');
  overlay[0].offsetHeight; // Force reflow
  overlay.removeClass('opacity-0').addClass('opacity-100');
  
  // Prevent background scrolling
  $('body').css('overflow', 'hidden');
}

function requestItem() {
  if (!selectedItemId) {
    alert('No item selected');
    return;
  }

  fetch(`/items/${selectedItemId}/request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
    .then(res => {
      if (res.status === 403) {
        return res.json().then(data => {
          alert(data.error || 'Site is in read-only mode');
          dismissOverlay();
          throw new Error('Read-only mode');
        });
      }
      return res.json();
    })
    .then(result => {
      if (result.success) {
        dismissOverlay();
        alert('Item request submitted successfully! Someone will be in touch via email soon.');
        location.reload();
      } else {
        alert('Error: ' + (result.error || 'Unknown error'));
      }
    })
    .catch(err => {
      if (err.message !== 'Read-only mode') {
        alert('Network error: ' + err.message);
      }
    });
}