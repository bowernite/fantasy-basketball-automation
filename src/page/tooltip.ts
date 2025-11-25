export async function getTooltipContent(trigger: Element) {
  // Dispatch both mouseover and mouseenter to cover different event listeners
  trigger.dispatchEvent(
    new MouseEvent("mouseover", {
      bubbles: true,
      cancelable: true,
      view: window,
    })
  );
  trigger.dispatchEvent(
    new MouseEvent("mouseenter", {
      bubbles: false,
      cancelable: true,
      view: window,
    })
  );

  let tooltip: Element | null | undefined;
  let tooltipContent: string | null | undefined;

  // Poll for tooltip to appear (up to 1 second)
  // Optimized: check every 10ms for faster response
  for (let i = 0; i < 100; i++) {
    // Check in parent element as originally implemented
    tooltip = trigger.parentElement?.querySelector(".tooltip");

    // Also check next sibling just in case (common pattern)
    if (!tooltip) {
      const nextSibling = trigger.nextElementSibling;
      if (nextSibling?.classList.contains("tooltip")) {
        tooltip = nextSibling;
      }
    }

    if (tooltip && tooltip.textContent?.trim()) {
      tooltipContent = tooltip.textContent;
      break;
    }

    // Wait a bit before next check
    await new Promise((resolve) => setTimeout(resolve, 10));
  }

  // Cleanup events
  trigger.dispatchEvent(
    new MouseEvent("mouseout", {
      bubbles: true,
      cancelable: true,
      view: window,
    })
  );
  trigger.dispatchEvent(
    new MouseEvent("mouseleave", {
      bubbles: false,
      cancelable: true,
      view: window,
    })
  );

  return {
    fullString: tooltipContent,
    element: tooltip,
  };
}
