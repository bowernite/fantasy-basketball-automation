export type TooltipData = Map<string, string>;
let _tooltipData: TooltipData | undefined;

export function getTooltipPageData(): TooltipData {
  if (_tooltipData) return _tooltipData;

  const scriptEl = document.getElementById("page-data");
  if (!scriptEl || !scriptEl.textContent) {
    console.warn("Could not find #page-data script element");
    return new Map();
  }

  const content = scriptEl.textContent;
  // Look for window.pageData = {...};
  const match = content.match(/window\.pageData\s*=\s*(\{.*?\});/s);
  if (!match) {
    console.warn("Could not extract JSON from page-data script");
    return new Map();
  }

  try {
    const pageData = JSON.parse(match[1]);
    _tooltipData = new Map();

    if (Array.isArray(pageData.tooltips)) {
      for (const tooltip of pageData.tooltips) {
        if (
          Array.isArray(tooltip.ids) &&
          typeof tooltip.contents === "string"
        ) {
          for (const id of tooltip.ids) {
            _tooltipData.set(id, tooltip.contents);
          }
        }
      }
    }
    return _tooltipData;
  } catch (e) {
    console.error("Failed to parse page-data JSON", e);
    return new Map();
  }
}

export function getTooltipContentFromPageData(trigger: Element) {
  const id = trigger.id;
  if (!id) return undefined;

  const map = getTooltipPageData();
  const content = map.get(id);

  if (!content) return undefined;

  return {
    fullString: content.replace(/<[^>]*>?/gm, ""),
    htmlString: content,
  };
}

export function getTooltipContentFromMapText(trigger: Element) {
  const id = trigger.id;

  let targetId = id;
  if (!targetId && trigger.tagName !== "A") {
    const anchor = trigger.querySelector("a");
    if (anchor && anchor.id) targetId = anchor.id;
  }

  if (!targetId) return undefined;

  const map = getTooltipPageData();
  const contentHTML = map.get(targetId);

  if (!contentHTML) return undefined;

  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = contentHTML;

  return {
    fullString: tempDiv.textContent || undefined,
    element: tempDiv,
  };
}

