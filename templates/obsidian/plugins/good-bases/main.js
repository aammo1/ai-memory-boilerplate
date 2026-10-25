var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// src/main.ts
var main_exports = {};
__export(main_exports, {
  default: () => NotionBasesPlugin
});
module.exports = __toCommonJS(main_exports);
var import_obsidian8 = require("obsidian");

// src/constants.ts
var NOTION_TABLE_VIEW = "notion-table";
var LOG_PREFIX = "[good-bases]";

// src/view-options.ts
function buildViewOptions(_config) {
  return [
    {
      type: "toggle",
      key: "wrapCells",
      displayName: "Wrap all content",
      default: true
    },
    {
      type: "toggle",
      key: "verticalLines",
      displayName: "Show vertical lines",
      default: true
    },
    {
      type: "dropdown",
      key: "openMode",
      displayName: "Open notes in",
      default: "tab",
      options: {
        tab: "New tab",
        panel: "Page panel"
      }
    },
    {
      type: "dropdown",
      key: "titleIcon",
      displayName: "Name column icon",
      default: "page",
      options: {
        page: "Page icon \u{1F4C4}",
        theme: "Obsidian's file icon",
        custom: "Custom (set below)",
        none: "Hidden"
      }
    },
    {
      type: "text",
      key: "titleIconCustom",
      displayName: "Custom Name column icon \u2014 an emoji, or a Lucide icon name like file-text"
    },
    {
      type: "multitext",
      key: "pillProperties",
      displayName: "Properties to show as colored pills"
    },
    {
      type: "multitext",
      key: "pinnedColors",
      displayName: "Pinned pill colors (value=color \u2014 a name: gray, brown, orange, yellow, green, blue, purple, pink, red \u2014 or a hex like #0088ff)"
    }
  ];
}

// src/view/notion-table-view.ts
var import_obsidian7 = require("obsidian");

// src/lib/calculations.ts
var import_obsidian = require("obsidian");
var LOCAL = {
  count: { label: "Count all" },
  percentEmpty: { label: "Percent empty", of: "Empty" },
  percentFilled: { label: "Percent not empty", of: "Filled" },
  percentChecked: { label: "Percent checked", of: "Checked" },
  percentUnchecked: { label: "Percent unchecked", of: "Unchecked" }
};
var CORE_LABELS = {
  Unique: "Count unique values",
  Empty: "Count empty",
  Filled: "Count not empty",
  Sum: "Sum",
  Average: "Average",
  Median: "Median",
  Min: "Min",
  Max: "Max",
  Range: "Range",
  Stddev: "Standard deviation",
  Earliest: "Earliest date",
  Latest: "Latest date",
  Checked: "Checked",
  Unchecked: "Unchecked"
};
var ORDER = {
  any: ["count", "Unique", "Empty", "Filled", "percentEmpty", "percentFilled"],
  number: ["Sum", "Average", "Median", "Min", "Max", "Range", "Stddev"],
  date: ["Earliest", "Latest", "Range"],
  boolean: ["Checked", "Unchecked", "percentChecked", "percentUnchecked"]
};
function isLocalCalc(key) {
  return Object.prototype.hasOwnProperty.call(LOCAL, key);
}
function localCalcBase(key) {
  return LOCAL[key]?.of ?? null;
}
function calcKind(sample) {
  if (sample instanceof import_obsidian.NumberValue) return "number";
  if (sample instanceof import_obsidian.DateValue) return "date";
  if (sample instanceof import_obsidian.BooleanValue) return "boolean";
  return "any";
}
function sampleValue(entries, prop) {
  for (const entry of entries) {
    const value = entry.getValue(prop);
    if (value !== null && !(value instanceof import_obsidian.NullValue)) return value;
  }
  return null;
}
function calcOptions(kind) {
  const keys = kind === "any" ? ORDER.any : [...ORDER.any, ...ORDER[kind]];
  return keys.map((key) => ({ key, label: calcLabel(key, kind), local: isLocalCalc(key) }));
}
function calcLabel(key, kind) {
  if (isLocalCalc(key)) return LOCAL[key].label;
  if (key === "Range" && kind === "date") return "Date range";
  return CORE_LABELS[key] ?? key;
}
function formatPercent(part, total) {
  if (total <= 0) return "0%";
  const pct = Math.round(part / total * 1e3) / 10;
  return `${pct}%`;
}
function parseCalculations(raw) {
  const calcs = /* @__PURE__ */ new Map();
  if (!Array.isArray(raw)) return calcs;
  for (const item of raw) {
    const match = String(item).match(/^(.+?)\s*=\s*(\w+)$/);
    if (!match) continue;
    const prop = match[1].trim();
    const key = match[2];
    if (prop && isLocalCalc(key)) calcs.set(prop, key);
  }
  return calcs;
}
function serializeCalculations(calcs) {
  return Array.from(calcs, ([prop, key]) => `${prop}=${key}`);
}

// src/lib/column-widths.ts
var TITLE_COLUMN_KEY = "__title";
var MIN_COLUMN_WIDTH = 60;
function parseColumnWidths(raw) {
  const widths = /* @__PURE__ */ new Map();
  if (!Array.isArray(raw)) return widths;
  for (const item of raw) {
    const match = String(item).match(/^(.+?)\s*[=:]\s*(\d+(?:\.\d+)?)(?:px)?$/);
    if (!match) continue;
    const key = match[1].trim();
    const px = Number(match[2]);
    if (!key || !Number.isFinite(px)) continue;
    widths.set(key, Math.max(MIN_COLUMN_WIDTH, Math.round(px)));
  }
  return widths;
}
function serializeColumnWidths(widths) {
  return Array.from(widths, ([key, px]) => `${key}=${Math.round(px)}`);
}

// src/lib/colors.ts
var NOTION_COLORS = [
  { name: "gray", lightBg: "#EBECED", lightFg: "#9B9A97", darkBg: "#454B4E", darkFg: "rgba(151,154,155,0.95)" },
  { name: "brown", lightBg: "#E9E5E3", lightFg: "#64473A", darkBg: "#434040", darkFg: "#937264" },
  { name: "orange", lightBg: "#FAEBDD", lightFg: "#D9730D", darkBg: "#594A3A", darkFg: "#FFA344" },
  { name: "yellow", lightBg: "#FBF3DB", lightFg: "#DFAB01", darkBg: "#59563B", darkFg: "#FFDC49" },
  { name: "green", lightBg: "#DDEDEA", lightFg: "#0F7B6C", darkBg: "#354C4B", darkFg: "#4DAB9A" },
  { name: "blue", lightBg: "#DDEBF1", lightFg: "#0B6E99", darkBg: "#364954", darkFg: "#529CCA" },
  { name: "purple", lightBg: "#EAE4F2", lightFg: "#6940A5", darkBg: "#443F57", darkFg: "#9A6DD7" },
  { name: "pink", lightBg: "#F4DFEB", lightFg: "#AD1A72", darkBg: "#533B4C", darkFg: "#E255A1" },
  { name: "red", lightBg: "#FBE4E4", lightFg: "#E03E3E", darkBg: "#594141", darkFg: "#FF7369" }
];
function colorFor(text) {
  let h = 0;
  for (let i = 0; i < text.length; i++) {
    h = h * 31 + text.charCodeAt(i) >>> 0;
  }
  return NOTION_COLORS[h % NOTION_COLORS.length];
}
function colorByName(name) {
  return NOTION_COLORS.find((c) => c.name === name);
}
function parseHex(spec) {
  const m = spec.trim().replace(/^#/, "");
  if (!/^([0-9a-f]{3}|[0-9a-f]{6})$/i.test(m)) return void 0;
  const full = m.length === 3 ? m.split("").map((c) => c + c).join("") : m;
  return {
    r: parseInt(full.slice(0, 2), 16),
    g: parseInt(full.slice(2, 4), 16),
    b: parseInt(full.slice(4, 6), 16)
  };
}
function rgbToHex({ r, g, b }) {
  const hex = (n) => Math.round(n).toString(16).padStart(2, "0");
  return `#${hex(r)}${hex(g)}${hex(b)}`;
}
function rgbToHsl({ r, g, b }) {
  const rn = r / 255, gn = g / 255, bn = b / 255;
  const max = Math.max(rn, gn, bn), min = Math.min(rn, gn, bn);
  const l = (max + min) / 2;
  const d = max - min;
  if (!d) return { h: 0, s: 0, l };
  const s = d / (1 - Math.abs(2 * l - 1));
  let h;
  if (max === rn) h = (gn - bn) / d % 6;
  else if (max === gn) h = (bn - rn) / d + 2;
  else h = (rn - gn) / d + 4;
  return { h: (h * 60 + 360) % 360, s, l };
}
function hslToRgb(h, s, l) {
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(h / 60 % 2 - 1));
  const m = l - c / 2;
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x] : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x];
  return { r: (r + m) * 255, g: (g + m) * 255, b: (b + m) * 255 };
}
function luminance({ r, g, b }) {
  const lin = (v) => {
    const s = v / 255;
    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}
function contrast(a, b) {
  const la = luminance(a), lb = luminance(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}
function readableOn(bg) {
  const goDark = contrast(bg, { r: 0, g: 0, b: 0 }) >= contrast(bg, { r: 255, g: 255, b: 255 });
  const { h, s } = rgbToHsl(bg);
  const tinted = hslToRgb(h, Math.min(s, 0.85), goDark ? 0.2 : 0.94);
  if (contrast(bg, tinted) >= 4.5) return rgbToHex(tinted);
  return goDark ? "#1A1A1A" : "#FFFFFF";
}
function customColor(spec) {
  const rgb = parseHex(spec);
  if (!rgb) return void 0;
  const bg = rgbToHex(rgb);
  const fg = readableOn(rgb);
  return { name: bg, lightBg: bg, lightFg: fg, darkBg: bg, darkFg: fg };
}
function parseColorSpec(spec) {
  const s = spec.trim();
  return colorByName(s.toLowerCase()) ?? customColor(s);
}
function colorKey(text) {
  return text.replace(/^#/, "").toLowerCase();
}
function resolvePillColor(text, pinned) {
  const key = colorKey(text);
  return pinned.get(key) ?? colorFor(key);
}
function applyColorVars(el, c) {
  el.setCssProps({
    "--ntn-pill-bg-light": c.lightBg,
    "--ntn-pill-fg-light": c.lightFg,
    "--ntn-pill-bg-dark": c.darkBg,
    "--ntn-pill-fg-dark": c.darkFg
  });
}
function applyPillColor(pill, text, pinned) {
  applyColorVars(pill, resolvePillColor(text, pinned));
}

// src/lib/dates.ts
function splitDateTime(value) {
  const m = /^(\d{4}-\d{2}-\d{2})(?:[T ](\d{2}:\d{2}(?::\d{2})?))?/.exec(value.trim());
  return { date: m?.[1] ?? "", time: m?.[2] ?? "" };
}

// src/lib/pills.ts
var import_obsidian2 = require("obsidian");

// src/lib/property-types.ts
function propertyWidget(app, name) {
  const mtm = app.metadataTypeManager;
  const info = mtm?.getPropertyInfo?.(name);
  return typeof info === "string" ? info : info?.widget ?? info?.type;
}
function isDateWidget(widget) {
  return widget === "date" || widget === "datetime";
}

// src/lib/pills.ts
function bareName(prop) {
  return prop.split(".").slice(1).join(".");
}
function computePillProps(props, entries, config, app) {
  const pillProps = /* @__PURE__ */ new Set();
  const listProps = /* @__PURE__ */ new Set();
  const userListed = config.get("pillProperties");
  const userSet = new Set(
    Array.isArray(userListed) ? userListed.map((s) => String(s).toLowerCase().trim()) : []
  );
  for (const prop of props) {
    const bare = bareName(prop).toLowerCase();
    const display = config.getDisplayName(prop).toLowerCase();
    const metaType = propertyWidget(app, bare);
    let isList = metaType === "multitext" || metaType === "tags" || metaType === "aliases" || bare === "tags";
    if (!isList) {
      for (const entry of entries) {
        if (entry.getValue(prop) instanceof import_obsidian2.ListValue) {
          isList = true;
          break;
        }
      }
    }
    if (isList) listProps.add(prop);
    if (isList || bare === "tags" || userSet.has(bare) || userSet.has(display)) {
      pillProps.add(prop);
    }
  }
  return { pillProps, listProps };
}
function parsePinnedColors(raw) {
  const pinned = /* @__PURE__ */ new Map();
  if (!Array.isArray(raw)) return pinned;
  for (const item of raw) {
    const m = String(item).match(/^(.+?)\s*[=:]\s*(.+)$/);
    if (!m) continue;
    const value = m[1].trim().replace(/^#/, "").toLowerCase();
    const color = parseColorSpec(m[2]);
    if (value && color) pinned.set(value, color);
  }
  return pinned;
}

// src/lib/tag-search.ts
function normalizeTag(tag) {
  const bare = tag.trim().replace(/^#+/, "");
  return bare ? `#${bare}` : "";
}
function openTagSearch(app, tag) {
  const bare = normalizeTag(tag).slice(1);
  if (!bare) return false;
  const plugin = app.internalPlugins?.getEnabledPluginById?.("global-search");
  if (typeof plugin?.openGlobalSearch !== "function") return false;
  plugin.openGlobalSearch(`tag:${bare}`);
  return true;
}

// src/lib/values.ts
var import_obsidian3 = require("obsidian");
function valueToItems(value) {
  if (value === null) return [];
  if (value instanceof import_obsidian3.ListValue) {
    const out = [];
    for (let i = 0; i < value.length(); i++) {
      const item = value.get(i);
      const s2 = item.toString();
      if (s2) out.push({ text: s2, isTag: item instanceof import_obsidian3.TagValue });
    }
    return out;
  }
  const s = value.toString();
  return s ? [{ text: s, isTag: value instanceof import_obsidian3.TagValue }] : [];
}
function valueToStrings(value) {
  return valueToItems(value).map((item) => item.text);
}

// src/view/date-editor.ts
var import_obsidian4 = require("obsidian");

// src/view/floating-editor.ts
var FloatingEditor = class {
  constructor(deps) {
    this.deps = deps;
    this.closed = false;
  }
  /** The element this editor is anchored to (drives click-to-toggle). */
  get anchorEl() {
    return this.deps.anchor;
  }
  /** Whether the given node lives inside the popover. */
  contains(node) {
    return !!node && this.menu.contains(node);
  }
  /**
   * Re-point the editor at a freshly rendered cell for the same file +
   * property. `onDataUpdated` replaces every `td`, so without this the
   * anchor would dangle on a detached node and click-to-toggle (which
   * compares against the live cell) would miss. Returns whether it matched.
   */
  reanchorIfMatches(el, filePath, prop) {
    if (this.closed) return false;
    if (this.deps.prop !== prop || this.deps.file.path !== filePath) return false;
    if (!this.deps.container.contains(el)) return false;
    this.deps.anchor = el;
    return true;
  }
  /** Tear the popover down. Idempotent; notifies the owner via `onClose`. */
  close() {
    if (this.closed) return;
    this.closed = true;
    this.onClosing();
    this.menu.remove();
    this.deps.onClose();
  }
  /** Hook for subclasses to tear down side popovers before the menu goes. */
  onClosing() {
  }
  /** Place a popover just below `anchorRect`, nudged to stay on screen. */
  clampToWindow(el, anchorRect) {
    const { win } = this.deps;
    el.setCssStyles({
      left: `${anchorRect.left}px`,
      top: `${anchorRect.bottom + 4}px`
    });
    const rect = el.getBoundingClientRect();
    if (rect.bottom > win.innerHeight - 8) {
      el.setCssStyles({ top: `${Math.max(8, anchorRect.top - rect.height - 4)}px` });
    }
    if (rect.right > win.innerWidth - 8) {
      el.setCssStyles({ left: `${Math.max(8, win.innerWidth - rect.width - 8)}px` });
    }
  }
};

// src/view/date-editor.ts
function ymd(d) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${String(d.getFullYear()).padStart(4, "0")}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
var DateEditor = class extends FloatingEditor {
  constructor(deps) {
    super(deps);
    this.timeInput = null;
    this.written = deps.current.trim();
    ({ date: this.date, time: this.time } = splitDateTime(this.written));
    this.time = this.time.replace(/^(\d{2}:\d{2}):00$/, "$1");
    const today = /* @__PURE__ */ new Date();
    this.viewMonth = this.date ? new Date(Number(this.date.slice(0, 4)), Number(this.date.slice(5, 7)) - 1, 1) : new Date(today.getFullYear(), today.getMonth(), 1);
    this.menu = this.build();
    this.clampToWindow(this.menu, deps.anchor.getBoundingClientRect());
  }
  build() {
    const menu = this.deps.container.createDiv({ cls: "ntn-root ntn-date-menu" });
    const fields = menu.createDiv({ cls: "ntn-date-fields" });
    this.dateInput = fields.createEl("input", {
      type: "text",
      cls: "ntn-date-field",
      attr: { placeholder: "YYYY-MM-DD", spellcheck: "false" }
    });
    this.dateInput.value = this.deps.withTime ? this.date : this.written;
    this.dateInput.addEventListener("input", () => this.dateInput.removeClass("ntn-date-field-invalid"));
    this.dateInput.addEventListener("keydown", (evt) => this.onKeydown(evt, () => this.commitTyped()));
    if (this.deps.withTime) {
      this.timeInput = fields.createEl("input", {
        type: "time",
        cls: "ntn-date-time",
        attr: { step: "60", "aria-label": "Time" }
      });
      this.timeInput.value = this.time;
      this.timeInput.addEventListener("change", () => {
        this.time = this.timeInput?.value ?? "";
        if (this.date) this.save();
      });
      this.timeInput.addEventListener("keydown", (evt) => this.onKeydown(evt, () => {
        this.time = this.timeInput?.value ?? "";
        this.commitTyped();
      }));
    }
    const head = menu.createDiv({ cls: "ntn-date-head" });
    const prev = head.createDiv({ cls: "ntn-date-nav", attr: { "aria-label": "Previous month" } });
    (0, import_obsidian4.setIcon)(prev, "chevron-left");
    this.titleEl = head.createDiv({ cls: "ntn-date-title" });
    const next = head.createDiv({ cls: "ntn-date-nav", attr: { "aria-label": "Next month" } });
    (0, import_obsidian4.setIcon)(next, "chevron-right");
    prev.addEventListener("click", () => this.shiftMonth(-1));
    next.addEventListener("click", () => this.shiftMonth(1));
    this.gridEl = menu.createDiv({ cls: "ntn-date-grid" });
    this.renderGrid();
    const actions = menu.createDiv({ cls: "ntn-date-actions" });
    const today = actions.createDiv({ cls: "ntn-date-action", text: "Today" });
    today.addEventListener("click", () => this.pick(ymd(/* @__PURE__ */ new Date())));
    const clear = actions.createDiv({ cls: "ntn-date-action", text: "Clear" });
    clear.addEventListener("click", () => {
      this.save(null);
      this.close();
    });
    this.dateInput.focus();
    this.dateInput.select();
    return menu;
  }
  shiftMonth(delta) {
    this.viewMonth = new Date(this.viewMonth.getFullYear(), this.viewMonth.getMonth() + delta, 1);
    this.renderGrid();
  }
  /** Six weeks of days for the month on display, padded with its neighbours. */
  renderGrid() {
    const locale = import_obsidian4.moment.localeData();
    const year = this.viewMonth.getFullYear();
    const month = this.viewMonth.getMonth();
    this.titleEl.setText(`${import_obsidian4.moment.months()[month]} ${year}`);
    this.gridEl.empty();
    for (const name of import_obsidian4.moment.weekdaysMin(true)) {
      this.gridEl.createDiv({ cls: "ntn-date-weekday", text: name });
    }
    const lead = (this.viewMonth.getDay() - locale.firstDayOfWeek() + 7) % 7;
    const todayKey = ymd(/* @__PURE__ */ new Date());
    for (let i = 0; i < 42; i++) {
      const day = new Date(year, month, 1 - lead + i);
      const key = ymd(day);
      const cell = this.gridEl.createDiv({ cls: "ntn-date-day", text: String(day.getDate()) });
      if (day.getMonth() !== month) cell.addClass("ntn-date-outside");
      if (key === todayKey) cell.addClass("ntn-date-today");
      if (key === this.date) cell.addClass("ntn-date-selected");
      cell.addEventListener("click", () => this.pick(key));
    }
  }
  /**
   * A day was chosen. Date-only editors write and close; with a time
   * selector the write lands now and the editor stays open for the clock.
   */
  pick(date) {
    this.date = date;
    this.save();
    if (!this.deps.withTime) {
      this.close();
      return;
    }
    this.dateInput.value = date;
    this.viewMonth = new Date(Number(date.slice(0, 4)), Number(date.slice(5, 7)) - 1, 1);
    this.renderGrid();
    this.timeInput?.focus();
  }
  /** The typed field(s) were confirmed with Enter: validate, write, close. */
  commitTyped() {
    const raw = this.dateInput.value.trim();
    if (!raw) {
      this.save(null);
      this.close();
      return;
    }
    if (!import_obsidian4.DateValue.parseFromString(raw)) {
      this.dateInput.addClass("ntn-date-field-invalid");
      return;
    }
    const typed = splitDateTime(raw);
    this.date = typed.date;
    if (typed.time || !this.deps.withTime) this.time = typed.time;
    this.save();
    this.close();
  }
  /** The value as it should be written: date, plus `T` + time when set. */
  compose() {
    return this.date + (this.time ? `T${this.time}` : "");
  }
  /** Write the composed (or given) value unless the note already holds it. */
  save(value = this.compose()) {
    const next = value ?? "";
    if (next === this.written) return;
    this.written = next;
    this.deps.write(value);
  }
  onKeydown(evt, onEnter) {
    if (evt.key === "Escape") {
      evt.preventDefault();
      evt.stopPropagation();
      this.close();
    } else if (evt.key === "Enter") {
      evt.preventDefault();
      onEnter();
    }
  }
};

// src/view/note-modal.ts
var import_obsidian6 = require("obsidian");

// src/lib/frontmatter.ts
function splitFrontmatter(raw) {
  const match = raw.match(/^---\r?\n(?:[\s\S]*?\r?\n)?---(?:\r?\n|$)/);
  if (!match) return { frontmatter: "", body: raw };
  return { frontmatter: match[0], body: raw.slice(match[0].length) };
}

// src/view/live-editor.ts
var import_obsidian5 = require("obsidian");
var cachedCtor;
function editorClass(app) {
  if (cachedCtor !== void 0) return cachedCtor;
  cachedCtor = null;
  try {
    const registry = app.embedRegistry;
    const createMd = registry?.embedByExtension?.md;
    if (typeof createMd !== "function") return null;
    const embed = createMd({ app, containerEl: createDiv(), state: {} }, null, "");
    embed.load();
    embed.editable = true;
    embed.showEditor();
    const editMode = embed.editMode;
    const ctor = editMode ? Object.getPrototypeOf(Object.getPrototypeOf(editMode)).constructor : void 0;
    editMode?.destroy?.();
    embed.unload();
    if (typeof ctor === "function") cachedCtor = ctor;
  } catch (e) {
    console.warn(`${LOG_PREFIX} live preview editor unavailable, using plain textarea`, e);
  }
  return cachedCtor;
}
function createLiveEditor(app, container, file, text, onChange) {
  const resolved = editorClass(app);
  if (!resolved) return null;
  const Base = resolved;
  const owner = {
    app,
    get file() {
      return file;
    },
    get path() {
      return file.path;
    },
    getFile: () => file,
    getMode: () => "source",
    editMode: null,
    get editor() {
      return owner.editMode?.editor;
    },
    hoverPopover: null,
    showSearch: () => {
    },
    toggleMode: () => {
    },
    syncScroll: () => {
    },
    onMarkdownScroll: () => {
    },
    onMarkdownFold: () => {
    },
    onFoldChange: () => {
    },
    getFoldInfo: () => null
  };
  class PanelEditor extends Base {
    /** The base pads the bottom by half the viewport (scroll-past-end); not in a panel. */
    updateBottomPadding() {
    }
    onUpdate(update, changed) {
      Base.prototype.onUpdate.call(this, update, changed);
      if (update.docChanged) onChange();
    }
  }
  const comp = new import_obsidian5.Component();
  let instance;
  try {
    instance = new PanelEditor(app, container, owner);
    owner.editMode = instance;
    comp.load();
    comp.addChild(instance);
    instance.sourceMode = false;
    instance.set(text, true);
  } catch (e) {
    console.warn(`${LOG_PREFIX} live preview editor failed to mount, using plain textarea`, e);
    comp.unload();
    container.empty();
    return null;
  }
  let prevActive = null;
  instance.editorEl.addEventListener("focusin", () => {
    if (app.workspace.activeEditor === owner) return;
    prevActive = app.workspace.activeEditor;
    app.workspace.activeEditor = owner;
  });
  return {
    el: instance.editorEl,
    getValue: () => instance.editor.getValue(),
    focus: () => instance.editor.focus(),
    destroy: () => {
      if (app.workspace.activeEditor === owner) app.workspace.activeEditor = prevActive;
      try {
        instance.destroy();
      } catch (e) {
        console.warn(`${LOG_PREFIX} failed to tear down live preview editor`, e);
      }
      comp.unload();
    }
  };
}

// src/view/note-modal.ts
var NotePageModal = class extends import_obsidian6.Modal {
  constructor(app, file, deps) {
    super(app);
    /** Lifetime owner for MarkdownRenderer children; replaced per render. */
    this.renderComp = null;
    /** The Live Preview body editor; null when using the textarea fallback. */
    this.liveEditor = null;
    this.fileOpenRef = null;
    this.closed = false;
    this.saveTimer = null;
    /** True while the body holds keystrokes not yet written to disk. */
    this.dirty = false;
    this.file = file;
    this.deps = deps;
  }
  onOpen() {
    void this.buildPanel();
  }
  async buildPanel() {
    const { contentEl, modalEl } = this;
    modalEl.addClass("ntn-page-modal");
    contentEl.addClass("ntn-page-content");
    const openTabBtn = modalEl.createDiv({
      cls: "ntn-page-open-tab",
      attr: { "aria-label": "Open in new tab", tabindex: "0" }
    });
    (0, import_obsidian6.setIcon)(openTabBtn, "maximize-2");
    const openInTab = () => {
      this.close();
      void this.app.workspace.getLeaf(true).openFile(this.file);
    };
    openTabBtn.addEventListener("click", openInTab);
    openTabBtn.addEventListener("keydown", (evt) => {
      if (evt.key === "Enter" || evt.key === " ") {
        evt.preventDefault();
        openInTab();
      }
    });
    this.pageTitleEl = contentEl.createEl("h1", {
      cls: "ntn-page-title",
      // plaintext-only keeps pasted rich text from injecting HTML
      // (supported in Electron/Chromium, which is all Obsidian runs on).
      attr: { contenteditable: "plaintext-only", "data-placeholder": "Untitled" }
    });
    this.pageTitleEl.setText(this.file.basename);
    this.pageTitleEl.addEventListener("keydown", (evt) => {
      if (evt.key === "Enter") {
        evt.preventDefault();
        this.editBody();
      }
    });
    this.pageTitleEl.addEventListener("blur", () => void this.commitTitle());
    const { frontmatter, body } = splitFrontmatter(await this.app.vault.read(this.file));
    if (this.closed) return;
    this.propsEl = contentEl.createDiv({ cls: "ntn-page-props" });
    this.renderPropertyRows(this.parseProperties(frontmatter));
    const editorHost = contentEl.createDiv({ cls: "ntn-page-editor" });
    this.liveEditor = createLiveEditor(this.app, editorHost, this.file, body, () => {
      this.updateEditorEmpty(editorHost);
      this.scheduleSave();
    });
    if (this.liveEditor) {
      this.updateEditorEmpty(editorHost);
      editorHost.addEventListener("click", (evt) => {
        if (evt.target === editorHost) this.liveEditor?.focus();
      });
      this.fileOpenRef = this.app.workspace.on("file-open", (opened) => {
        if (opened && opened !== this.file) this.close();
      });
    } else {
      editorHost.remove();
      this.buildFallbackBody(body);
      await this.renderPreview();
    }
    this.pageTitleEl.focus();
    contentEl.win.getSelection()?.selectAllChildren(this.pageTitleEl);
  }
  /** The live editor's "Write something…" placeholder, shown while empty. */
  updateEditorEmpty(host) {
    host.toggleClass("ntn-page-editor-empty", !this.getBody().trim());
  }
  /**
   * Fallback body when the internal editor can't be built (see
   * live-editor.ts): rendered markdown, click to edit in a textarea.
   */
  buildFallbackBody(body) {
    const { contentEl } = this;
    this.previewEl = contentEl.createDiv({
      cls: "ntn-page-preview markdown-rendered"
    });
    this.previewEl.addEventListener("click", (evt) => {
      const link = evt.target.closest("a");
      if (link?.hasClass("internal-link")) {
        evt.preventDefault();
        const target = link.getAttribute("data-href") ?? link.getAttribute("href") ?? "";
        this.close();
        void this.app.workspace.openLinkText(target, this.file.path, import_obsidian6.Keymap.isModEvent(evt));
        return;
      }
      if (link?.hasClass("tag")) {
        evt.preventDefault();
        const tag = link.getAttribute("href") ?? link.getText();
        if (openTagSearch(this.app, tag)) this.close();
        return;
      }
      if (link) return;
      this.editBody();
    });
    this.bodyArea = contentEl.createEl("textarea", {
      cls: "ntn-page-body ntn-hidden",
      attr: { placeholder: "Write something\u2026" }
    });
    this.bodyArea.value = body;
    this.bodyArea.addEventListener("input", () => {
      this.autoSizeBody();
      this.scheduleSave();
    });
    this.bodyArea.addEventListener("blur", () => {
      if (this.dirty) void this.saveBody();
      void this.showPreview();
    });
  }
  // ---------------- Body: editor / preview <-> textarea ----------------
  /** The body text as currently edited. */
  getBody() {
    return this.liveEditor ? this.liveEditor.getValue() : this.bodyArea.value;
  }
  /** Move the caret into the body (Enter on the title). */
  editBody() {
    if (this.liveEditor) {
      this.liveEditor.focus();
      return;
    }
    this.previewEl.addClass("ntn-hidden");
    this.bodyArea.removeClass("ntn-hidden");
    this.autoSizeBody();
    this.bodyArea.focus();
  }
  /**
   * Grow the textarea to fit its content so the whole body stays readable
   * while editing — the panel scrolls, the textarea never does. Without
   * this, a long properties list plus the title can crush a flex-sized
   * textarea to nothing (many-properties bug, July 2026).
   */
  autoSizeBody() {
    this.bodyArea.setCssStyles({ height: "auto" });
    this.bodyArea.setCssStyles({ height: `${this.bodyArea.scrollHeight + 2}px` });
  }
  /** Swap the textarea back for the freshly rendered markdown. */
  async showPreview() {
    this.bodyArea.addClass("ntn-hidden");
    this.previewEl.removeClass("ntn-hidden");
    await this.renderPreview();
  }
  async renderPreview() {
    this.renderComp?.unload();
    this.renderComp = new import_obsidian6.Component();
    this.renderComp.load();
    this.previewEl.empty();
    const markdown = this.bodyArea.value;
    if (!markdown.trim()) {
      this.previewEl.createDiv({
        cls: "ntn-page-preview-empty",
        text: "Write something\u2026"
      });
      return;
    }
    await import_obsidian6.MarkdownRenderer.render(
      this.app,
      markdown,
      this.previewEl,
      this.file.path,
      this.renderComp
    );
  }
  // ---------------- Properties ----------------
  /** Re-read the file and rebuild the property rows from what's on disk. */
  async refreshProperties() {
    const { frontmatter } = splitFrontmatter(await this.app.vault.read(this.file));
    this.renderPropertyRows(this.parseProperties(frontmatter));
  }
  renderPropertyRows(props) {
    this.propsEl.empty();
    for (const [key, value] of Object.entries(props)) {
      this.renderPropertyRow(key, value);
    }
  }
  renderPropertyRow(key, value) {
    const row = this.propsEl.createDiv({ cls: "ntn-page-prop" });
    row.createDiv({ cls: "ntn-page-prop-name", text: key });
    const valueEl = row.createDiv({ cls: "ntn-page-prop-value" });
    const isTags = key.toLowerCase() === "tags";
    const isPill = isTags || this.deps.isPillProp(key) || Array.isArray(value);
    if (isPill) {
      const items = Array.isArray(value) ? value.map((v) => this.formatScalar(v)) : this.isEmpty(value) ? [] : [this.formatScalar(value)];
      for (const item of items) {
        const pill = valueEl.createSpan({ cls: "ntn-pill" });
        this.deps.applyColor(pill, item);
        pill.setText(item.replace(/^#/, ""));
        if (isTags) this.makeTagPill(pill, item);
      }
      if (!items.length) this.renderEmpty(valueEl);
      valueEl.addClass("ntn-page-prop-editable");
      valueEl.addEventListener("click", () => {
        this.deps.openSelect({
          anchor: valueEl,
          container: this.containerEl,
          file: this.file,
          propName: key,
          current: items,
          isList: isTags || this.deps.isListProp(key) || Array.isArray(value),
          onWrite: () => void this.refreshProperties()
        });
      });
      this.deps.reanchorEditor(valueEl, this.file.path, key);
      return;
    }
    if (typeof value === "boolean") {
      const cb = valueEl.createEl("input", { type: "checkbox", cls: "ntn-checkbox" });
      cb.checked = value;
      cb.addEventListener("change", () => void this.writeAndRefresh(key, cb.checked));
      return;
    }
    const text = this.isEmpty(value) ? "" : this.formatScalar(value);
    if (text) valueEl.createSpan({ text });
    else this.renderEmpty(valueEl);
    valueEl.addClass("ntn-page-prop-editable");
    if (this.deps.isDateProp(key) || text && import_obsidian6.DateValue.parseFromString(text)) {
      valueEl.addEventListener("click", () => {
        this.deps.openDate({
          anchor: valueEl,
          container: this.containerEl,
          file: this.file,
          propName: key,
          current: text,
          onWrite: () => void this.refreshProperties()
        });
      });
      this.deps.reanchorEditor(valueEl, this.file.path, key);
      return;
    }
    valueEl.addEventListener("click", () => this.editScalar(valueEl, key, value));
  }
  /**
   * Make a pill search the vault for its tag, like the table's tag pills.
   * The panel covers the whole workspace, so it steps aside for the search
   * pane — closing also flushes any pending title/body edit (onClose).
   */
  makeTagPill(pill, tag) {
    pill.addClass("ntn-pill-tag");
    pill.addEventListener("click", (evt) => {
      evt.stopPropagation();
      if (openTagSearch(this.app, tag)) this.close();
    });
  }
  /** Swap a property row's value for an input; Enter/blur commits, Esc cancels. */
  editScalar(valueEl, key, value) {
    if (valueEl.querySelector(".ntn-input")) return;
    const kind = typeof value === "number" ? "number" : "text";
    const current = this.isEmpty(value) ? "" : this.formatScalar(value);
    valueEl.empty();
    const input = valueEl.createEl("input", {
      type: "text",
      cls: "ntn-input ntn-page-prop-input"
    });
    input.value = current;
    input.focus();
    input.select();
    let committed = false;
    const commit = () => {
      if (committed) return;
      committed = true;
      const raw = input.value.trim();
      if (raw === current) {
        void this.refreshProperties();
        return;
      }
      let out = raw;
      if (kind === "number") {
        const n = Number(raw);
        out = raw === "" ? null : Number.isNaN(n) ? raw : n;
      } else if (raw === "") {
        out = null;
      }
      void this.writeAndRefresh(key, out);
    };
    input.addEventListener("keydown", (evt) => {
      if (evt.key === "Enter") {
        evt.preventDefault();
        commit();
      } else if (evt.key === "Escape") {
        committed = true;
        evt.preventDefault();
        evt.stopPropagation();
        void this.refreshProperties();
      }
    });
    input.addEventListener("blur", commit);
  }
  async writeAndRefresh(propName, value) {
    await this.deps.write(this.file, propName, value);
    await this.refreshProperties();
  }
  parseProperties(frontmatter) {
    if (!frontmatter) return {};
    const yaml = frontmatter.replace(/^---\r?\n/, "").replace(/---\r?\n?$/, "");
    try {
      const parsed = (0, import_obsidian6.parseYaml)(yaml);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        return parsed;
      }
    } catch (e) {
      console.error(`${LOG_PREFIX} failed to parse note frontmatter`, e);
    }
    return {};
  }
  isEmpty(value) {
    return value === null || value === void 0 || value === "";
  }
  renderEmpty(valueEl) {
    valueEl.createSpan({ cls: "ntn-page-prop-empty", text: "Empty" });
  }
  /** YAML scalars as Notion would show them (dates as yyyy-mm-dd). */
  formatScalar(value) {
    if (value instanceof Date) return value.toISOString().slice(0, 10);
    return String(value);
  }
  // ---------------- Body ----------------
  /** Debounced autosave: write 400ms after the last keystroke. */
  scheduleSave() {
    this.dirty = true;
    const win = this.contentEl.win;
    if (this.saveTimer !== null) win.clearTimeout(this.saveTimer);
    this.saveTimer = win.setTimeout(() => void this.saveBody(), 400);
  }
  async saveBody() {
    this.dirty = false;
    const body = this.getBody();
    try {
      await this.app.vault.process(
        this.file,
        (data) => splitFrontmatter(data).frontmatter + body
      );
    } catch (e) {
      console.error(`${LOG_PREFIX} failed to save note body`, e);
      new import_obsidian6.Notice("Couldn't save the note.");
    }
  }
  // ---------------- Title ----------------
  /** Rename the file to match the title; revert the h1 if that fails. */
  async commitTitle() {
    const title = (this.pageTitleEl.textContent ?? "").replace(/\s+/g, " ").trim();
    if (!title || title === this.file.basename) return;
    const folder = this.file.parent?.path ?? "";
    const newPath = folder && folder !== "/" ? `${folder}/${title}.md` : `${title}.md`;
    try {
      await this.app.fileManager.renameFile(this.file, newPath);
    } catch (e) {
      console.error(`${LOG_PREFIX} failed to rename note`, e);
      new import_obsidian6.Notice(`Couldn't rename the note to "${title}".`);
      this.pageTitleEl.setText(this.file.basename);
    }
  }
  onClose() {
    this.deps.closeEditor();
    this.renderComp?.unload();
    this.renderComp = null;
    if (this.saveTimer !== null) this.contentEl.win.clearTimeout(this.saveTimer);
    void this.flushPendingEdits();
    this.closed = true;
    this.liveEditor?.destroy();
    this.liveEditor = null;
    if (this.fileOpenRef) this.app.workspace.offref(this.fileOpenRef);
    this.fileOpenRef = null;
    this.contentEl.empty();
  }
  async flushPendingEdits() {
    if (this.dirty) await this.saveBody();
    await this.commitTitle();
  }
};

// src/view/select-editor.ts
var SelectEditor = class extends FloatingEditor {
  constructor(deps) {
    super(deps);
    /** Open color-picker flyout, if any (a sibling popover in the container). */
    this.colorMenu = null;
    /** Distinct known values for this property: lowercase key → display text. */
    this.known = /* @__PURE__ */ new Map();
    const { entries, current, prop } = deps;
    for (const e of entries) {
      for (const s of valueToStrings(e.getValue(prop))) {
        const display = s.replace(/^#/, "");
        if (display && !this.known.has(display.toLowerCase())) {
          this.known.set(display.toLowerCase(), display);
        }
      }
    }
    this.selected = current.map((s) => s.replace(/^#/, ""));
    this.menu = this.build();
    this.position();
  }
  /** Whether the given node lives inside the menu or its color flyout. */
  contains(node) {
    return super.contains(node) || (this.colorMenu?.contains(node) ?? false);
  }
  onClosing() {
    this.closeColorMenu();
  }
  closeColorMenu() {
    this.colorMenu?.remove();
    this.colorMenu = null;
  }
  build() {
    const { container, isList } = this.deps;
    const menu = container.createDiv({ cls: "ntn-root ntn-select-menu" });
    const currentEl = menu.createDiv({ cls: "ntn-select-current" });
    this.pillsWrap = currentEl.createDiv({ cls: "ntn-select-pills" });
    this.input = currentEl.createEl("input", {
      type: "text",
      cls: "ntn-select-input",
      attr: { placeholder: "Search or create\u2026", spellcheck: "false" }
    });
    menu.createDiv({
      cls: "ntn-select-hint",
      text: isList ? "Select options or create one" : "Select an option or create one"
    });
    this.optionsEl = menu.createDiv({ cls: "ntn-select-options" });
    this.input.addEventListener("input", () => this.renderOptions());
    this.input.addEventListener("keydown", (evt) => this.onKeydown(evt));
    this.renderPills();
    this.renderOptions();
    this.input.focus();
    return menu;
  }
  /** Empty selection deletes the property (`write` treats `null` as delete). */
  write() {
    const out = this.deps.isList ? this.selected.length ? this.selected : null : this.selected[0] ?? null;
    this.deps.write(out);
  }
  renderPills() {
    this.pillsWrap.empty();
    for (const v of this.selected) {
      const pill = this.pillsWrap.createSpan({ cls: "ntn-pill" });
      this.deps.applyColor(pill, v);
      pill.createSpan({ text: v });
      const x = pill.createSpan({ cls: "ntn-pill-remove", text: "\u2715" });
      x.addEventListener("click", (evt) => {
        evt.stopPropagation();
        this.selected = this.selected.filter((s) => s !== v);
        this.write();
        this.renderPills();
        this.renderOptions();
      });
    }
  }
  pick(v) {
    if (this.deps.isList) {
      const has = this.selected.some((s) => s.toLowerCase() === v.toLowerCase());
      this.selected = has ? this.selected.filter((s) => s.toLowerCase() !== v.toLowerCase()) : [...this.selected, v];
      if (!this.known.has(v.toLowerCase())) this.known.set(v.toLowerCase(), v);
      this.write();
      this.input.value = "";
      this.renderPills();
      this.renderOptions();
      this.input.focus();
    } else {
      this.selected = [v];
      this.write();
      this.close();
    }
  }
  renderOptions() {
    this.closeColorMenu();
    this.optionsEl.empty();
    const q = this.input.value.trim();
    const ql = q.toLowerCase();
    const visible = [...this.known.values()].filter((o) => !ql || o.toLowerCase().includes(ql)).sort((a, b) => a.localeCompare(b, void 0, { sensitivity: "base" }));
    for (const o of visible) {
      const row = this.optionsEl.createDiv({ cls: "ntn-select-option" });
      const colorBtn = row.createSpan({
        cls: "ntn-select-color-btn",
        attr: { "aria-label": "Change color" }
      });
      this.deps.applyColor(colorBtn, o);
      colorBtn.addEventListener("click", (evt) => {
        evt.stopPropagation();
        this.openColorMenu(colorBtn, o);
      });
      const pill = row.createSpan({ cls: "ntn-pill" });
      this.deps.applyColor(pill, o);
      pill.setText(o);
      if (this.selected.some((s) => s.toLowerCase() === o.toLowerCase())) {
        row.createSpan({ cls: "ntn-select-check", text: "\u2713" });
      }
      row.addEventListener("click", () => this.pick(o));
    }
    if (q && !this.known.has(ql)) {
      const row = this.optionsEl.createDiv({ cls: "ntn-select-option" });
      row.createSpan({ cls: "ntn-select-create", text: "Create" });
      const pill = row.createSpan({ cls: "ntn-pill" });
      this.deps.applyColor(pill, q);
      pill.setText(q);
      row.addEventListener("click", () => this.pick(q));
    }
    if (!visible.length && !q) {
      this.optionsEl.createDiv({
        cls: "ntn-select-empty",
        text: "No options yet \u2014 type to create one"
      });
    }
  }
  onKeydown(evt) {
    if (evt.key === "Escape") {
      evt.preventDefault();
      evt.stopPropagation();
      this.close();
    } else if (evt.key === "Enter") {
      const q = this.input.value.trim();
      if (q) this.pick(this.known.get(q.toLowerCase()) ?? q);
      else this.close();
    } else if (evt.key === "Backspace" && this.input.value === "" && this.deps.isList && this.selected.length) {
      this.selected = this.selected.slice(0, -1);
      this.write();
      this.renderPills();
      this.renderOptions();
    }
  }
  /** Open the color picker for a value, anchored to its row button. */
  openColorMenu(anchorEl, value) {
    this.closeColorMenu();
    const menu = this.deps.container.createDiv({ cls: "ntn-root ntn-color-menu" });
    this.colorMenu = menu;
    const apply = (spec) => {
      this.deps.setColor(value, spec);
      this.renderPills();
      this.renderOptions();
    };
    this.buildCustomColorSection(menu, anchorEl, apply);
    menu.createDiv({ cls: "ntn-color-section", text: "Notion colors" });
    for (const c of NOTION_COLORS) {
      const item = menu.createDiv({ cls: "ntn-color-option" });
      const swatch = item.createSpan({ cls: "ntn-color-swatch" });
      applyColorVars(swatch, c);
      item.createSpan({ cls: "ntn-color-name", text: c.name });
      item.addEventListener("click", (evt) => {
        evt.stopPropagation();
        apply(c.name);
      });
    }
    this.clampToWindow(menu, anchorEl.getBoundingClientRect());
  }
  /**
   * The "any color you like" half of the picker: the OS color dialog plus a
   * hex field, both committing a `#rrggbb` spec. Seeded with the value's
   * current color, read back from the CSS variables `applyColor` just set on
   * the row's swatch (they hold a plain hex for every palette entry).
   */
  buildCustomColorSection(menu, anchorEl, apply) {
    const currentBg = anchorEl.style.getPropertyValue("--ntn-pill-bg-light").trim();
    const seed = /^#[0-9a-f]{6}$/i.test(currentBg) ? currentBg : "#cccccc";
    menu.createDiv({ cls: "ntn-color-section", text: "Custom" });
    const row = menu.createDiv({ cls: "ntn-color-custom" });
    const picker = row.createEl("input", {
      type: "color",
      cls: "ntn-color-input",
      attr: { "aria-label": "Pick a custom color" }
    });
    picker.value = seed;
    picker.addEventListener("change", () => apply(picker.value));
    picker.addEventListener("click", (evt) => evt.stopPropagation());
    const hex = row.createEl("input", {
      type: "text",
      cls: "ntn-color-hex",
      attr: { placeholder: seed, spellcheck: "false", "aria-label": "Custom color hex" }
    });
    const commitHex = () => {
      const spec = hex.value.trim();
      if (!spec) return;
      if (customColor(spec)) apply(spec);
      else hex.addClass("ntn-color-hex-invalid");
    };
    hex.addEventListener("input", () => hex.removeClass("ntn-color-hex-invalid"));
    hex.addEventListener("click", (evt) => evt.stopPropagation());
    hex.addEventListener("keydown", (evt) => {
      if (evt.key === "Enter") {
        evt.preventDefault();
        commitHex();
      } else if (evt.key === "Escape") {
        evt.preventDefault();
        evt.stopPropagation();
        this.closeColorMenu();
      }
    });
  }
  /** Anchor the main menu below the cell, then clamp into the window. */
  position() {
    const rect = this.deps.anchor.getBoundingClientRect();
    this.menu.setCssStyles({ minWidth: `${Math.max(rect.width, 220)}px` });
    this.clampToWindow(this.menu, rect);
  }
};

// src/view/notion-table-view.ts
var TITLE_SORT_PROPERTY = "file.name";
var NotionTableView = class extends import_obsidian7.BasesView {
  constructor(controller, parentEl) {
    super(controller);
    this.type = NOTION_TABLE_VIEW;
    /** True while the toolbar's New button is rerouted to the page panel. */
    this.newButtonPatched = false;
    /** Pill / list classification, recomputed each update. */
    this.pills = { pillProps: /* @__PURE__ */ new Set(), listProps: /* @__PURE__ */ new Set() };
    /** User-pinned value → color overrides from the `pinnedColors` view option. */
    this.pinnedColors = /* @__PURE__ */ new Map();
    /** Column key → user-dragged width; unlisted columns size themselves. */
    this.columnWidths = /* @__PURE__ */ new Map();
    /** Property → LOCAL footer calculation (core ones live in the view's `summaries`). */
    this.calculations = /* @__PURE__ */ new Map();
    /** How the Name column's icons render (the `titleIcon` view option). */
    this.titleIcon = { mode: "page", custom: "" };
    /**
     * The open floating editor (select or date), if any — at most one at a
     * time; also drives outside-click detection.
     */
    this.editor = null;
    this.queryCtrl = controller;
    this.rootEl = parentEl.createDiv({ cls: "ntn-root" });
    this.register(() => this.closeEditor());
    this.registerDomEvent(this.rootEl.doc, "mousedown", (evt) => {
      if (!this.editor) return;
      const target = evt.target;
      if (this.editor.contains(target)) return;
      if (this.editor.anchorEl.contains(target)) return;
      this.closeEditor();
    }, { capture: true });
    this.patchToolbarNew();
  }
  onDataUpdated() {
    this.patchToolbarNew();
    const root = this.rootEl;
    root.empty();
    root.toggleClass("ntn-wrap", this.config.get("wrapCells") !== false);
    root.toggleClass("ntn-vlines", this.config.get("verticalLines") !== false);
    const props = this.config.getOrder();
    this.pills = computePillProps(props, this.data.data, this.config, this.app);
    this.pinnedColors = parsePinnedColors(this.config.get("pinnedColors"));
    this.columnWidths = parseColumnWidths(this.config.get("columnWidths"));
    this.calculations = parseCalculations(this.config.get("calculations"));
    this.titleIcon = {
      mode: String(this.config.get("titleIcon") ?? "page"),
      custom: String(this.config.get("titleIconCustom") ?? "").trim()
    };
    const table = root.createEl("table", { cls: "ntn-table" });
    const thead = table.createEl("thead");
    const headRow = thead.createEl("tr");
    const sorts = this.config.getSort();
    const thTitle = headRow.createEl("th", { cls: "ntn-th ntn-col-title" });
    const titleLabel = thTitle.createSpan({ cls: "ntn-th-content" });
    if (this.titleIcon.mode !== "none") {
      titleLabel.createSpan({ cls: "ntn-th-icon", text: "Aa" });
    }
    titleLabel.createSpan({ text: "Name" });
    this.setupColumn(thTitle, TITLE_COLUMN_KEY, 0);
    this.setupSort(thTitle, titleLabel, TITLE_SORT_PROPERTY, sorts);
    props.forEach((prop, i) => {
      const th = headRow.createEl("th", { cls: "ntn-th" });
      const label = th.createSpan({ cls: "ntn-th-content" });
      label.createSpan({ text: this.config.getDisplayName(prop) });
      this.setupColumn(th, prop, i + 1);
      this.setupSort(th, label, prop, sorts);
    });
    const tbody = table.createEl("tbody");
    const colCount = props.length + 1;
    for (const group of this.data.groupedData) {
      if (group.hasKey() && group.key) {
        const gRow = tbody.createEl("tr", { cls: "ntn-group-row" });
        const gCell = gRow.createEl("td", { attr: { colspan: String(colCount) } });
        const keyText = group.key.toString();
        const isTag = group.key instanceof import_obsidian7.TagValue;
        const pill = gCell.createSpan({ cls: "ntn-pill" });
        this.applyPillColor(pill, keyText);
        pill.setText(isTag ? keyText.replace(/^#/, "") : keyText);
        if (isTag) this.makeTagPill(pill, keyText);
        gCell.createSpan({ cls: "ntn-group-count", text: String(group.entries.length) });
      }
      for (const entry of group.entries) {
        this.renderRow(tbody, entry, props);
      }
    }
    this.renderCalcRow(table, props);
    const newRow = root.createDiv({ cls: "ntn-new-row" });
    newRow.createSpan({ cls: "ntn-new-plus", text: "+" });
    newRow.createSpan({ text: "New" });
    newRow.addEventListener("click", () => void this.createAndOpenPage());
  }
  renderRow(tbody, entry, props) {
    const tr = tbody.createEl("tr", { cls: "ntn-row" });
    const titleTd = tr.createEl("td", { cls: "ntn-td ntn-col-title" });
    this.applyColumnWidth(titleTd, TITLE_COLUMN_KEY);
    const titleWrap = titleTd.createDiv({ cls: "ntn-title-wrap" });
    this.renderTitleIcon(titleWrap);
    const link = titleWrap.createSpan({
      cls: "ntn-title-text",
      text: entry.file.basename
    });
    link.addEventListener("click", (evt) => {
      void this.app.workspace.openLinkText(
        entry.file.path,
        "",
        evt.ctrlKey || evt.metaKey
      );
    });
    const openBtn = titleWrap.createSpan({ cls: "ntn-open-btn", text: "OPEN" });
    openBtn.addEventListener("click", (evt) => {
      evt.stopPropagation();
      if (this.config.get("openMode") === "panel") {
        this.openPagePanel(entry.file);
      } else {
        void this.app.workspace.openLinkText(entry.file.path, "", true);
      }
    });
    for (const prop of props) {
      const td = tr.createEl("td", { cls: "ntn-td" });
      this.applyColumnWidth(td, prop);
      this.renderCell(td, entry, prop);
    }
  }
  /**
   * Pin a cell to its column's dragged width. A column's width is the max
   * over all its cells, so the constraint has to land on every `th`/`td` of
   * the column, not just the header. `min-width` is part of it because the
   * stylesheet pins the title column at 280px, and `max-width` because the
   * table stays in `table-layout: auto` (switching to `fixed` would undo the
   * `width: max-content` narrow-container fix — see bug history #4).
   */
  applyColumnWidth(cell, key) {
    const width = this.columnWidths.get(key);
    if (width === void 0) return;
    const px = `${width}px`;
    cell.setCssStyles({ width: px, minWidth: px, maxWidth: px });
  }
  /**
   * The icon at the head of each Name cell. Notion's page emoji is the
   * default, but it is a fixed glyph that can sit badly against a theme —
   * so the `titleIcon` view option also offers Obsidian's own file icon
   * (which takes the theme's color), any emoji or Lucide icon the user
   * names, or no icon at all.
   */
  renderTitleIcon(wrap) {
    const { mode, custom } = this.titleIcon;
    if (mode === "none") return;
    const el = wrap.createSpan({ cls: "ntn-page-icon" });
    if (mode === "theme") {
      this.setLucideIcon(el, "file-text");
      return;
    }
    if (mode === "custom" && custom) {
      const named = /^[a-z][a-z0-9-]*$/.test(custom);
      if (named && this.setLucideIcon(el, custom)) return;
      el.setText(custom);
      return;
    }
    el.addClass("ntn-page-icon-emoji");
    el.setText("\u{1F4C4}");
  }
  /**
   * Draw a Lucide icon into the span. Returns false — leaving the span
   * untouched — when the name isn't a real icon, since `setIcon` fails
   * silently and would otherwise leave an empty gap before the title.
   */
  setLucideIcon(el, name) {
    el.addClass("ntn-page-icon-lucide");
    (0, import_obsidian7.setIcon)(el, name);
    if (el.firstElementChild) return true;
    el.removeClass("ntn-page-icon-lucide");
    return false;
  }
  /** Apply a header cell's stored width and give it a drag-to-resize handle. */
  setupColumn(th, key, colIndex) {
    this.applyColumnWidth(th, key);
    const handle = th.createDiv({ cls: "ntn-col-resize" });
    handle.addEventListener("pointerdown", (evt) => {
      evt.preventDefault();
      evt.stopPropagation();
      const startX = evt.clientX;
      const startWidth = th.getBoundingClientRect().width;
      const cells = this.columnCells(th, colIndex);
      let width = startWidth;
      let moved = false;
      handle.setPointerCapture(evt.pointerId);
      handle.addClass("ntn-col-resize-active");
      this.rootEl.addClass("ntn-resizing");
      const onMove = (e) => {
        if (e.clientX === startX) return;
        moved = true;
        width = Math.max(MIN_COLUMN_WIDTH, startWidth + e.clientX - startX);
        const px = `${Math.round(width)}px`;
        for (const cell of cells) {
          cell.setCssStyles({ width: px, minWidth: px, maxWidth: px });
        }
      };
      const onEnd = () => {
        handle.removeEventListener("pointermove", onMove);
        handle.removeEventListener("pointerup", onEnd);
        handle.removeEventListener("pointercancel", onEnd);
        handle.removeClass("ntn-col-resize-active");
        this.rootEl.removeClass("ntn-resizing");
        if (moved) this.saveColumnWidth(key, Math.round(width));
      };
      handle.addEventListener("pointermove", onMove);
      handle.addEventListener("pointerup", onEnd);
      handle.addEventListener("pointercancel", onEnd);
    });
    handle.addEventListener("dblclick", (evt) => {
      evt.preventDefault();
      evt.stopPropagation();
      this.saveColumnWidth(key, null);
      this.onDataUpdated();
    });
  }
  /**
   * Notion's header interaction: a sorted column shows its direction arrow
   * after the name, and clicking a header opens a menu with Sort ascending /
   * Sort descending (plus Remove sort while the column is sorted). The write
   * goes through the internal `setSortProperty` — if it's ever missing the
   * header stays inert (arrow still drawn) and the toolbar's Sort menu keeps
   * working, so the view degrades rather than breaks.
   */
  setupSort(th, label, prop, sorts) {
    const active = sorts.find((s) => s.property === prop);
    if (active) {
      const arrow = label.createSpan({ cls: "ntn-th-sort" });
      (0, import_obsidian7.setIcon)(arrow, active.direction === "ASC" ? "arrow-up" : "arrow-down");
    }
    if (!this.sortableConfig()) return;
    th.addClass("ntn-th-sortable");
    th.addEventListener("click", (evt) => {
      if (evt.target.closest(".ntn-col-resize")) return;
      this.openHeaderMenu(th, prop, active?.direction);
    });
  }
  /** The column header's sort menu, dropped under the header like Notion's. */
  openHeaderMenu(th, prop, current) {
    const config = this.sortableConfig();
    if (!config) return;
    this.closeEditor();
    const menu = new import_obsidian7.Menu();
    menu.addItem((item) => item.setTitle("Sort ascending").setIcon("arrow-up").setChecked(current === "ASC").onClick(() => config.setSortProperty(prop, "ASC")));
    menu.addItem((item) => item.setTitle("Sort descending").setIcon("arrow-down").setChecked(current === "DESC").onClick(() => config.setSortProperty(prop, "DESC")));
    if (current) {
      menu.addSeparator();
      menu.addItem((item) => item.setTitle("Remove sort").setIcon("x").onClick(() => config.setSortProperty(prop, "NONE")));
    }
    const rect = th.getBoundingClientRect();
    menu.showAtPosition({ x: rect.left, y: rect.bottom + 4 }, th.doc);
  }
  /**
   * Notion's "Calculate" footer: one cell per column that shows the chosen
   * calculation as label + value, or a hover-revealed "Calculate" placeholder;
   * either opens the menu. Computed over the whole filtered result (not per
   * group). Core-backed calculations are read from the view's `summaries`
   * and evaluated by `getSummaryValue`; Count all and the percentages —
   * which core has no function for — are derived here (see lib/calculations).
   */
  renderCalcRow(table, props) {
    const tr = table.createEl("tfoot").createEl("tr", { cls: "ntn-calc-row" });
    const entries = this.data.data;
    this.renderCalcCell(tr, TITLE_COLUMN_KEY, TITLE_SORT_PROPERTY, entries);
    for (const prop of props) this.renderCalcCell(tr, prop, prop, entries);
  }
  renderCalcCell(tr, widthKey, prop, entries) {
    const td = tr.createEl("td", { cls: "ntn-td ntn-calc" });
    this.applyColumnWidth(td, widthKey);
    const kind = calcKind(sampleValue(entries, prop));
    const key = this.calculationFor(prop);
    if (key) {
      td.createSpan({ cls: "ntn-calc-label", text: calcLabel(key, kind) });
      td.createSpan({ cls: "ntn-calc-value", text: this.calcValue(prop, key, entries) });
    } else {
      const placeholder = td.createSpan({ cls: "ntn-calc-placeholder" });
      placeholder.createSpan({ text: "Calculate" });
      (0, import_obsidian7.setIcon)(placeholder.createSpan({ cls: "ntn-calc-chevron" }), "chevron-down");
    }
    td.addEventListener("click", () => this.openCalcMenu(td, prop, kind, key));
  }
  /** The column's calculation key: a local one wins, else the core summary. */
  calculationFor(prop) {
    return this.calculations.get(prop) ?? this.summaryConfig()?.getSummaryKey(prop) ?? null;
  }
  /** Evaluate a calculation to its display text; `—` when core has no value. */
  calcValue(prop, key, entries) {
    if (!isLocalCalc(key)) return this.summaryText(prop, key, entries);
    const base = localCalcBase(key);
    if (base === null) return String(entries.length);
    const n = Number(this.summaryText(prop, base, entries));
    return Number.isFinite(n) ? formatPercent(n, entries.length) : "\u2014";
  }
  summaryText(prop, key, entries) {
    const value = this.data.getSummaryValue(this.queryCtrl, entries, prop, key);
    return value instanceof import_obsidian7.NullValue ? "\u2014" : value.toString();
  }
  /** The footer cell's menu: None, then the calculations for the column's kind. */
  openCalcMenu(td, prop, kind, current) {
    this.closeEditor();
    const summary = this.summaryConfig();
    const menu = new import_obsidian7.Menu();
    menu.addItem((item) => item.setTitle("None").setChecked(current === null).onClick(() => this.setCalculation(prop, null)));
    menu.addSeparator();
    for (const opt of calcOptions(kind)) {
      if (!opt.local && !summary) continue;
      menu.addItem((item) => item.setTitle(opt.label).setChecked(current === opt.key).onClick(() => this.setCalculation(prop, opt.key)));
    }
    const custom = summary ? this.customSummaryKeys() : [];
    if (custom.length) {
      menu.addSeparator();
      for (const key of custom) {
        menu.addItem((item) => item.setTitle(key).setIcon("square-function").setChecked(current === key).onClick(() => this.setCalculation(prop, key)));
      }
    }
    const rect = td.getBoundingClientRect();
    menu.showAtPosition({ x: rect.left, y: rect.bottom + 4 }, td.doc);
  }
  /**
   * Persist a column's calculation. Local keys go to our `calculations`
   * config entry and core keys to the view's `summaries` — each column holds
   * at most one, so setting either side clears the other. Both writes save
   * the view config, which re-renders us.
   */
  setCalculation(prop, key) {
    const summary = this.summaryConfig();
    const local = key !== null && isLocalCalc(key);
    summary?.setSummaryKey(prop, local ? null : key);
    const had = this.calculations.get(prop);
    if (local) {
      if (had === key) return;
      this.calculations.set(prop, key);
    } else {
      if (had === void 0) return;
      this.calculations.delete(prop);
    }
    this.config.set("calculations", serializeCalculations(this.calculations));
  }
  /** Names of the custom summary formulas defined in this base, if reachable. */
  customSummaryKeys() {
    const query = this.queryCtrl.query;
    const formulas = query?.summaryFormulas;
    return formulas && typeof formulas === "object" ? Object.keys(formulas) : [];
  }
  /** The view config's internal summary accessors, or null if this Obsidian lacks them. */
  summaryConfig() {
    const cfg = this.config;
    return typeof cfg.getSummaryKey === "function" && typeof cfg.setSummaryKey === "function" ? cfg : null;
  }
  /** The view config's internal sort setter, or null if this Obsidian lacks it. */
  sortableConfig() {
    const cfg = this.config;
    return typeof cfg.setSortProperty === "function" ? cfg : null;
  }
  /**
   * Every `td` of one column, plus its header. Group rows hold a single
   * `colspan` cell, so only `.ntn-row`s carry a td at this index.
   */
  columnCells(th, colIndex) {
    const cells = [th];
    const table = th.closest("table");
    if (!table) return cells;
    const tds = table.querySelectorAll(
      `tr.ntn-row > td:nth-child(${colIndex + 1})`
    );
    tds.forEach((td) => cells.push(td));
    return cells;
  }
  /** Persist (or clear, with `null`) one column's width in the view config. */
  saveColumnWidth(key, width) {
    if (width === null) {
      this.columnWidths.delete(key);
    } else {
      this.columnWidths.set(key, width);
    }
    this.config.set("columnWidths", serializeColumnWidths(this.columnWidths));
  }
  renderCell(td, entry, prop) {
    const value = entry.getValue(prop);
    const editable = prop.startsWith("note.");
    const propName = prop.split(".").slice(1).join(".");
    if (this.pills.pillProps.has(prop)) {
      const wrap = td.createDiv({ cls: "ntn-pills" });
      for (const item of valueToItems(value)) {
        const pill = wrap.createSpan({ cls: "ntn-pill" });
        this.applyPillColor(pill, item.text);
        pill.setText(item.text.replace(/^#/, ""));
        if (item.isTag) this.makeTagPill(pill, item.text);
      }
      if (editable) {
        td.addClass("ntn-editable");
        td.addEventListener(
          "click",
          () => this.openSelectEditor(td, entry, prop, propName)
        );
        this.editor?.reanchorIfMatches(td, entry.file.path, prop);
      }
      return;
    }
    if (value instanceof import_obsidian7.BooleanValue) {
      const cb = td.createEl("input", { type: "checkbox", cls: "ntn-checkbox" });
      cb.checked = value.isTruthy();
      if (editable) {
        cb.addEventListener("change", () => {
          void this.writeProperty(entry.file, propName, cb.checked);
        });
      } else {
        cb.disabled = true;
      }
      return;
    }
    const cellEl = td.createDiv({ cls: "ntn-cell" });
    if (value !== null) {
      value.renderTo(cellEl, this.app.renderContext);
    }
    if (!editable) return;
    td.addClass("ntn-editable");
    const isDate = value instanceof import_obsidian7.DateValue || value === null && isDateWidget(propertyWidget(this.app, propName));
    if (isDate) {
      td.addEventListener("click", () => this.openDateAt({
        anchor: td,
        file: entry.file,
        propName,
        current: value ? value.toString() : ""
      }));
      this.editor?.reanchorIfMatches(td, entry.file.path, prop);
      return;
    }
    const kind = value instanceof import_obsidian7.NumberValue ? "number" : "text";
    td.addEventListener("click", (evt) => {
      if (evt.target.closest("a")) return;
      this.editCell(td, entry, propName, value ? value.toString() : "", kind);
    });
  }
  /** Swap a cell's content for an input; commit on Enter/blur, cancel on Esc. */
  editCell(td, entry, propName, current, kind) {
    if (td.querySelector(".ntn-input")) return;
    const rect = td.getBoundingClientRect();
    const multiline = kind === "text" && rect.height > 40;
    const style = td.win.getComputedStyle(td);
    const padX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
    const padY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
    td.empty();
    const input = multiline ? td.createEl("textarea", { cls: "ntn-input ntn-textarea" }) : td.createEl("input", { type: "text", cls: "ntn-input" });
    input.setCssStyles({
      width: `${Math.max(0, rect.width - padX)}px`,
      height: `${Math.max(0, rect.height - padY)}px`
    });
    input.value = current;
    input.focus();
    input.select();
    let committed = false;
    const commit = () => {
      if (committed) return;
      committed = true;
      const raw = input.value.trim();
      if (raw === current) {
        this.onDataUpdated();
        return;
      }
      let out = raw;
      if (kind === "number") {
        const n = Number(raw);
        out = raw === "" ? null : Number.isNaN(n) ? raw : n;
      } else if (raw === "") {
        out = null;
      }
      td.empty();
      td.createDiv({ cls: "ntn-cell", text: raw });
      void this.writeProperty(entry.file, propName, out);
    };
    input.addEventListener("keydown", (ev) => {
      const evt = ev;
      if (evt.key === "Enter" && !evt.shiftKey) {
        evt.preventDefault();
        commit();
      } else if (evt.key === "Escape") {
        committed = true;
        this.onDataUpdated();
      }
    });
    input.addEventListener("blur", commit);
  }
  async writeProperty(file, propName, value) {
    try {
      await this.app.fileManager.processFrontMatter(file, (fm) => {
        if (value === null) {
          delete fm[propName];
        } else {
          fm[propName] = value;
        }
      });
    } catch (e) {
      console.error(`${LOG_PREFIX} failed to write property`, propName, e);
      new import_obsidian7.Notice(`Couldn't update "${propName}".`);
      this.onDataUpdated();
    }
  }
  /**
   * Reroute the core toolbar's New button to the page panel while this
   * view is active. The button lives on the query controller, outside this
   * view's DOM, so its menu's `open` is shadowed on the instance and
   * restored on unload. `newItemMenu` is internal API — if it ever moves,
   * the guard below simply leaves the core behavior untouched (and the
   * footer "+ New" falls back to its own capture flow).
   */
  patchToolbarNew() {
    if (this.newButtonPatched) return;
    const menu = this.queryCtrl.newItemMenu;
    if (!menu || typeof menu.open !== "function" || typeof menu.close !== "function") {
      return;
    }
    const orig = menu.open.bind(menu);
    const patched = async (name, fmProc) => {
      if (import_obsidian7.Platform.isPhone) return orig(name, fmProc);
      let created;
      const ref = this.app.vault.on("create", (file) => {
        if (file instanceof import_obsidian7.TFile) created = file;
      });
      const body = this.rootEl.doc.body;
      body.addClass("ntn-hide-new-popover");
      try {
        await orig(name, fmProc);
      } finally {
        this.app.vault.offref(ref);
        menu.close();
        body.removeClass("ntn-hide-new-popover");
      }
      if (created) this.openPagePanel(created);
    };
    menu.open = patched;
    this.newButtonPatched = true;
    this.register(() => {
      menu.open = orig;
      this.newButtonPatched = false;
    });
  }
  /**
   * "+ New" flow: create the note through the core Bases flow — so it lands
   * in the configured folder and gets the frontmatter implied by the view's
   * filters — then edit it in the centered Notion-style page panel instead
   * of the small popover Obsidian anchors to the toolbar's New button.
   */
  async createAndOpenPage() {
    if (import_obsidian7.Platform.isPhone || this.newButtonPatched) {
      await this.createFileForView();
      return;
    }
    let created;
    const ref = this.app.vault.on("create", (file) => {
      if (file instanceof import_obsidian7.TFile) created = file;
    });
    try {
      await this.createFileForView();
    } finally {
      this.app.vault.offref(ref);
    }
    if (!created) return;
    const doc = this.rootEl.doc;
    if (doc.querySelector(".bases-new-item-popover")) doc.body.click();
    this.openPagePanel(created);
  }
  /** Open a note centered in the Notion-style page panel. */
  openPagePanel(file) {
    new NotePageModal(this.app, file, {
      applyColor: (pill, text) => this.applyPillColor(pill, text),
      write: (f, propName, value) => this.writeProperty(f, propName, value),
      isPillProp: (name) => this.pills.pillProps.has(`note.${name}`),
      isListProp: (name) => this.pills.listProps.has(`note.${name}`),
      isDateProp: (name) => isDateWidget(propertyWidget(this.app, name)),
      openSelect: (opts) => this.openSelectAt(opts),
      openDate: (opts) => this.openDateAt(opts),
      reanchorEditor: (anchor, filePath, propName) => void this.editor?.reanchorIfMatches(
        anchor,
        filePath,
        `note.${propName}`
      ),
      closeEditor: () => this.closeEditor()
    }).open();
  }
  /**
   * Make a pill behave like a tag link: clicking it searches the vault, the
   * way tags do in core Bases and in rendered notes. The click never reaches
   * the cell, so a tag in an editable pill column doesn't also open the
   * select editor — click the cell's empty space for that.
   */
  makeTagPill(pill, tag) {
    pill.addClass("ntn-pill-tag");
    pill.addEventListener("click", (evt) => {
      evt.stopPropagation();
      openTagSearch(this.app, tag);
    });
  }
  /** Color a pill element using this view's pinned-color overrides. */
  applyPillColor(pill, text) {
    applyPillColor(pill, text, this.pinnedColors);
  }
  /** Open the Notion-style select editor for a pill cell of the table. */
  openSelectEditor(td, entry, prop, propName) {
    this.openSelectAt({
      anchor: td,
      file: entry.file,
      propName,
      current: valueToStrings(entry.getValue(prop)),
      isList: this.pills.listProps.has(prop)
    });
  }
  /**
   * Open the select editor anchored anywhere — a table cell or a property
   * row of the page panel. Known values always come from the live query
   * result; lifetime stays with the view (outside-click / Esc / unload).
   */
  openSelectAt(opts) {
    this.openEditor(opts.anchor, () => new SelectEditor({
      win: this.rootEl.win,
      container: opts.container ?? this.rootEl.doc.body,
      anchor: opts.anchor,
      entries: this.data.data,
      file: opts.file,
      current: opts.current,
      prop: `note.${opts.propName}`,
      isList: opts.isList,
      applyColor: (pill, text) => this.applyPillColor(pill, text),
      write: (value) => void this.writeProperty(opts.file, opts.propName, value).then(() => opts.onWrite?.()),
      setColor: (value, color) => this.setPinnedColor(value, color),
      onClose: () => {
        this.editor = null;
      }
    }));
  }
  /**
   * Open the calendar editor anchored to a date cell or property row. The
   * time selector shows for properties the vault types as `datetime`, and
   * for any value that already carries a time (so it's never silently
   * dropped when the property isn't typed).
   */
  openDateAt(opts) {
    const withTime = propertyWidget(this.app, opts.propName) === "datetime" || splitDateTime(opts.current).time !== "";
    this.openEditor(opts.anchor, () => new DateEditor({
      win: this.rootEl.win,
      container: opts.container ?? this.rootEl.doc.body,
      anchor: opts.anchor,
      file: opts.file,
      current: opts.current,
      withTime,
      prop: `note.${opts.propName}`,
      write: (value) => void this.writeProperty(opts.file, opts.propName, value).then(() => opts.onWrite?.()),
      onClose: () => {
        this.editor = null;
      }
    }));
  }
  /**
   * Replace the open floating editor with a new one — unless the click is on
   * the element whose editor is already open, which toggles it shut instead
   * (the outside-mousedown listener leaves anchor clicks alone for this).
   */
  openEditor(anchor, create) {
    if (this.editor?.anchorEl === anchor) {
      this.closeEditor();
      return;
    }
    this.closeEditor();
    this.editor = create();
  }
  /**
   * Pin a value to a color — a Notion palette name or any custom hex. Updates
   * the live map for instant feedback in the open editor, then persists into
   * the `pinnedColors` view option (replacing any prior entry for the same
   * value) so it survives reloads and is editable from the view settings too.
   * The stored spec is the resolved color's canonical name (`green`, or a
   * normalized `#rrggbb`).
   */
  setPinnedColor(value, spec) {
    const color = parseColorSpec(spec);
    if (!color) return;
    const bare = value.replace(/^#/, "");
    const key = bare.toLowerCase();
    this.pinnedColors.set(key, color);
    const raw = this.config.get("pinnedColors");
    const list = Array.isArray(raw) ? raw.map((s) => String(s)) : [];
    const kept = list.filter((item) => {
      const m = item.match(/^(.+?)\s*[=:]\s*(.+)$/);
      return m ? m[1].trim().replace(/^#/, "").toLowerCase() !== key : true;
    });
    kept.push(`${bare}=${color.name}`);
    this.config.set("pinnedColors", kept);
  }
  closeEditor() {
    this.editor?.close();
    this.editor = null;
  }
};

// src/main.ts
var NotionBasesPlugin = class extends import_obsidian8.Plugin {
  async onload() {
    if (typeof this.registerBasesView !== "function") {
      new import_obsidian8.Notice("GoodBases: requires Obsidian 1.10.0+ (registerBasesView API missing).", 8e3);
      return;
    }
    const ok = this.registerBasesView(NOTION_TABLE_VIEW, {
      name: "Notion-style table",
      icon: "lucide-table-2",
      factory: (controller, containerEl) => new NotionTableView(controller, containerEl),
      options: buildViewOptions
    });
    if (!ok) {
      new import_obsidian8.Notice("GoodBases: view registration failed. Is the Bases core plugin enabled?", 8e3);
    }
  }
};

/* nosourcemap */