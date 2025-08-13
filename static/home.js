// Home page specific JavaScript

document.addEventListener('DOMContentLoaded', () => {
  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();

      const targetId = this.getAttribute('href');
      if (targetId === '#') return; // Skip if it's just "#"

      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        // Add offset for fixed navbar
        const navbarHeight = document.querySelector('.navbar').offsetHeight;
        const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - navbarHeight;

        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });
      }
    });
  });

  // Navbar scroll effect
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        navbar.classList.add('navbar-scrolled');
      } else {
        navbar.classList.remove('navbar-scrolled');
      }
    });
  }

  // Navigation is now handled by navigation.js

  // Feature card hover effect
  const featureCards = document.querySelectorAll('.feature-card');
  featureCards.forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.classList.add('feature-card-hover');
    });

    card.addEventListener('mouseleave', () => {
      card.classList.remove('feature-card-hover');
    });
  });

  // Theme toggle functionality
  const themeToggleBtn = document.getElementById('theme-toggle-btn');

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      toggleTheme();
    });
  }

  // Function to toggle between light and dark themes
  function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
  }

  // Function to apply the selected theme
  function applyTheme(theme) {
    // Apply the theme class to the <html> element
    document.documentElement.setAttribute('data-theme', theme);

    // Update the toggle button icon
    if (themeToggleBtn) {
      const icon = themeToggleBtn.querySelector('i');
      if (icon) {
        if (theme === 'light') {
          // Show moon icon when in light mode (clicking will switch to dark)
          icon.className = 'fas fa-moon';
        } else {
          // Show sun icon when in dark mode (clicking will switch to light)
          icon.className = 'fas fa-sun';
        }
      }
    }

    // Save theme preference
    try {
      localStorage.setItem('vocal-local-theme', theme);
    } catch (e) {
      console.warn('LocalStorage is not available.');
    }
  }

  // Function to load the saved theme or default to light
  function loadTheme() {
    let savedTheme = 'light'; // Default to light
    try {
      savedTheme = localStorage.getItem('vocal-local-theme') || 'light';
    } catch (e) {
      console.warn('LocalStorage is not available. Defaulting to light theme.');
    }
    applyTheme(savedTheme);
  }

  // Load saved theme on page load
  loadTheme();

  // Initialize dropdowns for authenticated users using global functions
  console.log('Home.js: Checking for authenticated user dropdowns');

  // Use the global functions to initialize dropdowns
  if (typeof window.initializeProfileDropdown === 'function') {
    console.log('Home.js: Calling global profile dropdown initialization');
    window.initializeProfileDropdown();
  } else {
    console.warn('Home.js: Global profile dropdown initialization function not found');
  }

  // History is now consolidated under Profile dropdown, no separate History dropdown needed

  // Theme dropdown handling is now consolidated above with the main theme toggle functionality
});
