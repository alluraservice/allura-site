// Wait for Dash components to mount on page changes
const observeCarousel = () => {
    const observer = new MutationObserver(() => {
        const scrollContainer = document.querySelector('.cards-scroll-container');
        const prevBtn = document.querySelector('.nav-left');
        const nextBtn = document.querySelector('.nav-right');

        if (scrollContainer && prevBtn && nextBtn && !scrollContainer.dataset.navAttached) {
            // Mark as attached so we don't attach duplicate listeners
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

            // Listen for scroll & window resize events
            scrollContainer.addEventListener('scroll', updateNavButtons);
            window.addEventListener('resize', updateNavButtons);

            // Initial check
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