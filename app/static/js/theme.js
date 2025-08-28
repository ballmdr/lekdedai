// Theme JavaScript functions adapted from v0.app theme

// Initialize current date display
document.addEventListener('DOMContentLoaded', function() {
    // Set current date in Thai format
    const currentDateElement = document.getElementById('current-date');
    if (currentDateElement) {
        const today = new Date();
        const thaiDate = today.toLocaleDateString('th-TH', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
        currentDateElement.textContent = thaiDate;
    }
    
    // Initialize countdown timer
    initializeCountdownTimer();
    
    // Add loading animation styles
    addLoadingStyles();
});

// Countdown timer function
function initializeCountdownTimer() {
    const countdownElement = document.getElementById('countdown-timer');
    if (countdownElement) {
        // Set target date (example: next lottery draw)
        const targetDate = new Date();
        targetDate.setDate(targetDate.getDate() + 5); // 5 days from now
        targetDate.setHours(15, 30, 0, 0); // 3:30 PM
        
        function updateCountdown() {
            const now = new Date();
            const difference = targetDate.getTime() - now.getTime();
            
            if (difference > 0) {
                const days = Math.floor(difference / (1000 * 60 * 60 * 24));
                const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((difference % (1000 * 60)) / 1000);
                
                countdownElement.textContent = `${days} วัน ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            } else {
                countdownElement.textContent = 'หมดเวลาแล้ว';
            }
        }
        
        // Update immediately and then every second
        updateCountdown();
        setInterval(updateCountdown, 1000);
    }
}

// Add custom loading animation styles
function addLoadingStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .animate-spin {
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            from {
                transform: rotate(0deg);
            }
            to {
                transform: rotate(360deg);
            }
        }
        
        .card-hover {
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        
        .card-hover:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }
        
        .feature-card-1 {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .feature-card-2 {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .feature-card-3 {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        .feature-card-4 {
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
        
        .lucky-number {
            background: linear-gradient(135deg, #FFD700, #FFA500);
            border: 3px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(255, 215, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }
        
        .countdown-timer {
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    `;
    document.head.appendChild(style);
}

// Theme utilities
const ThemeUtils = {
    // Get CSS custom property value
    getCSSVariable: function(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    },
    
    // Set CSS custom property value
    setCSSVariable: function(name, value) {
        document.documentElement.style.setProperty(name, value);
    },
    
    // Toggle dark mode
    toggleDarkMode: function() {
        document.documentElement.classList.toggle('dark');
        const isDark = document.documentElement.classList.contains('dark');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    },
    
    // Initialize theme from localStorage
    initTheme: function() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.documentElement.classList.add('dark');
        } else if (savedTheme === 'light') {
            document.documentElement.classList.remove('dark');
        } else {
            // Auto detect based on system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.documentElement.classList.add('dark');
            }
        }
    }
};

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
    ThemeUtils.initTheme();
});

// Export for global access
window.ThemeUtils = ThemeUtils;