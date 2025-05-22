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

  // Active link highlighting based on scroll position
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link');

  if (sections.length && navLinks.length) {
    window.addEventListener('scroll', () => {
      let current = '';
      const navbarHeight = document.querySelector('.navbar').offsetHeight;

      sections.forEach(section => {
        const sectionTop = section.offsetTop - navbarHeight - 100;
        const sectionHeight = section.offsetHeight;

        if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
          current = section.getAttribute('id');
        }
      });

      navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === `#${current}`) {
          link.classList.add('active');
        }
      });

      // Always keep Home active if no section is active
      if (current === '') {
        navLinks.forEach(link => {
          if (link.getAttribute('href') === '#') {
            link.classList.add('active');
          }
        });
      }
    });
  }

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

  if (typeof window.initializeHistoryDropdown === 'function') {
    console.log('Home.js: Calling global history dropdown initialization');
    window.initializeHistoryDropdown();
  } else {
    console.warn('Home.js: Global history dropdown initialization function not found');
  }

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
