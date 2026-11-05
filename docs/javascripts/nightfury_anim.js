/* ===================================================================
   N1ghtFury — scroll reveal
   -------------------------------------------------------------------
   Adds `nf-anim` to <body>, tags a set of elements with `nf-reveal`,
   and adds `nf-in` as each scrolls into view. The matching CSS lives in
   stylesheets/nightfury_animations.css and is scoped entirely to
   `body.nf-anim`, so this script is purely additive:

     - no IntersectionObserver support  -> body class never added, nothing hides
     - prefers-reduced-motion: reduce   -> body class never added, nothing hides
     - script fails to load             -> body class never added, nothing hides

   In every failure case the page renders fully, just without motion.
   =================================================================== */

(function () {
  "use strict";

  /* Elements worth revealing. Order does not matter; each selector is
     tagged independently and siblings cascade via :nth-child in the CSS. */
  var SELECTORS = [
    ".nf-section__title",
    ".nf-section__lead",
    ".nf-topic-pills",
    ".md-typeset .grid.cards > ul > li",
    ".nf-profile",
    ".nf-stat",
    ".nf-skills-group",
    ".nf-tooling",
    ".nf-timeline__item",
    ".nf-cert-badge",
    ".nf-contact-item",
    ".md-typeset img[src$='.svg']",
    "article.md-post"
  ].join(", ");

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

  function init() {
    if (!supported()) return;

    document.body.classList.add("nf-anim");

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

    var nodes = document.querySelectorAll(SELECTORS);

    Array.prototype.forEach.call(nodes, function (node) {
      /* The hero runs its own CSS entrance — never double-animate it. */
      if (node.closest && node.closest(".nf-hero")) return;
      if (node.classList.contains("nf-reveal")) return;

      node.classList.add("nf-reveal");
      observer.observe(node);
    });

    /* Safety net: if anything is still unrevealed after 3s (an observer
       that never fired, a container with zero height at tag time), show
       it unconditionally. Content must never be stuck invisible. */
    window.setTimeout(function () {
      Array.prototype.forEach.call(
        document.querySelectorAll(".nf-reveal:not(.nf-in)"),
        function (node) {
          node.classList.add("nf-in");
        }
      );
    }, 3000);
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
