$(document).ready(() => {
  // server-side render the cards, then replace the html
  $("#cards-container").load("_ssr/cards")
});
