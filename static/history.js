document.addEventListener('DOMContentLoaded', function() {
  console.log('History page loaded');

  // Get current type from URL or default to 'all'
  const urlParams = new URLSearchParams(window.location.search);
  const currentType = urlParams.get('type') || 'all';

  // Pagination variables
  const itemsPerPage = 10;
  let currentPage = 1;
  let filteredItems = [];
  let currentTypeFilter = currentType;

  // Get all history items and initialize
  const historyItems = Array.from(document.querySelectorAll('.history-item'));
  console.log('Found history items:', historyItems.length);

  // Define type filter functions first
  function initializeTypeFilters() {
    const typeFilterButtons = document.querySelectorAll('.type-filter-btn');
    console.log('Found type filter buttons:', typeFilterButtons.length);

    typeFilterButtons.forEach(button => {
      button.addEventListener('click', function() {
        console.log('Type filter clicked:', this.dataset.type);

        // Remove active class from all buttons
        typeFilterButtons.forEach(btn => btn.classList.remove('active'));

        // Add active class to clicked button
        this.classList.add('active');

        // Update current type filter
        currentTypeFilter = this.dataset.type;
        console.log('Current type filter set to:', currentTypeFilter);

        // Apply the filter
        applyTypeFilter(currentTypeFilter);

        // Reset search and apply filters
        const searchInput = document.getElementById('history-search');
        if (searchInput) {
          searchInput.value = '';
        }
        filterItems();
      });
    });
  }

  function applyTypeFilter(type) {
    // Apply type filter to all items
    filteredItems = getTypeFilteredItems();
  }

  function getTypeFilteredItems() {
    console.log('Getting type filtered items for:', currentTypeFilter);
    console.log('Total history items:', historyItems.length);

    // Debug: log the data-type of each item
    historyItems.forEach((item, index) => {
      console.log(`Item ${index}: data-type = "${item.dataset.type}"`);
    });

    let filtered;
    if (currentTypeFilter === 'all') {
      filtered = [...historyItems];
    } else if (currentTypeFilter === 'transcription') {
      filtered = historyItems.filter(item => item.dataset.type === 'transcription');
    } else if (currentTypeFilter === 'translation') {
      filtered = historyItems.filter(item => item.dataset.type === 'translation');
    } else {
      filtered = [...historyItems];
    }

    console.log('Filtered items count:', filtered.length);
    return filtered;
  }

  // Initialize type filter buttons
  initializeTypeFilters();

  // Set active filter button based on current type
  document.querySelectorAll('.type-filter-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.dataset.type === currentType) {
      btn.classList.add('active');
    }
  });

  // Apply initial type filter
  applyTypeFilter(currentTypeFilter);

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
    console.log('updatePagination called with filteredItems.length:', filteredItems.length);
    const totalPages = Math.ceil(filteredItems.length / itemsPerPage);

    // Update page info
    document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages || 1}`;

    // Update button states
    document.getElementById('prev-page').disabled = currentPage === 1;
    document.getElementById('next-page').disabled = currentPage === totalPages || totalPages === 0;

    // First, hide ALL history items
    console.log('Hiding all', historyItems.length, 'history items');
    historyItems.forEach(item => {
      item.style.display = 'none';
    });

    // Then show only the filtered items for the current page
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage - 1;

    console.log('Showing filtered items from index', startIndex, 'to', endIndex);
    filteredItems.forEach((item, index) => {
      if (index >= startIndex && index <= endIndex) {
        console.log('Showing item', index, 'with data-type:', item.dataset.type);
        item.style.display = 'block';
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

    // Start with type-filtered items
    let typeFilteredItems = getTypeFilteredItems();

    if (searchTerm === '') {
      // If search is empty, show type-filtered items
      filteredItems = [...typeFilteredItems];
    } else {
      // Filter type-filtered items based on search term
      filteredItems = typeFilteredItems.filter(item => {
        const itemText = item.textContent.toLowerCase();
        return itemText.includes(searchTerm);
      });
    }

    // Reset to first page and update
    currentPage = 1;
    sortItems(sortSelect.value);
    updateStatusText();
  }



  function updateStatusText() {
    const statusText = document.getElementById('status-text');
    if (statusText) {
      const transcriptionCount = historyItems.filter(item =>
        item.dataset.type === 'transcription' &&
        (currentTypeFilter === 'all' || currentTypeFilter === 'transcription') &&
        filteredItems.includes(item)
      ).length;

      const translationCount = historyItems.filter(item =>
        item.dataset.type === 'translation' &&
        (currentTypeFilter === 'all' || currentTypeFilter === 'translation') &&
        filteredItems.includes(item)
      ).length;

      if (currentTypeFilter === 'all') {
        statusText.textContent = `${filteredItems.length} total items (${transcriptionCount} transcriptions, ${translationCount} translations)`;
      } else if (currentTypeFilter === 'transcription') {
        statusText.textContent = `${transcriptionCount} transcriptions found`;
      } else if (currentTypeFilter === 'translation') {
        statusText.textContent = `${translationCount} translations found`;
      }
    }
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
