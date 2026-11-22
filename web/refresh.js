"use strict";
(() => {
  const link = document.getElementById("refresh-dragon");
  const status = document.getElementById("refresh-status");
  const cancel = document.getElementById("cancel-refresh");
  const baseline = Date.parse(JSON.parse(document.getElementById("dragon-stats").textContent).updated_at);
  let timer, started, checking = false, controller;
  function stop(message) {
    clearInterval(timer);
    timer = undefined;
    controller?.abort();
    cancel.hidden = true;
    status.textContent = message;
  }
  async function check() {
    if (!timer || checking || document.hidden) return;
    if (Date.now() - started >= 20 * 60 * 1000) {
      stop("No new deployment detected yet. Check the workflow in GitHub, then try Refresh dragon again.");
      return;
    }
    checking = true;
    controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const url = new URL("stats.json", location.href);
      url.searchParams.set("refresh", Date.now());
      const response = await fetch(url, {cache: "no-store", credentials: "omit", signal: controller.signal});
      if (!response.ok) throw new Error("Stats unavailable");
      const latest = await response.json();
      const timestamp = Date.parse(latest.updated_at);
      if (latest.version !== 1 || !Number.isFinite(timestamp)) throw new Error("Invalid stats");
      if (!timer) return;
      if (timestamp > baseline) {
        const page = new URL(location.href);
        page.searchParams.set("refresh", timestamp);
        stop("New dragon published. Loading the updated artwork and stats…");
        location.replace(page.href);
      } else {
        status.textContent = "Waiting for a new deployment. In GitHub Actions, select Run workflow on main. This page updates automatically when it finishes.";
      }
    } catch {
      if (timer) status.textContent = "Could not check for updates. Your current dragon is unchanged; retrying automatically. You can check the run in GitHub.";
    } finally {
      clearTimeout(timeout);
      checking = false;
    }
  }
  // The native link opens GitHub's authenticated owner-only workflow controls.
  // Public visitors never receive a token or a privileged dispatch endpoint.
  link.addEventListener("click", () => {
    if (timer) return;
    started = Date.now();
    status.textContent = "GitHub Actions opened. Select Run workflow on main, then return here. Watching for the updated dragon…";
    cancel.hidden = false;
    timer = setInterval(check, 10000);
    void check();
  });
  cancel.addEventListener("click", () => stop("Stopped watching. A workflow already started in GitHub will continue."));
  document.addEventListener("visibilitychange", () => { if (!document.hidden) void check(); });
  window.addEventListener("pagehide", () => stop(""));
})();
