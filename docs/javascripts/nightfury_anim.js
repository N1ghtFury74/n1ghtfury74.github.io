/* ===================================================================
   N1ghtFury — scroll motion
   -------------------------------------------------------------------
   Three jobs:

     1. Scroll reveal. Adds `nf-anim` to <body>, tags elements with
        `nf-reveal` plus a variant class, and adds `nf-in` as each
        scrolls into view.
     2. Stagger. Writes `--nf-i` on each revealed element: its index
        among its *revealed* siblings. CSS turns that into a delay, so
        a row of cards cascades. This has to be computed here, because
        `:nth-child` counts every sibling — in an article body the
        third child might be a paragraph, so an h2 would inherit a
        delay for no reason.
     3. Scroll position. Writes `--nf-sy` on <body>: how far the first
        viewport has been scrolled, 0 to 1. CSS uses it to drift and
        dim the hero as the reader leaves it, which gives the page a
        sense of depth without a second scroll listener.

   Matching CSS lives in stylesheets/nightfury_animations.css, scoped
   to `body.nf-anim`, so this script is purely additive:

     - no IntersectionObserver support  -> body class never added, nothing hides
     - prefers-reduced-motion: reduce   -> body class never added, nothing hides
     - script fails to load             -> body class never added, nothing hides

   In every failure case the page renders fully, just without motion.
   `--nf-sy` defaults to 0 in the CSS, which is the resting hero.
   =================================================================== */

(function () {
  "use strict";

  /* Element families, each with the motion that suits it. A heading
     slides in from the side, a card lifts, a diagram scales up. One
     generic rise applied to everything is what makes a site read as a
     template. */
  var GROUPS = [
    {
      /* Anything in a grid or a row: lift and settle */
      variant: "nf-reveal--lift",
      selector: [
        ".nf-post-card",
        ".nf-cat-chip",
        ".nf-stat",
        ".nf-cert-badge",
        ".nf-contact-item",
        ".md-typeset .grid.cards > ul > li",
        ".md-typeset .grid > .card"
      ].join(", ")
    },
    {
      /* Headings: draw in from the left, with the accent rule growing */
      variant: "nf-reveal--slide",
      selector: [".nf-section__title", ".md-typeset h2"].join(", ")
    },
    {
      /* The post diagrams are the centrepiece of a write-up — scale up */
      variant: "nf-reveal--zoom",
      selector: ".md-typeset img[src$='.svg']"
    },
    {
      /* Blocks that interrupt prose: a short, quiet rise */
      variant: "nf-reveal--rise",
      selector: [
        ".nf-section__lead",
        ".nf-topic-pills",
        ".nf-profile",
        ".nf-skills",
        ".nf-tooling",
        ".nf-timeline__item",
        "article.md-post",
        ".md-post--excerpt",
        ".md-typeset table:not([class])",
        ".md-typeset .admonition",
        ".md-typeset details",
        ".md-typeset .tabbed-set",
        /* Direct child only: a code block nested in an inactive tab
           panel is display:none, so it would never intersect and would
           sit waiting on the 3s safety net. */
        ".md-typeset > .highlight"
      ].join(", ")
    }
  ];

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

    var tagged = [];

    /* Pass one: tag. */
    GROUPS.forEach(function (group) {
      Array.prototype.forEach.call(
        document.querySelectorAll(group.selector),
        function (node) {
          /* The hero runs its own CSS entrance — never double-animate it. */
          if (node.closest && node.closest(".nf-hero")) return;
          if (node.classList.contains("nf-reveal")) return;

          node.classList.add("nf-reveal", group.variant);
          tagged.push(node);
        }
      );
    });

    /* Pass two: stagger. Only correct once every element is tagged,
       because the index counts tagged siblings. Capped so a long run of
       cards or code blocks never waits most of a second to appear. */
    tagged.forEach(function (node) {
      var i = 0;
      var sib = node.previousElementSibling;

      while (sib) {
        if (sib.classList.contains("nf-reveal")) i++;
        sib = sib.previousElementSibling;
      }

      if (i > 5) i = 5;
      if (i > 0) node.style.setProperty("--nf-i", String(i));
    });

    /* Pass three: observe. */
    tagged.forEach(function (node) {
      observer.observe(node);
    });

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
     Scroll position: reading progress, and the hero depth cue.

     Both live in one rAF-throttled handler. The progress bar is only
     drawn where the page is meaningfully longer than the viewport, so
     short pages do not get a bar that is always full. `--nf-sy` is
     written only where there is a hero to move.
     ---------------------------------------------------------------- */
  function initScroll() {
    var doc = document.documentElement;
    var hero = document.querySelector(".nf-hero");
    var scrollable = doc.scrollHeight - window.innerHeight;
    var bar = null;

    if (scrollable >= window.innerHeight * 0.6) {
      bar = document.createElement("div");
      bar.className = "nf-progress";
      document.body.appendChild(bar);
    }

    if (!bar && !hero) return;

    var ticking = false;

    function update() {
      var y = window.pageYOffset;

      if (bar) {
        var max = doc.scrollHeight - window.innerHeight;
        var pct = max > 0 ? (y / max) * 100 : 0;
        if (pct < 0) pct = 0;
        if (pct > 100) pct = 100;
        bar.style.setProperty("--nf-progress", pct.toFixed(2) + "%");
      }

      if (hero) {
        /* 0 at the top, 1 once the first viewport has gone by. Clamped
           both ways, so overscroll on a trackpad cannot push the hero
           past its end state or back above its start. */
        var span = window.innerHeight * 0.9;
        var sy = span > 0 ? y / span : 0;
        if (sy < 0) sy = 0;
        if (sy > 1) sy = 1;
        document.body.style.setProperty("--nf-sy", sy.toFixed(3));
      }

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
      document.body.style.removeProperty("--nf-sy");
      if (bar && bar.parentNode) bar.parentNode.removeChild(bar);
    });
  }

  function init() {
    teardown();
    if (!supported()) return;

    document.body.classList.add("nf-anim");
    initReveal();
    initScroll();
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
