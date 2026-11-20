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

/* Allura Bot open / close.
   Opened by the navbar Allura Bot icon (#open_allubot_btn, toggles) and the
   "Chat with Allura Bot" button on Home (#home_open_chatbot_btn, always opens).
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

/* Scroll reveal (Nov 20, 2026): on public pages, sections and cards fade up as they come into view.
   Styles are in 10_motion.css. Skipped when the visitor's device asks for reduced motion. */
(function () {
    if (!('IntersectionObserver' in window)) { return; }
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) { return; }

    var SELECTOR = [
        '.site-shell .site-section-head',
        '.site-shell .a-card',
        '.site-shell .section-card',
        '.site-shell .category-card',
        '.site-shell .item-tile',
        '.site-shell .tl-item',
        '.site-shell .stat',
        '.site-shell .leader'
    ].join(', ');

    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (!entry.isIntersecting) { return; }
            var el = entry.target;
            el.classList.add('is-in');
            io.unobserve(el);
            // Once it has arrived, hand the element back to its normal hover effects
            setTimeout(function () {
                el.classList.remove('reveal', 'is-in');
                el.style.removeProperty('--reveal-delay');
            }, 1100);
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    function scan() {
        document.querySelectorAll(SELECTOR).forEach(function (el) {
            if (el.dataset.revealed) { return; }
            if (el.closest('.cards-scroll-container, .modal, .reveal')) { return; }   // carousels, pop-ups, nested
            el.dataset.revealed = '1';
            // Cards in the same row arrive one after another
            var siblings = el.parentElement ? Array.prototype.filter.call(el.parentElement.children, function (c) {
                return c.matches(SELECTOR);
            }) : [];
            var i = Math.max(0, siblings.indexOf(el));
            el.style.setProperty('--reveal-delay', (Math.min(i, 5) * 80) + 'ms');
            el.classList.add('reveal');
            io.observe(el);
        });
    }

    var timer = null;
    new MutationObserver(function () {
        clearTimeout(timer);
        timer = setTimeout(scan, 50);
    }).observe(document.body, { childList: true, subtree: true });
    scan();
})();
