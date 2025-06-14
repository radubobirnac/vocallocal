// Navigation active state management
// This script handles navigation highlighting across all pages

document.addEventListener('DOMContentLoaded', () => {
  // Navigation active state management
  function updateActiveNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section[id]');
    const currentPath = window.location.pathname;
    const currentHash = window.location.hash;

    // Remove active class from all links
    navLinks.forEach(link => link.classList.remove('active'));

    // Determine which page we're on based on the URL
    let currentPage = 'home'; // default

    if (currentPath.includes('/try_it_free') || currentPath.includes('/try-it-free')) {
      currentPage = 'try_it_free';
    } else if (currentPath.includes('/dashboard')) {
      currentPage = 'dashboard';
    } else if (currentPath.includes('/history')) {
      currentPage = 'history';
    } else if (currentPath.includes('/profile')) {
      currentPage = 'profile';
    } else if (currentPath === '/' || currentPath === '/home' || currentPath === '/main' || currentPath === '' || currentPath.includes('/index')) {
      currentPage = 'home';
    }

    // If we're on a specific page (not home), activate the corresponding link
    if (currentPage !== 'home') {
      const pageLink = document.querySelector(`[data-page="${currentPage}"]`);
      if (pageLink) {
        pageLink.classList.add('active');
        return;
      }
    }

    // If we're on the home page, handle section-based navigation
    if (currentPage === 'home') {
      // If there's a hash in the URL, activate the corresponding section link
      if (currentHash) {
        const sectionId = currentHash.substring(1); // Remove the #
        const sectionLink = document.querySelector(`[data-section="${sectionId}"]`);
        if (sectionLink) {
          sectionLink.classList.add('active');
          return;
        }
      }

      // Handle scroll-based navigation for sections (only on home page)
      if (sections.length > 0) {
        let current = '';
        const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 0;

        sections.forEach(section => {
          const sectionTop = section.offsetTop - navbarHeight - 100;
          const sectionHeight = section.offsetHeight;

          if (window.scrollY >= sectionTop && window.scrollY < sectionTop + sectionHeight) {
            current = section.getAttribute('id');
          }
        });

        // Activate the link for the current section
        if (current) {
          const currentSectionLink = document.querySelector(`[data-section="${current}"]`);
          if (currentSectionLink) {
            currentSectionLink.classList.add('active');
            return;
          }
        }
      }

      // Default to Home if no section is active and we're on the home page
      const homeLink = document.querySelector('[data-page="home"]');
      if (homeLink) homeLink.classList.add('active');
    }
  }

  // Initialize navigation on page load
  updateActiveNavigation();

  // Update navigation on scroll (for section-based navigation on home page)
  if (document.querySelectorAll('section[id]').length > 0) {
    let scrollTimeout;
    window.addEventListener('scroll', () => {
      // Throttle scroll events for better performance
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(updateActiveNavigation, 50);
    });
  }

  // Update navigation on hash change (for direct section links)
  window.addEventListener('hashchange', updateActiveNavigation);

  // Handle navigation link clicks for smooth scrolling to sections
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return; // Skip if it's just "#"

      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        e.preventDefault();
        
        // Add offset for fixed navbar
        const navbarHeight = document.querySelector('.navbar')?.offsetHeight || 0;
        const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - navbarHeight;

        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth'
        });

        // Update URL hash
        history.pushState(null, null, targetId);
        
        // Update navigation immediately
        setTimeout(updateActiveNavigation, 100);
      }
    });
  });

  // Debug logging
  console.log('Navigation script initialized');
  console.log('Current path:', window.location.pathname);
  console.log('Current hash:', window.location.hash);
});
