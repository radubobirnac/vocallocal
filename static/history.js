document.addEventListener('DOMContentLoaded', function() {
  console.log('History page loaded');

  // Use the global function to initialize the history dropdown
  if (typeof window.initializeHistoryDropdown === 'function') {
    window.initializeHistoryDropdown();
  } else {
    console.log('History dropdown initialization function not found, defining it');

    // Define the function if it doesn't exist yet
    window.initializeHistoryDropdown = function() {
      const historyButton = document.getElementById('history-button');
      const historyDropdown = document.getElementById('history-dropdown');

      if (historyButton && historyDropdown && !historyButton._initialized) {
        console.log('Initializing history dropdown from history.js');
        // Mark as initialized to prevent duplicate event listeners
        historyButton._initialized = true;

        historyButton.addEventListener('click', (event) => {
          event.stopPropagation();
          const isExpanded = historyButton.getAttribute('aria-expanded') === 'true';

          historyButton.setAttribute('aria-expanded', !isExpanded);
          historyDropdown.classList.toggle('show');

          // Close user dropdown if open
          const avatarButton = document.getElementById('avatar-button');
          const userDropdown = document.getElementById('user-dropdown');
          if (avatarButton && userDropdown) {
            avatarButton.setAttribute('aria-expanded', 'false');
            userDropdown.classList.remove('show');
          }
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
          historyButton.setAttribute('aria-expanded', 'false');
          historyDropdown.classList.remove('show');
        });

        // Prevent dropdown from closing when clicking inside it
        historyDropdown.addEventListener('click', (event) => {
          event.stopPropagation();
        });
      }
    };

    // Call the function to initialize the dropdown
    window.initializeHistoryDropdown();
  }

  // Pagination variables
  const itemsPerPage = 10;
  let currentPage = 1;
  let filteredItems = [];

  // Get all history items and initialize
  const historyItems = Array.from(document.querySelectorAll('.history-item'));
  filteredItems = [...historyItems];

  // Sort items by timestamp (newest first by default)
  sortItems('newest');

  // Initialize pagination
  updatePagination();

  // Handle pagination buttons
  document.getElementById('prev-page').addEventListener('click', function() {
    if (currentPage > 1) {
      currentPage--;
      updatePagination();
    }
  });

  document.getElementById('next-page').addEventListener('click', function() {
    const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
    if (currentPage < totalPages) {
      currentPage++;
      updatePagination();
    }
  });

  // Handle search
  const searchInput = document.getElementById('history-search');
  const searchButton = document.getElementById('search-btn');

  searchInput.addEventListener('input', debounce(function() {
    filterItems();
  }, 300));

  searchButton.addEventListener('click', function() {
    filterItems();
  });

  // Handle sort selection
  const sortSelect = document.getElementById('sort-select');
  sortSelect.addEventListener('change', function() {
    sortItems(this.value);
  });

  // Handle view full text buttons
  document.querySelectorAll('.view-full-text').forEach(button => {
    button.addEventListener('click', function() {
      const text = this.dataset.text;
      const originalText = this.dataset.original;
      const translatedText = this.dataset.translated;

      // Create modal for viewing full text
      const modal = document.createElement('div');
      modal.className = 'modal';

      let modalContent = '';
      if (originalText && translatedText) {
        // Translation view
        modalContent = `
          <div class="modal-content">
            <span class="close-modal">&times;</span>
            <h3>Original Text</h3>
            <div class="full-text-container">${originalText}</div>
            <h3>Translated Text</h3>
            <div class="full-text-container">${translatedText}</div>
          </div>
        `;
      } else {
        // Transcription view
        modalContent = `
          <div class="modal-content">
            <span class="close-modal">&times;</span>
            <h3>Full Transcription</h3>
            <div class="full-text-container">${text}</div>
          </div>
        `;
      }

      modal.innerHTML = modalContent;
      document.body.appendChild(modal);

      // Handle close button
      modal.querySelector('.close-modal').addEventListener('click', function() {
        document.body.removeChild(modal);
      });

      // Close when clicking outside the modal
      window.addEventListener('click', function(event) {
        if (event.target === modal) {
          document.body.removeChild(modal);
        }
      });
    });
  });

  // Handle copy text buttons
  document.querySelectorAll('.copy-text').forEach(button => {
    button.addEventListener('click', function() {
      const text = this.dataset.text;
      navigator.clipboard.writeText(text).then(() => {
        // Show copy success notification
        const notification = document.createElement('div');
        notification.className = 'notification success';
        notification.textContent = 'Text copied to clipboard!';
        document.body.appendChild(notification);

        // Remove notification after 2 seconds
        setTimeout(() => {
          document.body.removeChild(notification);
        }, 2000);
      });
    });
  });

  // Replay functionality has been removed

  // Helper functions
  function updatePagination() {
    const totalPages = Math.ceil(filteredItems.length / itemsPerPage);

    // Update page info
    document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages || 1}`;

    // Update button states
    document.getElementById('prev-page').disabled = currentPage === 1;
    document.getElementById('next-page').disabled = currentPage === totalPages || totalPages === 0;

    // Show only items for current page
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage - 1;

    filteredItems.forEach((item, index) => {
      if (index >= startIndex && index <= endIndex) {
        item.style.display = 'block';
      } else {
        item.style.display = 'none';
      }
    });

    // Show empty message if no items
    const emptyMessage = document.querySelector('.empty-history');
    if (emptyMessage) {
      if (filteredItems.length === 0) {
        emptyMessage.style.display = 'block';
      } else {
        emptyMessage.style.display = 'none';
      }
    }
  }

  function filterItems() {
    const searchTerm = searchInput.value.toLowerCase().trim();

    if (searchTerm === '') {
      // If search is empty, show all items
      filteredItems = [...historyItems];
    } else {
      // Filter items based on search term
      filteredItems = historyItems.filter(item => {
        const itemText = item.textContent.toLowerCase();
        return itemText.includes(searchTerm);
      });
    }

    // Reset to first page and update
    currentPage = 1;
    sortItems(sortSelect.value);
  }

  function sortItems(sortOrder) {
    // Sort items based on timestamp
    filteredItems.sort((a, b) => {
      const timestampA = a.dataset.timestamp;
      const timestampB = b.dataset.timestamp;

      if (sortOrder === 'newest') {
        return timestampB.localeCompare(timestampA);
      } else {
        return timestampA.localeCompare(timestampB);
      }
    });

    // Update pagination after sorting
    updatePagination();
  }

  // Debounce function to limit how often a function is called
  function debounce(func, wait) {
    let timeout;
    return function() {
      const context = this;
      const args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        func.apply(context, args);
      }, wait);
    };
  }
});
