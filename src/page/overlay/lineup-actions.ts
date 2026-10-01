import { saveLineup } from "../../lineup/lineup-dom-actions";
import { setLineup } from "../../lineup/set-lineup";
import { saveLineupIcon, setLineupIcon, spinnerIcon } from "../../icons/icons";
import { showNotice } from "./notice";

export const LINEUP_ACTIONS_CSS = `
  .ffx-actions .btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
  }
  .ffx-actions svg {
    width: 16px;
    height: 16px;
    flex: none;
  }
  @media (prefers-reduced-motion: no-preference) {
    .ffx-spinner {
      animation: ffx-spin 800ms linear infinite;
    }
  }
  @keyframes ffx-spin {
    to {
      transform: rotate(360deg);
    }
  }
`;

export function addLineupActions() {
  document.querySelector(".ffx-actions")?.remove();

  const group = document.createElement("div");
  group.className = "btn-group ffx-actions";
  group.append(
    actionButton({ label: "Set lineup", icon: setLineupIcon, className: "btn btn-primary ffx-set-lineup", onClick: runSetLineup }),
    actionButton({ label: "Save lineup", icon: saveLineupIcon, className: "btn btn-default ffx-save-lineup", onClick: runSaveLineup }),
  );

  const toolbar = document.querySelector("#body-top .button-bar .btn-toolbar");
  (toolbar ?? document.getElementById("statusBox")!.parentElement!).prepend(group);
}

// Also run by the Set lineup shortcut, so it works without the buttons on the page
export async function runSetLineup() {
  const setButton = document.querySelector<HTMLButtonElement>(".ffx-set-lineup");
  const saveButton = document.querySelector<HTMLButtonElement>(".ffx-save-lineup");
  const restore = showBusy(setButton, "Setting lineup…");
  try {
    await setLineup();
    showNotice({ kind: "info", message: "Lineup set. Review the highlighted rows, then save." });
    setButton?.classList.replace("btn-primary", "btn-default");
    saveButton?.classList.replace("btn-default", "btn-primary");
  } catch (error) {
    console.error("Error setting lineup:", error);
    showNotice({
      kind: "error",
      message: `Couldn't set the lineup; nothing changed. ${errorMessage(error)}`,
      action: { label: "Retry", onClick: runSetLineup },
    });
  } finally {
    restore();
  }
}

// Stays busy on success: the form submit reloads the page
export function runSaveLineup() {
  const restore = showBusy(document.querySelector<HTMLButtonElement>(".ffx-save-lineup"), "Saving…");
  try {
    saveLineup();
  } catch (error) {
    console.error("Error saving lineup:", error);
    restore();
    showNotice({ kind: "error", message: `Couldn't save the lineup. ${errorMessage(error)}` });
  }
}

function actionButton({ label, icon, className, onClick }: { label: string; icon: string; className: string; onClick: () => void }) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.innerHTML = buttonContent(icon, label);
  button.addEventListener("click", onClick);
  return button;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function buttonContent(icon: string, label: string) {
  return `${icon}<span class="ffx-actions__label">${label}</span>`;
}

// Returns a function that puts the button back as it was
function showBusy(button: HTMLButtonElement | null, label: string) {
  if (!button) return () => {};

  const idleContent = button.innerHTML;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  button.innerHTML = buttonContent(spinnerIcon.replace("<svg ", '<svg class="ffx-spinner" '), label);
  return () => {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.innerHTML = idleContent;
  };
}
