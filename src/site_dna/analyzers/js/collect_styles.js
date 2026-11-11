() => {
  const MAX_ELEMENTS = 5000;
  const MAX_BUTTONS = 200;
  const MAX_LINKS = 200;
  const MAX_HEADINGS = 3;
  const SVG_TAGS = new Set([
    "svg", "path", "circle", "rect", "polygon", "line", "polyline", "ellipse", "g", "use",
  ]);

  function parseAlpha(color) {
    if (!color) return 0;
    const value = String(color).trim().toLowerCase();
    if (value === "transparent") return 0;
    const match = value.match(/^rgba?\((.*)\)$/);
    if (!match) return 1;
    const parts = match[1].replace("/", " ").replace(/,/g, " ").split(/\s+/).filter(Boolean);
    if (parts.length < 4) return 1;
    const raw = parts[3];
    const alpha = raw.endsWith("%") ? parseFloat(raw) / 100 : parseFloat(raw);
    return Number.isFinite(alpha) ? alpha : 1;
  }

  function effectiveBackground(el) {
    let node = el;
    while (node && node.nodeType === 1) {
      const background = getComputedStyle(node).backgroundColor;
      if (background && parseAlpha(background) >= 0.99) return background;
      node = node.parentElement;
    }
    return "rgb(255, 255, 255)";
  }

  function isVisible(style, rect) {
    return rect.width > 0 && rect.height > 0 &&
      style.display !== "none" &&
      style.visibility !== "hidden" &&
      parseFloat(style.opacity || "1") > 0;
  }

  function directTextLength(el) {
    let length = 0;
    for (const node of el.childNodes) {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = (node.textContent || "").trim();
        if (text) length += text.length;
      }
    }
    return length;
  }

  function styleSample(el, style, rect) {
    const tag = el.tagName.toLowerCase();
    const borderWidth = parseFloat(style.borderTopWidth || "0") || 0;
    const isSvg = SVG_TAGS.has(tag) ||
      (typeof SVGElement !== "undefined" && el instanceof SVGElement);
    const textLength = directTextLength(el);
    return {
      tag: tag,
      color: style.color || null,
      backgroundColor: style.backgroundColor || null,
      borderColor: borderWidth > 0 ? (style.borderTopColor || null) : null,
      borderWidth: borderWidth,
      fill: isSvg ? (style.fill || null) : null,
      stroke: isSvg ? (style.stroke || null) : null,
      fontFamily: style.fontFamily || null,
      fontSize: style.fontSize || null,
      fontWeight: style.fontWeight || null,
      hasText: textLength > 0,
      textLength: textLength,
      area: rect.width * rect.height,
      effectiveBg: effectiveBackground(el),
    };
  }

  function collectForSelector(selector, limit) {
    const output = [];
    const nodes = document.querySelectorAll(selector);
    for (const el of nodes) {
      if (output.length >= limit) break;
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      if (!isVisible(style, rect)) continue;
      output.push(styleSample(el, style, rect));
    }
    return output;
  }

  function collectHeadings(selector) {
    const output = [];
    const nodes = document.querySelectorAll(selector);
    for (const el of nodes) {
      if (output.length >= MAX_HEADINGS) break;
      const style = getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      if (!isVisible(style, rect)) continue;
      output.push({
        color: style.color || null,
        fontSize: style.fontSize || null,
        fontWeight: style.fontWeight || null,
        fontFamily: style.fontFamily || null,
        lineHeight: style.lineHeight || null,
        letterSpacing: style.letterSpacing || null,
        textTransform: style.textTransform || null,
      });
    }
    return output;
  }

  function collectCssVariables() {
    const names = new Set();
    for (const sheet of Array.from(document.styleSheets)) {
      let rules;
      try {
        rules = sheet.cssRules;
      } catch (error) {
        continue;
      }
      for (const rule of Array.from(rules)) {
        if (!rule.style) continue;
        for (const property of Array.from(rule.style)) {
          if (property.startsWith("--")) names.add(property);
        }
      }
    }
    for (const property of Array.from(document.documentElement.style)) {
      if (property.startsWith("--")) names.add(property);
    }
    const rootStyle = getComputedStyle(document.documentElement);
    const variables = {};
    for (const name of names) {
      const value = rootStyle.getPropertyValue(name).trim();
      if (value) variables[name] = value;
    }
    return variables;
  }

  function collectFonts() {
    if (!document.fonts) return [];
    return Array.from(document.fonts).map((font) => ({
      family: font.family,
      weight: font.weight,
      status: font.status,
    }));
  }

  const samples = [];
  let sampled = 0;
  let truncated = false;
  for (const el of document.querySelectorAll("*")) {
    const style = getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    if (!isVisible(style, rect)) continue;
    if (sampled >= MAX_ELEMENTS) {
      truncated = true;
      continue;
    }
    samples.push(styleSample(el, style, rect));
    sampled += 1;
  }

  return {
    samples: samples,
    buttons: collectForSelector(
      'button, [role="button"], input[type="submit"], a.btn, a[class*="btn"]',
      MAX_BUTTONS
    ),
    links: collectForSelector("a", MAX_LINKS),
    headings: {
      h1: collectHeadings("h1"),
      h2: collectHeadings("h2"),
      h3: collectHeadings("h3"),
    },
    cssVariables: collectCssVariables(),
    fonts: collectFonts(),
    sampledElements: sampled,
    truncatedSampling: truncated,
  };
}
