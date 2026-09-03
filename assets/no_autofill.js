/*
 * Chrome's "Addresses & more" autofill feature reads visible <label> text
 * (not just id/name/autocomplete) to decide a field is a name/address/email
 * field, and deliberately ignores autocomplete="off" once it decides that.
 * The one reliable workaround: keep the field readonly at rest (Chrome won't
 * offer autofill on a readonly field) and remove readonly the instant it's
 * focused, restoring it on blur. Typing feels completely normal to the user.
 *
 * Applies to every .quote-modal-input / .quote-modal-textarea / .form-input /
 * .form-textarea on the site - including ones inserted later by Dash
 * callbacks (product/service detail pages rebuild their content on every
 * item change), via a MutationObserver + event delegation instead of
 * one-time querySelectorAll.
 */
(function () {
    var TARGET_SELECTOR = '.quote-modal-input, .quote-modal-textarea, .form-input, .form-textarea';

    function markReadonly(el) {
        if (!el || el.hasAttribute('readonly')) return;
        if (el === document.activeElement) return; // don't lock the field the user is currently in
        el.setAttribute('readonly', 'readonly');
    }

    function scan(root) {
        if (!root || !root.querySelectorAll) return;
        if (root.matches && root.matches(TARGET_SELECTOR)) markReadonly(root);
        root.querySelectorAll(TARGET_SELECTOR).forEach(markReadonly);
    }

    var observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            mutation.addedNodes.forEach(function (node) {
                if (node.nodeType === 1) scan(node);
            });
        });
    });

    function start() {
        scan(document);
        observer.observe(document.body, { childList: true, subtree: true });

        document.addEventListener('focusin', function (e) {
            if (e.target && e.target.matches && e.target.matches(TARGET_SELECTOR)) {
                e.target.removeAttribute('readonly');
            }
        });

        document.addEventListener('focusout', function (e) {
            if (e.target && e.target.matches && e.target.matches(TARGET_SELECTOR)) {
                e.target.setAttribute('readonly', 'readonly');
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start);
    } else {
        start();
    }
})();