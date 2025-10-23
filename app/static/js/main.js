function initLightbox() {
  const lightboxHTML = `
    <div id="lightbox-overlay" class="lightbox-overlay cursor-pointer">
      <div class="lightbox-content cursor-default">
        <img id="lightbox-image" class="lightbox-image" src="" alt="">
      </div>
    </div>
  `;
  $('body').append(lightboxHTML);

  const $overlay = $('#lightbox-overlay');
  const $lightboxImage = $('#lightbox-image');

  function openLightbox(imageSrc, imageAlt) {
    $lightboxImage.attr('src', imageSrc);
    $lightboxImage.attr('alt', imageAlt || '');
    $overlay.addClass('active');
    $('body').css('overflow', 'hidden'); // Prevent background scrolling
  }

  function closeLightbox() {
    $overlay.removeClass('active');
    $('body').css('overflow', ''); // Restore scrolling
  }

  // Close on overlay click (but not on image click)
  $overlay.on('click', function (e) {
    if (e.target === this) {
      closeLightbox();
    }
  });

  // Close on Escape key
  $(document).on('keydown', function (e) {
    if (e.key === 'Escape' && $overlay.hasClass('active')) {
      closeLightbox();
    }
  });

  // Attach image listeners
  $('.card img').off('click.lightbox').on('click.lightbox', function () {
    openLightbox(this.src, this.alt);
  });

  $(document).on('click', '.card img', function () {
    openLightbox(this.src, this.alt);
  });
}

$(document).ready(() => {
  initLightbox();

  // lazy icon loading
  $('span.icon').each((_, el) => {
    const iconName = $(el).data('icon');
    $(el).load("/static/icons/" + iconName + ".svg");
  });

  // auto-collapse sidebar on mobile (< md breakpoint: 768px)
  function handleSidebarResize() {
    const $sidebar = $('.sidebar');
    if (window.innerWidth < 768) {
      $sidebar.attr('aria-hidden', 'true');
    } else {
      $sidebar.attr('aria-hidden', 'false');
    }
  }

  handleSidebarResize();
  $(window).on('resize', handleSidebarResize);
});

function signOut() {
  var auth2 = gapi.auth2.getAuthInstance();
  auth2.signOut();
}

function dismissOverlay() {
  const overlay = $('.overlay');
  overlay.removeClass('opacity-100').addClass('opacity-0');
  setTimeout(() => {
    overlay.addClass('hidden');
  }, 300); // Match transition duration

  $('body').css('overflow', ''); // Re-enable background scrolling
}