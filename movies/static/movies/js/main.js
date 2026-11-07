/**
 * CineScope - Interactive UI Utilities
 */

document.addEventListener('DOMContentLoaded', () => {
  initSearch();
  initTrailerModal();
  initImageFallbacks();
});

/**
 * Enhanced Search input features
 * - Keyboard shortcut ('/' key to focus)
 * - Clear button toggle and action
 */
function initSearch() {
  const searchInput = document.querySelector('.search-input');
  const clearBtn = document.querySelector('.search-clear-btn');

  if (!searchInput) return;

  // Toggle clear button on input
  function updateClearBtn() {
    if (clearBtn) {
      if (searchInput.value.trim().length > 0) {
        clearBtn.classList.add('visible');
      } else {
        clearBtn.classList.remove('visible');
      }
    }
  }

  searchInput.addEventListener('input', updateClearBtn);
  updateClearBtn();

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      searchInput.value = '';
      updateClearBtn();
      searchInput.focus();
    });
  }

  // Keyboard shortcut: Pressing '/' anywhere focuses the search bar
  document.addEventListener('keydown', (e) => {
    const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
    if (activeTag === 'input' || activeTag === 'textarea' || document.activeElement.isContentEditable) {
      return;
    }

    if (e.key === '/') {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  });
}

/**
 * Trailer Modal Popup
 * - Plays YouTube video when triggered
 * - Stops video immediately on close
 * - Closes on backdrop click or Escape key
 */
function initTrailerModal() {
  const modal = document.getElementById('trailerModal');
  const modalContainer = document.getElementById('trailerVideoContainer');
  const closeBtn = document.getElementById('closeTrailerBtn');
  const trailerTriggers = document.querySelectorAll('[data-trailer-key]');

  if (!modal || !modalContainer) return;

  function openModal(trailerKey) {
    if (!trailerKey) return;
    modalContainer.innerHTML = `
      <iframe 
        src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(trailerKey)}?autoplay=1&rel=0&modestbranding=1" 
        title="Movie Trailer" 
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
        allowfullscreen>
      </iframe>
    `;
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    modal.classList.remove('open');
    // Clear iframe to immediately stop sound/video playback
    modalContainer.innerHTML = '';
    document.body.style.overflow = '';
  }

  trailerTriggers.forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const key = btn.getAttribute('data-trailer-key');
      if (key) {
        openModal(key);
      }
    });
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', closeModal);
  }

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      closeModal();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('open')) {
      closeModal();
    }
  });
}

/**
 * Graceful fallback when an image fails to load
 */
function initImageFallbacks() {
  const images = document.querySelectorAll('img[data-fallback]');
  images.forEach((img) => {
    img.addEventListener('error', () => {
      img.style.display = 'none';
      const fallback = img.nextElementSibling;
      if (fallback && fallback.classList.contains('movie-poster-fallback')) {
        fallback.style.display = 'flex';
      }
    });
  });
}
