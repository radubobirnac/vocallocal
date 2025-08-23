/**
 * Mobile-First Navigation System
 * Handles bottom navigation, slide-up panels, and theme switching
 */

class MobileNavigation {
  constructor() {
    this.activePanel = null;
    this.panels = {};
    this.overlay = null;
    this.bottomNav = null;
    
    this.init();
  }

  init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }

  setup() {
    console.log('Initializing Mobile Navigation System');
    
    // Get DOM elements
    this.bottomNav = document.querySelector('.bottom-nav');
    this.overlay = document.querySelector('.panel-overlay');
    
    // Initialize panels
    this.initializePanels();
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Setup theme system
    this.setupThemeSystem();
    
    // Setup mobile toggles sync
    this.setupMobileToggles();
    
    console.log('Mobile Navigation System initialized');
  }

  initializePanels() {
    const panelElements = document.querySelectorAll('.slide-panel');
    
    panelElements.forEach(panel => {
      const panelId = panel.id.replace('-panel', '').replace('-mobile', '');
      this.panels[panelId] = panel;
    });
  }

  setupEventListeners() {
    // Bottom navigation tabs
    if (this.bottomNav) {
      const navTabs = this.bottomNav.querySelectorAll('.nav-tab');
      navTabs.forEach(tab => {
        tab.addEventListener('click', (e) => this.handleNavTabClick(e));
      });
    }

    // Panel close buttons
    document.querySelectorAll('.panel-close').forEach(btn => {
      btn.addEventListener('click', (e) => this.handlePanelClose(e));
    });

    // Overlay click to close
    if (this.overlay) {
      this.overlay.addEventListener('click', () => this.closeActivePanel());
    }

    // Escape key to close panels
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.activePanel) {
        this.closeActivePanel();
      }
    });

    // Handle panel swipe gestures
    this.setupSwipeGestures();
  }

  handleNavTabClick(event) {
    const tab = event.currentTarget;
    const panelName = tab.dataset.panel;
    
    // Update active tab
    this.setActiveTab(tab);
    
    // Handle panel opening
    if (panelName === 'home') {
      this.closeActivePanel();
    } else {
      this.openPanel(panelName);
    }
  }

  setActiveTab(activeTab) {
    // Remove active state from all tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.dataset.active = 'false';
    });
    
    // Set active state on clicked tab
    activeTab.dataset.active = 'true';
  }

  openPanel(panelName) {
    // Close any currently open panel
    this.closeActivePanel();
    
    const panel = this.panels[panelName];
    if (!panel) return;
    
    // Open new panel
    this.activePanel = panel;
    panel.classList.add('active');
    this.overlay.classList.add('active');
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Announce to screen readers
    panel.setAttribute('aria-hidden', 'false');
  }

  closeActivePanel() {
    if (!this.activePanel) return;
    
    this.activePanel.classList.remove('active');
    this.overlay.classList.remove('active');
    
    // Re-enable body scroll
    document.body.style.overflow = '';
    
    // Announce to screen readers
    this.activePanel.setAttribute('aria-hidden', 'true');
    
    this.activePanel = null;
    
    // Reset home tab as active
    this.setActiveTab(document.querySelector('.nav-tab[data-panel="home"]'));
  }

  handlePanelClose(event) {
    const panelName = event.currentTarget.dataset.panel;
    this.closeActivePanel();
  }

  setupSwipeGestures() {
    let startY = 0;
    let currentY = 0;
    let isDragging = false;

    document.querySelectorAll('.slide-panel').forEach(panel => {
      const panelHeader = panel.querySelector('.panel-header');
      
      panelHeader.addEventListener('touchstart', (e) => {
        startY = e.touches[0].clientY;
        isDragging = true;
      });

      panelHeader.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        
        currentY = e.touches[0].clientY;
        const deltaY = currentY - startY;
        
        if (deltaY > 0) {
          panel.style.transform = `translateY(${deltaY}px)`;
        }
      });

      panelHeader.addEventListener('touchend', (e) => {
        if (!isDragging) return;
        
        const deltaY = currentY - startY;
        
        if (deltaY > 100) {
          // Swipe down to close
          this.closeActivePanel();
        } else {
          // Snap back
          panel.style.transform = '';
        }
        
        isDragging = false;
        panel.style.transform = '';
      });
    });
  }

  setupThemeSystem() {
    // Setup mobile theme toggle button sync with desktop
    this.setupMobileThemeToggleSync();

    // Load and apply saved theme - use same key as desktop system
    const savedTheme = localStorage.getItem('vocal-local-theme') || 'light';
    this.setTheme(savedTheme);
  }

  setTheme(theme) {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme);

    // Save to localStorage using same key as desktop system
    localStorage.setItem('vocal-local-theme', theme);

    // Update desktop theme toggle button icon if it exists
    this.updateDesktopThemeToggleIcon(theme);

    // Trigger theme change event for other components
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));

    // Update legacy theme system if it exists
    if (window.setTheme) {
      window.setTheme(theme);
    }
  }

  setupMobileThemeToggleSync() {
    // Find the desktop theme toggle button
    const desktopThemeToggle = document.getElementById('theme-toggle-btn');

    if (desktopThemeToggle) {
      // Remove any existing event listeners to avoid duplicates
      const newToggleBtn = desktopThemeToggle.cloneNode(true);
      desktopThemeToggle.parentNode.replaceChild(newToggleBtn, desktopThemeToggle);

      // Add unified event listener that works for both mobile and desktop
      newToggleBtn.addEventListener('click', (event) => {
        event.stopPropagation();
        this.toggleTheme();
      });
    }
  }

  toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  }

  updateDesktopThemeToggleIcon(theme) {
    const desktopThemeToggle = document.getElementById('theme-toggle-btn');
    if (desktopThemeToggle) {
      const icon = desktopThemeToggle.querySelector('i');
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
  }



  setupMobileToggles() {
    // Sync mobile bilingual toggle with main toggle
    const mobileToggle = document.getElementById('mobile-bilingual-toggle');
    const mainToggle = document.getElementById('bilingual-mode');
    
    if (mobileToggle && mainToggle) {
      // Sync initial state
      mobileToggle.checked = mainToggle.checked;
      
      // Sync changes
      mobileToggle.addEventListener('change', () => {
        mainToggle.checked = mobileToggle.checked;
        mainToggle.dispatchEvent(new Event('change'));
      });
      
      mainToggle.addEventListener('change', () => {
        mobileToggle.checked = mainToggle.checked;
      });
    }

    // Sync mobile interpretation toggle
    const mobileInterpretation = document.getElementById('mobile-interpretation-toggle');
    const mainInterpretation = document.getElementById('enable-interpretation');
    
    if (mobileInterpretation && mainInterpretation) {
      // Sync initial state
      mobileInterpretation.checked = mainInterpretation.checked;
      
      // Sync changes
      mobileInterpretation.addEventListener('change', () => {
        mainInterpretation.checked = mobileInterpretation.checked;
        mainInterpretation.dispatchEvent(new Event('change'));
      });
      
      mainInterpretation.addEventListener('change', () => {
        mobileInterpretation.checked = mainInterpretation.checked;
      });
    }
  }

  // Public API methods
  isOpen() {
    return this.activePanel !== null;
  }

  getCurrentPanel() {
    return this.activePanel ? this.activePanel.id : null;
  }

  openSpecificPanel(panelName) {
    this.openPanel(panelName);
    
    // Update corresponding nav tab
    const tab = document.querySelector(`[data-panel="${panelName}"]`);
    if (tab) {
      this.setActiveTab(tab);
    }
  }
}

// Initialize the mobile navigation system
window.mobileNav = new MobileNavigation();

// Expose useful functions globally
window.openMobilePanel = (panelName) => {
  window.mobileNav.openSpecificPanel(panelName);
};

window.closeMobilePanel = () => {
  window.mobileNav.closeActivePanel();
};

// Handle orientation changes
window.addEventListener('orientationchange', () => {
  setTimeout(() => {
    if (window.mobileNav.isOpen()) {
      // Recalculate panel positioning if needed
      const activePanel = window.mobileNav.activePanel;
      if (activePanel) {
        activePanel.style.transform = '';
      }
    }
  }, 100);
});

console.log('Mobile Navigation JavaScript loaded successfully');
