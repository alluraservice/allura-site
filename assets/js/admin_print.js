/*
 * One-page A4 printing for the Reports & Analytics page.
 *
 * How the fit works:
 *   1. The sheet is laid out at A4 content width (194mm) and its natural height is measured.
 *   2. If it's taller than one page, it is laid out a little WIDER (width / scale) and then shrunk
 *      with transform: scale(), so after scaling it is exactly one page wide and at most one page tall.
 *      Transforms don't change layout size, so negative margins remove the space the shrink frees up.
 *   3. Charts are redrawn at the new width and the fit is measured again.
 *   60_report.css also fixes <html>/<body> to one page in print and clips the rest, so a
 *   second page can never appear even if a chart redraws slightly taller.
 * Dash loads every .js file in /assets automatically.
 */
(function () {
    var MM = 96 / 25.4;                    // CSS px per mm
    var PAGE_W = 194 * MM;                 // A4 width 210mm minus 8mm side margins
    var PAGE_H = (297 - 16) * MM - 16;     // A4 height minus 8mm top/bottom margins, with a safety gap

    function sheet() { return document.querySelector('.report-sheet'); }

    function resizePlots(el) {
        if (!el || !window.Plotly) return;
        el.querySelectorAll('.js-plotly-plot').forEach(function (p) {
            try { window.Plotly.Plots.resize(p); } catch (e) { /* ignore */ }
        });
    }

    function clearFit(el) {
        el.style.transform = '';
        el.style.width = '';
        el.style.marginBottom = '';
        el.style.marginRight = '';
    }

    function fitToPage(el) {
        clearFit(el);
        // Find the scale z where (height at width PAGE_W / z) * z == one page. A wider layout is shorter,
        // so this converges; damping avoids bouncing between two values.
        var z = 1, w = PAGE_W, h = 0;
        for (var i = 0; i < 14; i++) {
            w = PAGE_W / z;
            el.style.width = w + 'px';
            h = el.offsetHeight;                        // layout height, unaffected by transform
            var next = Math.min(1, PAGE_H / h);
            if (Math.abs(next - z) < 0.002) { z = next; break; }
            z = (z + next) / 2;
        }
        w = PAGE_W / z;
        el.style.width = w + 'px';
        h = el.offsetHeight;
        if (h * z > PAGE_H) { z = PAGE_H / h; }         // never taller than the page (may leave a hair of side margin)
        if (z < 1) {
            el.style.transform = 'scale(' + z.toFixed(4) + ')';
            el.style.marginBottom = (-(h * (1 - z))) + 'px';
            el.style.marginRight = (-(w * (1 - z))) + 'px';
        }
        return z;
    }

    function prepare() {
        var el = sheet();
        if (!el) return null;
        document.body.classList.add('printing-report');
        fitToPage(el);
        resizePlots(el);
        return el;
    }

    function restore() {
        var el = sheet();
        document.body.classList.remove('printing-report');
        if (el) {
            clearFit(el);
            setTimeout(function () { resizePlots(el); }, 50);
        }
    }

    // Print button: lay out, let Plotly redraw at the new width, re-check the fit, then print
    window.alluraPrintReport = function () {
        var el = prepare();
        if (!el) { window.print(); return; }
        setTimeout(function () {
            fitToPage(el);
            resizePlots(el);
            setTimeout(function () { fitToPage(el); window.print(); }, 250);
        }, 450);
    };

    // Ctrl+P / browser menu on the analytics page: same layout, best effort
    window.addEventListener('beforeprint', function () {
        if (sheet() && !document.body.classList.contains('printing-report')) { prepare(); }
    });
    window.addEventListener('afterprint', restore);
})();