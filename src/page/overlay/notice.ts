// Host Bootstrap alert colors, with the overlay's radius and spacing
export const NOTICE_CSS = `
  .ffx-notice {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
    padding: 8px 12px;
    border-radius: var(--ffx-radius);
  }
  .ffx-notice__message {
    flex: 1;
  }
  .ffx-notice .close {
    order: 1;
    float: none;
  }
  .ffx-notice .close::before {
    content: "\\00d7";
  }
`;

export type NoticeKind = "info" | "warning" | "error";

export type Notice = {
  kind: NoticeKind;
  message: string;
  action?: { label: string; onClick: () => void };
};

const ALERT_CLASS: Record<NoticeKind, string> = {
  info: "alert-info",
  warning: "alert-warning",
  error: "alert-danger",
};

// One notice at a time, in Fleaflicker's message box above the roster
export function showNotice({ kind, message, action }: Notice) {
  document.querySelector(".ffx-notice")?.remove();

  const notice = document.createElement("div");
  notice.className = `alert ${ALERT_CLASS[kind]} ffx-notice`;
  notice.setAttribute("role", kind === "info" ? "status" : "alert");

  const text = document.createElement("span");
  text.className = "ffx-notice__message";
  text.textContent = message;
  notice.appendChild(text);

  if (action) {
    const actionButton = document.createElement("button");
    actionButton.type = "button";
    actionButton.className = "btn btn-default btn-xs";
    actionButton.textContent = action.label;
    actionButton.addEventListener("click", action.onClick);
    notice.appendChild(actionButton);
  }

  notice.insertAdjacentHTML(
    "beforeend",
    '<button type="button" class="close" aria-label="Dismiss"></button>',
  );
  notice.querySelector(".close")!.addEventListener("click", () => notice.remove());

  const statusBox = document.getElementById("statusBox");
  const rosterForm = document.querySelector("form[method='post']");
  if (statusBox) statusBox.appendChild(notice);
  else if (rosterForm) rosterForm.insertAdjacentElement("beforebegin", notice);
  else document.getElementById("body-center-main")!.insertAdjacentElement("afterbegin", notice);
}
