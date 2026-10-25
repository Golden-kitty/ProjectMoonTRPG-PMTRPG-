/* Reading aids progressively enhance Material; navigation and search stay native. */
(() => {
  "use strict";

  let article = null;
  let progress = null;
  let backTop = null;
  let pending = false;
  let observer = null;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function updateProgress() {
    pending = false;
    if (!article || !progress) return;
    const articleTop = article.getBoundingClientRect().top + window.scrollY;
    const readableHeight = article.offsetHeight - window.innerHeight + 90;
    const fraction = readableHeight > 0
      ? Math.max(0, Math.min(1, (window.scrollY - articleTop + 90) / readableHeight))
      : 0;
    progress.style.transform = `scaleX(${fraction})`;
    if (backTop) backTop.hidden = window.scrollY < 600;
  }

  function queueProgress() {
    if (!pending) {
      pending = true;
      window.requestAnimationFrame(updateProgress);
    }
  }

  function updateTableScroll() {
    document.querySelectorAll(".md-typeset .pmtrpg-table-scroll").forEach((wrapper) => {
      const overflows = wrapper.scrollWidth > wrapper.clientWidth + 2;
      wrapper.dataset.overflow = String(overflows);
      if (overflows) {
        wrapper.tabIndex = 0;
        wrapper.setAttribute("role", "region");
        if (!wrapper.hasAttribute("aria-label")) {
          wrapper.setAttribute("aria-label", "规则表格，可横向滚动；键盘聚焦后使用左右方向键");
        }
      } else {
        wrapper.removeAttribute("tabindex");
      }
    });
    queueProgress();
  }

  function initialise() {
    article = document.querySelector(".md-content__inner");
    progress = document.querySelector(".pm-reading-progress span");
    backTop = document.querySelector(".pm-back-top");
    if (backTop && !backTop.dataset.ready) {
      backTop.dataset.ready = "true";
      backTop.addEventListener("click", () => {
        const heading = article && article.querySelector("h1, h2");
        if (heading) {
          heading.tabIndex = -1;
          heading.focus({ preventScroll: true });
        }
        window.scrollTo({ top: 0, behavior: reducedMotion.matches ? "auto" : "smooth" });
      });
    }
    if (observer) observer.disconnect();
    if ("ResizeObserver" in window && article) {
      observer = new ResizeObserver(updateTableScroll);
      observer.observe(article);
      article.querySelectorAll(".pmtrpg-table-scroll").forEach((wrapper) => observer.observe(wrapper));
    }
    updateTableScroll();
  }

  window.addEventListener("scroll", queueProgress, { passive: true });
  window.addEventListener("resize", updateTableScroll, { passive: true });
  if (typeof document$ !== "undefined") document$.subscribe(initialise);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialise);
  else initialise();
})();
