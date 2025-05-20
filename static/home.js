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
});
