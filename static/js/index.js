$(document).ready(() => {
  // server-side render the cards, then replace the html
  $("#cards-container").load("_ssr/cards", () => {
    // on finish, load icons asynchronously
    $('span.icon').each((_, el) => {
      const iconName = $(el).data('icon');
      $(el).load("/static/icons/" + iconName + ".svg");
    });
  });
});
