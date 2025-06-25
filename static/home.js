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
  const themeOptionsDropdown = document.getElementById('theme-options');

  if (themeToggleBtn && themeOptionsDropdown) {
    themeToggleBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      const isShown = themeOptionsDropdown.classList.toggle('show');
      themeOptionsDropdown.style.display = isShown ? 'block' : 'none';
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (event) => {
      if (!themeToggleBtn.contains(event.target) && !themeOptionsDropdown.contains(event.target)) {
        themeOptionsDropdown.classList.remove('show');
        themeOptionsDropdown.style.display = 'none';
      }
    });
  }

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

  // Handle theme dropdown separately
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const themeOptionsDropdown = document.getElementById('theme-options');

  if (themeToggleBtn && themeOptionsDropdown) {
    // Close theme dropdown when clicking outside
    document.addEventListener('click', (event) => {
      if (!themeToggleBtn.contains(event.target) && !themeOptionsDropdown.contains(event.target)) {
        themeOptionsDropdown.classList.remove('show');
        themeOptionsDropdown.style.display = 'none';
      }
    });
  }
});
