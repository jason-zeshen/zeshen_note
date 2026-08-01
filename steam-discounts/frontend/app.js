"use strict";

const els = {
  grid: document.getElementById("grid"),
  status: document.getElementById("status"),
  meta: document.getElementById("meta"),
  search: document.getElementById("search"),
  cc: document.getElementById("cc"),
  sort: document.getElementById("sort"),
  min: document.getElementById("min"),
  minLabel: document.getElementById("minLabel"),
  refresh: document.getElementById("refresh"),
};

let allItems = [];   // full dataset from the server
let updated = "";

function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function sortItems(items) {
  const mode = els.sort.value;
  const val = (g) => (g.final_price_value == null ? Infinity : g.final_price_value);
  const copy = items.slice();
  copy.sort((a, b) => {
    switch (mode) {
      case "discount_asc": return a.discount_percent - b.discount_percent;
      case "price_asc": return val(a) - val(b);
      case "price_desc": return val(b) - val(a);
      case "name": return a.name.localeCompare(b.name);
      case "discount_desc":
      default: return b.discount_percent - a.discount_percent;
    }
  });
  return copy;
}

function render() {
  const q = els.search.value.trim().toLowerCase();
  const minPct = Number(els.min.value);
  let items = allItems.filter(
    (g) => g.discount_percent >= minPct &&
           (!q || g.name.toLowerCase().includes(q))
  );
  items = sortItems(items);

  els.status.className = "status";
  els.status.textContent =
    `${items.length} game${items.length === 1 ? "" : "s"} shown` +
    (allItems.length ? ` · ${allItems.length} on sale total` : "") +
    (updated ? ` · updated ${updated}` : "");

  if (!items.length) {
    els.grid.innerHTML = "";
    // Distinguish "Steam returned nothing for this region" from "your filters
    // hid everything", so an empty region isn't mistaken for a broken app.
    if (allItems.length === 0) {
      els.status.className = "status";
      els.status.innerHTML =
        `Steam returned <b>0</b> discounts for <b>${escapeHtml(els.cc.value.toUpperCase())}</b>. ` +
        `If other regions do show games, this is almost always Steam <b>rate-limiting</b> a ` +
        `fresh region fetch — wait ~30s, then hit <b>↻ Refresh</b>. ` +
        `(A region genuinely may also have no active specials.)`;
    } else {
      els.status.className = "status";
      els.status.textContent =
        `0 of ${allItems.length} games match your filters (region ${els.cc.value.toUpperCase()}).`;
    }
    return;
  }

  els.grid.innerHTML = items.map((g) => {
    const img = g.image
      ? `<img class="thumb" loading="lazy" src="${escapeHtml(g.image)}" alt="">`
      : `<div class="thumb"></div>`;
    const orig = g.original_price
      ? `<span class="orig">${escapeHtml(g.original_price)}</span>` : "";
    const final = g.final_price
      ? `<span class="final">${escapeHtml(g.final_price)}</span>` : "";
    const href = g.url || (g.appid ? `https://store.steampowered.com/app/${g.appid}/` : "#");
    return `
      <a class="card" href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">
        ${img}
        <div class="body">
          <div class="name">${escapeHtml(g.name)}</div>
          <div class="prices">
            <span class="badge">-${g.discount_percent}%</span>
            ${orig}${final}
          </div>
        </div>
      </a>`;
  }).join("");
}

async function load(refresh = false) {
  const cc = els.cc.value;
  els.refresh.disabled = true;
  els.status.className = "status";
  els.status.textContent = refresh
    ? "Re-fetching from Steam… (this can take 10–30s)"
    : "Loading discounts…";
  els.grid.innerHTML = "";
  try {
    const params = new URLSearchParams({ cc });
    if (refresh) params.set("refresh", "1");
    const res = await fetch(`/api/discounts?${params}`);
    const data = await res.json();
    if (!res.ok || data.error) {
      throw new Error(data.message || `Request failed (${res.status})`);
    }
    allItems = data.items || [];
    updated = data.updated || "";
    const demoTag = data.demo ? " · ⚠ DEMO data (not live)" : "";
    els.meta.textContent = `${allItems.length} games on sale · ${cc.toUpperCase()}${demoTag}`;
    render();
  } catch (err) {
    els.status.className = "status error";
    els.status.innerHTML =
      `Couldn't load discounts: ${escapeHtml(err.message)}` +
      `<div class="hint" style="margin-top:8px">` +
      `If Steam is blocked on this network, run the server on an ` +
      `unrestricted connection, or set <code>HTTPS_PROXY</code>.</div>`;
    els.meta.textContent = "—";
  } finally {
    els.refresh.disabled = false;
  }
}

// --- events ---
els.search.addEventListener("input", render);
els.sort.addEventListener("change", render);
els.min.addEventListener("input", () => {
  els.minLabel.textContent = `${els.min.value}%`;
  render();
});
els.cc.addEventListener("change", () => load(false));
els.refresh.addEventListener("click", () => load(true));

load(false);
