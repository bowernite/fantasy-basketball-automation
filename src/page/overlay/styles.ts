import { LINEUP_ACTIONS_CSS } from "./lineup-actions";
import { NOTICE_CSS } from "./notice";
import { ROW_STATES_CSS } from "./row-states";
import { SCORE_RAIL_CSS } from "./score-rail";
import { STATUS_TAG_CSS } from "./status-tag";

// Light theme only; Fleaflicker's dark theme (`body.slate`) can override these vars
const TOKENS_CSS = `
  :root {
    --ffx-ink: #26313D;
    --ffx-muted: #5F6A77;
    --ffx-track: #E8EDF3;
    --ffx-band40: #00386E;
    --ffx-band30: #16558C;
    --ffx-band20: #346FA9;
    --ffx-band-sit: #4F8AC6;
    --ffx-orange: #D55E00;
    --ffx-orange-text: #A84A00;
    --ffx-row-started: #EAF1F9;
    --ffx-row-risk: #FCEEE3;
    --ffx-focus: #337ab7;
    --ffx-radius-sm: 2px;
    --ffx-radius: 3px;
    --ffx-ease: cubic-bezier(0.23, 1, 0.32, 1);
    --ffx-duration: 200ms;
    --ffx-shadow-pinned: 0 1px 2px rgba(0, 56, 110, 0.12), 0 4px 12px rgba(0, 56, 110, 0.14);
  }
  @media (prefers-reduced-motion: reduce) {
    :root { --ffx-duration: 0ms; }
  }
`;

export function injectOverlayStyles() {
  if (document.head.querySelector("style[data-ffx]")) return;

  const style = document.createElement("style");
  style.setAttribute("data-ffx", "");
  style.textContent = [TOKENS_CSS, SCORE_RAIL_CSS, ROW_STATES_CSS, STATUS_TAG_CSS, LINEUP_ACTIONS_CSS, NOTICE_CSS].join("\n");
  document.head.appendChild(style);
}
