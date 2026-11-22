"use strict";
(() => {
  const stats = JSON.parse(document.getElementById("dragon-stats").textContent);
  const calendar = stats.version === 2;
  const unit = calendar ? "contributions" : "commits";
  const total = calendar ? stats.total_contributions : stats.total_commits;
  const recent = calendar ? stats.recent_contributions : stats.recent_commits;
  const artwork = document.getElementById("artwork");
  const svg = artwork.querySelector("svg");
  const buttons = [...document.querySelectorAll("[data-feature]")];
  const title = document.getElementById("detail-title");
  const value = document.getElementById("detail-value");
  const copy = document.getElementById("detail-copy");
  const number = n => n.toLocaleString();
  document.getElementById("features").hidden = false;
  buttons.forEach(button => button.setAttribute("aria-controls", "inspection"));
  const tooltip = document.getElementById("paper-tooltip");
  function showTooltip() {
    if (tooltip.querySelector("strong").textContent !== title.textContent)
      tooltip.querySelector("strong").textContent = title.textContent;
    if (tooltip.querySelector("span").textContent !== value.textContent)
      tooltip.querySelector("span").textContent = value.textContent;
    tooltip.hidden = false;
  }
  let displayed;
  let selected = "growth";
  function inspect(feature) {
    let heading, amount, explanation;
    if (feature.startsWith("language-")) {
      const language = stats.palette[Number(feature.slice(9))];
      if (!language) return;
      heading = language.name;
      amount = `${(language.share * 100).toFixed(1)}% of the displayed language mix`;
      explanation = "These colored paper panels represent repository language proportions, weighted by your authored commits. Private and public repositories authorized by your tokens contribute. This is not a count of lines personally written.";
    } else if (feature === "streak") {
      heading = "Gold & streaks";
      amount = `${stats.gold.count} gold seals · ${stats.current_weeks} current streak weeks · ${stats.record_weeks} record weeks`;
      explanation = `${stats.gold.remaining === null ? "Every gold seal is earned." : `${number(stats.gold.remaining)} more ${unit} unlock the next seal.`} The streak accent is ${Math.round(stats.accent * 100)}% full. Consecutive active UTC weeks build the accent; the record permanently enriches pigments.`;
    } else if (feature === "motion") {
      heading = {rest: "Quiet breathing", active: "Steady swimming", busy: "Busy current"}[stats.mood];
      amount = `${number(recent)} ${unit} in the last seven days`;
      explanation = `Zero ${unit} gives gentle breathing, 1–9 gives swimming, and 10 or more adds faster undulation and a gold wake. The window includes today. Reduced-motion preferences are respected.`;
    } else {
      feature = "growth";
      heading = `${stats.stage.name} form`;
      amount = stats.stage.next ? `${number(stats.stage.next.remaining)} more ${unit} to ${stats.stage.next.name}` : "Elder reached · every growth form is unlocked";
      explanation = `${number(total)} ${unit} counted. ${calendar ? "Growth follows your default GitHub contribution calendar for the past year." : "Each accessible authored commit counts once."} Earned forms carry over.`;
    }
    if (displayed === feature) return;
    displayed = feature;
    title.textContent = heading;
    value.textContent = amount;
    copy.textContent = explanation;
    buttons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.feature === feature)));
  }
  buttons.forEach(button => {
    button.addEventListener("pointerenter", () => inspect(button.dataset.feature));
    button.addEventListener("pointerleave", () => inspect(selected));
    button.addEventListener("focus", () => inspect(button.dataset.feature));
    button.addEventListener("click", () => { selected = button.dataset.feature; inspect(selected);
      if (matchMedia("(max-width:650px)").matches) showTooltip(); });
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") { selected = "growth"; inspect(selected); tooltip.hidden = true; }
  });
  const pause = document.getElementById("pause");
  pause.hidden = false;
  pause.addEventListener("click", () => {
    const paused = artwork.classList.toggle("paused");
    if (paused) svg.pauseAnimations(); else svg.unpauseAnimations();
    pause.setAttribute("aria-pressed", String(paused));
    pause.textContent = paused ? "Resume motion" : "Pause motion";
  });
  // Test the artwork's alpha and pigment, rather than making empty parchment
  // or rectangular image bounds act like language panels. No network requests.
  const sprite = new Image();
  sprite.onload = () => {
    try {
      const canvas = document.createElement("canvas");
      canvas.width = 800; canvas.height = 640;
      const context = canvas.getContext("2d", {willReadFrequently: true});
      const scale = Math.min(748 / sprite.naturalWidth, 600 / sprite.naturalHeight);
      const width = sprite.naturalWidth * scale, height = sprite.naturalHeight * scale;
      context.drawImage(sprite, 26 + (748 - width) / 2, 20 + (600 - height) / 2, width, height);
      const pixels = context.getImageData(0, 0, 800, 640).data;
      function hit(event) {
        // This transform follows the animated creature. The small displacement
        // filter can shift the outermost edge slightly; keyboard controls are exact.
        const rootMatrix = svg.getScreenCTM();
        if (rootMatrix) {
          const rootPoint = new DOMPoint(event.clientX, event.clientY).matrixTransform(rootMatrix.inverse());
          for (let i = 0; i < stats.gold.count; i++) {
            if (Math.hypot(rootPoint.x - (650 + i * 23), rootPoint.y - 609) < 12) return "streak";
          }
        }
        const matrix = svg.querySelector(".body").getScreenCTM();
        if (!matrix) return null;
        const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse());
        const x = Math.floor(point.x), y = Math.floor(point.y);
        if (x < 0 || x >= 800 || y < 0 || y >= 640) return null;
        const offset = (y * 800 + x) * 4;
        const [r, g, b, a] = pixels.subarray(offset, offset + 4);
        if (a < 40) return null;
        const redPaper = (4 * r - 8 * g + 4 * b) / 255 - .08 > .1;
        if (redPaper && stats.accent > .1 && (y >= 420 || y >= 300 && x < 380)) return "streak";
        if (redPaper) {
          let end = 0;
          for (let i = 0; i < stats.palette.length; i++) {
            end += stats.palette[i].share * 640;
            if (y < end) return `language-${i}`;
          }
        }
        return r > 160 && g > 80 && b < 150 ? "streak" : "growth";
      }
      artwork.classList.add("ready");
      artwork.addEventListener("pointermove", event => {
        if (event.pointerType !== "touch") {
          const feature = hit(event);
          inspect(feature || selected);
          if (feature) showTooltip(); else tooltip.hidden = true;
        }
      });
      artwork.addEventListener("pointerleave", () => { inspect(selected); tooltip.hidden = true; });
      artwork.addEventListener("click", event => {
        const feature = hit(event);
        if (feature) { selected = feature; inspect(feature); showTooltip(); }
        else tooltip.hidden = true;
      });
      document.getElementById("hint").textContent = "Hover or tap the colored paper. The controls below work with a keyboard, too.";
    } catch {
      document.getElementById("hint").textContent = "Choose a feature below to explore the dragon.";
    }
  };
  sprite.src = svg.querySelector("#dragon-art").getAttribute("href");
  inspect(selected);
})();
