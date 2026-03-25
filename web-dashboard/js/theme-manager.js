/**
 * Theme Manager Module
 * Handles light/dark mode switching and persistence
 */

export class ThemeManager {
    constructor() {
        this.currentTheme = this.loadTheme();
        this.themeToggleBtn = null;
        this.themeIcon = null;
        
        console.log('ThemeManager initialized with theme:', this.currentTheme);
    }

    /**
     * Initialize theme manager
     */
    initialize() {
        // Apply saved theme
        this.applyTheme(this.currentTheme);
        
        // Setup theme toggle button
        this.themeToggleBtn = document.getElementById('theme-toggle');
        this.themeIcon = this.themeToggleBtn?.querySelector('.theme-icon');
        
        if (this.themeToggleBtn) {
            this.themeToggleBtn.addEventListener('click', () => this.toggleTheme());
            this.updateIcon();
        }
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!this.hasUserPreference()) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
        
        console.log('Theme manager initialized');
    }

    /**
     * Load theme from localStorage or system preference
     */
    loadTheme() {
        // Check localStorage first
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            return savedTheme;
        }
        
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    }

    /**
     * Check if user has set a theme preference
     */
    hasUserPreference() {
        return localStorage.getItem('theme') !== null;
    }

    /**
     * Apply theme to document
     */
    applyTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        this.updateIcon();
        console.log('Theme applied:', theme);
    }

    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        this.saveTheme(newTheme);
        
        // Show notification
        this.showThemeNotification(newTheme);
    }

    /**
     * Save theme to localStorage
     */
    saveTheme(theme) {
        localStorage.setItem('theme', theme);
        console.log('Theme saved:', theme);
    }

    /**
     * Update theme toggle icon and label
     */
    updateIcon() {
        if (!this.themeToggleBtn) return;
        const isDark = this.currentTheme === 'dark';
        const icon = this.themeToggleBtn.querySelector('.theme-icon');
        const label = this.themeToggleBtn.querySelector('.theme-label');
        if (icon) icon.textContent = isDark ? '☀️' : '🌙';
        if (label) label.textContent = isDark ? 'Light Mode' : 'Dark Mode';
        this.themeToggleBtn.setAttribute('aria-label',
            `Switch to ${isDark ? 'light' : 'dark'} mode`);
    }

    /**
     * Show theme change notification
     */
    showThemeNotification(theme) {
        const message = theme === 'dark' ? '🌙 Dark mode enabled' : '☀️ Light mode enabled';
        
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'theme-notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            padding: 12px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-shadow: var(--shadow-lg);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 2 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    /**
     * Get current theme
     */
    getCurrentTheme() {
        return this.currentTheme;
    }

    /**
     * Set theme programmatically
     */
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.applyTheme(theme);
            this.saveTheme(theme);
        }
    }
}

// Add notification animations to document
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
