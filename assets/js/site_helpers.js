/* Small page helpers.
   - /home?login=1 (where signed-out visitors to /admin are sent) opens the Login pop-up automatically.
   Dash loads every .js file in /assets automatically. */
(function () {
    function openLoginIfAsked() {
        if (!/[?&]login=1\b/.test(window.location.search)) return;
        var tries = 0;
        var timer = setInterval(function () {
            var btn = document.getElementById('btn-open-login-modal');
            if (btn) {
                clearInterval(timer);
                btn.click();
                if (window.history && window.history.replaceState) {
                    window.history.replaceState(null, '', window.location.pathname);
                }
            } else if (++tries > 40) {
                clearInterval(timer);
            }
        }, 150);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', openLoginIfAsked);
    } else {
        openLoginIfAsked();
    }
})();

// Wait for Dash components to mount on page changes
const observeCarousel = () => {
    const observer = new MutationObserver(() => {
        const scrollContainer = document.querySelector('.cards-scroll-container');
        const prevBtn = document.querySelector('.carousel-btn-left');
        const nextBtn = document.querySelector('.carousel-btn-right');

        if (scrollContainer && prevBtn && nextBtn && !scrollContainer.dataset.navAttached) {
            scrollContainer.dataset.navAttached = "true";

            function updateNavButtons() {
                const scrollLeft = scrollContainer.scrollLeft;
                const maxScrollLeft = scrollContainer.scrollWidth - scrollContainer.clientWidth;

                // Hide left button at start
                if (scrollLeft <= 1) {
                    prevBtn.classList.add('hidden');
                } else {
                    prevBtn.classList.remove('hidden');
                }

                // Hide right button at end
                if (scrollLeft >= maxScrollLeft - 1) {
                    nextBtn.classList.add('hidden');
                } else {
                    nextBtn.classList.remove('hidden');
                }
            }

            // Click event listeners to scroll and update button visibility
            nextBtn.addEventListener('click', () => {
                scrollContainer.scrollBy({ left: 280, behavior: 'smooth' });
                setTimeout(updateNavButtons, 300); // Sync visibility after animation
            });

            prevBtn.addEventListener('click', () => {
                scrollContainer.scrollBy({ left: -280, behavior: 'smooth' });
                setTimeout(updateNavButtons, 300); // Sync visibility after animation
            });

            // Listen for manual scroll & window resize events
            scrollContainer.addEventListener('scroll', updateNavButtons);
            window.addEventListener('resize', updateNavButtons);

            // Initial check on load
            updateNavButtons();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', observeCarousel);
} else {
    observeCarousel();
}

/* AlluBot open / close.
   Opened by the navbar AlluBot icon (#open_allubot_btn, toggles) and the
   "Chat with AlluBot" button on Home (#home_open_chatbot_btn, always opens).
   Done in the browser so it works on every page without extra callbacks. */
(function () {
    function panel() { return document.getElementById('allubot-panel'); }

    function setOpen(open) {
        var p = panel();
        if (!p) { return; }
        p.classList.toggle('open', open);
        p.setAttribute('aria-hidden', open ? 'false' : 'true');
        if (open) {
            setTimeout(function () {
                var box = document.getElementById('allubot-messages');
                if (box) { box.scrollTop = box.scrollHeight; }
            }, 180);
        }
    }

    document.addEventListener('click', function (e) {
        var opener = e.target.closest('#open_allubot_btn, #home_open_chatbot_btn');
        if (opener) {
            e.preventDefault();
            var p = panel();
            var isOpen = p && p.classList.contains('open');
            setOpen(opener.id === 'open_allubot_btn' ? !isOpen : true);
            return;
        }
        if (e.target.closest('#allubot-close')) {
            setOpen(false);
            return;
        }
        // Following a link inside the chat on a phone: close so the page is visible
        if (e.target.closest('.allubot-link') && window.matchMedia('(max-width: 599px)').matches) {
            setOpen(false);
        }
    });

    document.addEventListener('keydown', function (e) {
        var p = panel();
        if (e.key === 'Escape' && p && p.classList.contains('open')) { setOpen(false); }
    });
})();