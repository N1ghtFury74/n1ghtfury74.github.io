/* ===================================================================
   N1ghtFury — scroll reveal + reading progress
   -------------------------------------------------------------------
   Adds `nf-anim` to <body>, tags a set of elements with `nf-reveal`,
   and adds `nf-in` as each scrolls into view. Also draws a reading
   progress bar on pages long enough for one to be useful.

   Matching CSS lives in stylesheets/nightfury_animations.css and
   stylesheets/nightfury_components.css, scoped to `body.nf-anim`, so
   this script is purely additive:

     - no IntersectionObserver support  -> body class never added, nothing hides
     - prefers-reduced-motion: reduce   -> body class never added, nothing hides
     - script fails to load             -> body class never added, nothing hides

   In every failure case the page renders fully, just without motion.
   =================================================================== */

(function () {
  "use strict";

  /* Elements worth revealing, across every page type. Each selector is
     tagged independently; siblings cascade via :nth-child in the CSS. */
  var SELECTORS = [
    /* home */
    ".nf-section__title",
    ".nf-section__lead",
    ".nf-topic-pills",
    ".nf-post-card",
    ".nf-cat-chip",
    ".md-typeset .grid.cards > ul > li",
    /* about */
    ".nf-profile",
    ".nf-stat",
    ".nf-skills-group",
    ".nf-tooling",
    ".nf-timeline__item",
    ".nf-cert-badge",
    ".nf-contact-item",
    /* blog index / category / archive */
    "article.md-post",
    ".md-post--excerpt",
    /* post body */
    ".md-typeset img[src$='.svg']",
    ".md-typeset h2",
    ".md-typeset table:not([class])",
    ".md-typeset .admonition"
  ].join(", ");

  /* Teardown for listeners registered on the previous document, so
     instant navigation does not stack handlers. */
  var cleanup = [];

  function teardown() {
    while (cleanup.length) {
      try {
        cleanup.pop()();
      } catch (e) {
        /* never let teardown break the page */
      }
    }
  }

  function prefersReducedMotion() {
    return (
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function supported() {
    return (
      "IntersectionObserver" in window &&
      typeof document.querySelectorAll === "function" &&
      !prefersReducedMotion()
    );
  }

  /* ----------------------------------------------------------------
     Scroll reveal
     ---------------------------------------------------------------- */
  function initReveal() {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("nf-in");
          /* Reveal once, then stop watching — no re-hide on scroll up. */
          observer.unobserve(entry.target);
        });
      },
      {
        /* Trigger slightly before the element reaches the viewport edge
           so the motion finishes as it arrives rather than after. */
        rootMargin: "0px 0px -8% 0px",
        threshold: 0.08
      }
    );

    Array.prototype.forEach.call(
      document.querySelectorAll(SELECTORS),
      function (node) {
        /* The hero runs its own CSS entrance — never double-animate it. */
        if (node.closest && node.closest(".nf-hero")) return;
        if (node.classList.contains("nf-reveal")) return;

        node.classList.add("nf-reveal");
        observer.observe(node);
      }
    );

    cleanup.push(function () {
      observer.disconnect();
    });

    /* Safety net: if anything is still unrevealed after 3s (an observer
       that never fired, a container with zero height at tag time), show
       it unconditionally. Content must never be stuck invisible. */
    var timer = window.setTimeout(function () {
      Array.prototype.forEach.call(
        document.querySelectorAll(".nf-reveal:not(.nf-in)"),
        function (node) {
          node.classList.add("nf-in");
        }
      );
    }, 3000);

    cleanup.push(function () {
      window.clearTimeout(timer);
    });
  }

  /* ----------------------------------------------------------------
     Reading progress
     Only drawn where the page is meaningfully longer than the viewport,
     so short pages do not get a bar that is always full.
     ---------------------------------------------------------------- */
  function initProgress() {
    var doc = document.documentElement;
    var scrollable = doc.scrollHeight - window.innerHeight;

    if (scrollable < window.innerHeight * 0.6) return;

    var bar = document.createElement("div");
    bar.className = "nf-progress";
    document.body.appendChild(bar);

    var ticking = false;

    function update() {
      var max = doc.scrollHeight - window.innerHeight;
      var pct = max > 0 ? (window.pageYOffset / max) * 100 : 0;
      if (pct < 0) pct = 0;
      if (pct > 100) pct = 100;
      bar.style.setProperty("--nf-progress", pct.toFixed(2) + "%");
      ticking = false;
    }

    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(update);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    update();

    cleanup.push(function () {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (bar.parentNode) bar.parentNode.removeChild(bar);
    });
  }

  function init() {
    teardown();
    if (!supported()) return;

    document.body.classList.add("nf-anim");
    initReveal();
    initProgress();
  }

  /* Material's instant navigation swaps the <article> without a page load,
     so re-run on every document emission. `document$` is provided by
     mkdocs-material; fall back to a plain DOM-ready listener without it. */
  if (typeof window.document$ !== "undefined" && window.document$.subscribe) {
    window.document$.subscribe(init);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
