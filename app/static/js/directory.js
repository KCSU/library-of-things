const ITEMS_PER_PAGE = 10;
let currentPage = 1;
let totalPages = 1;
let matching = null;

$(document).ready(function() {
  $('#user-search').on('input', applyFilter);
  $('.toggle-enabled').on('click', function() {
    setEnabled($(this).data('crsid'), $(this).data('enable') === true ||
                                     $(this).data('enable') === 'true');
  });
  applyFilter();
});

function applyFilter() {
  const query = $('#user-search').val().trim().toLowerCase();
  const $all = $('.user-row');
  matching = query
    ? $all.filter((_, row) => $(row).data('search').indexOf(query) !== -1)
    : $all;

  totalPages = Math.max(1, Math.ceil(matching.length / ITEMS_PER_PAGE));
  $('#total-items').text(matching.length);
  $('#total-pages').text(totalPages);
  $all.hide();
  showPage(1);
}

function showPage(page) {
  const start = (page - 1) * ITEMS_PER_PAGE;
  const end = start + ITEMS_PER_PAGE;

  matching.hide().slice(start, end).show();

  $('#start-item').text(matching.length ? start + 1 : 0);
  $('#end-item').text(Math.min(end, matching.length));
  $('#current-page').text(page);
  $('#prev-btn').prop('disabled', page === 1);
  $('#next-btn').prop('disabled', page === totalPages);

  currentPage = page;
}

function changePage(direction) {
  const next = currentPage + direction;
  if (next >= 1 && next <= totalPages) {
    showPage(next);
  }
}

function setEnabled(crsid, enabled) {
  const verb = enabled ? 'enabling' : 'disabling';
  const reason = prompt(`Please give your reason for ${verb} ${crsid}:`);
  if (!reason) {
    return;
  }

  post('/admin/api/set_user_enabled',
       { crsid: crsid, enabled: enabled, reason: reason })
    .then(() => location.reload())
    .catch(err => alert('Error: ' + err.message));
}
