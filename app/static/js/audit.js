// Debounce delay
const SEARCH_DELAY_MS = 300;

$(document).ready(function() {
  let timer = null;
  let latest = 0;

  $('#audit-search').on('input', function() {
    clearTimeout(timer);
    timer = setTimeout(() => search($(this).val().trim()), SEARCH_DELAY_MS);
  });

  function search(query) {
    const url = new URL(location.pathname, location.origin);
    if (query) {
      url.searchParams.set('q', query);  // a new search starts at page 1
    }

    const id = ++latest;
    fetch(url)
      .then(response => response.text())
      .then(html => {
        if (id !== latest) {
          return;  // a newer search has started, drop this one
        }
        const fresh = new DOMParser().parseFromString(html, 'text/html')
          .getElementById('audit-results');
        if (!fresh) {
          location.href = url;
          return;
        }
        $('#audit-results').replaceWith(fresh);
        history.replaceState(null, '', url);
      })
      .catch(() => { location.href = url; });
  }
});
