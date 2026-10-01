import { saveLineup } from "../../lineup/lineup-dom-actions";
import { setLineup } from "../../lineup/set-lineup";
import { saveLineupIcon, setLineupIcon } from "../../icons/icons";

export const LINEUP_ACTIONS_CSS = "";

export function addSaveLineupButton() {
  if (!document.head.querySelector('style[data-button-styles]')) {
    const style = document.createElement("style");
    style.textContent = BUTTON_STYLES;
    style.setAttribute('data-button-styles', '');
    document.head.appendChild(style);
  }

  const button = document.createElement("button");
  button.className = "save-lineup-button";
  button.type = "button";

  const innerButton = document.createElement("div");
  innerButton.className = "save-lineup-button__inner";
  
  const iconDiv = document.createElement("div");
  iconDiv.className = "save-lineup-button__icon";
  iconDiv.innerHTML = saveLineupIcon;
  
  const textSpan = document.createElement("span");
  textSpan.textContent = "Save Lineup";
  
  innerButton.appendChild(iconDiv);
  innerButton.appendChild(textSpan);

  button.appendChild(innerButton);
  document.body.appendChild(button);

  button.addEventListener("click", () => {
    saveLineup();
  });
}

export async function addSetLineupButton() {
  if (!document.head.querySelector('style[data-button-styles]')) {
    const style = document.createElement("style");
    style.textContent = BUTTON_STYLES;
    style.setAttribute('data-button-styles', '');
    document.head.appendChild(style);
  }

  const button = document.createElement("button");
  button.className = "set-lineup-button";
  button.type = "button";

  const innerButton = document.createElement("div");
  innerButton.className = "set-lineup-button__inner";
  
  const iconDiv = document.createElement("div");
  iconDiv.className = "set-lineup-button__icon";
  iconDiv.innerHTML = setLineupIcon;
  
  const textSpan = document.createElement("span");
  textSpan.textContent = "Set Lineup";
  
  innerButton.appendChild(iconDiv);
  innerButton.appendChild(textSpan);

  button.appendChild(innerButton);
  document.body.appendChild(button);

  button.addEventListener("click", async () => {
    try {
      await setLineup();
    } catch (error) {
      console.error("Error setting lineup:", error);
      alert(`Error setting lineup: ${error}`);
    }
  });
}

const BUTTON_STYLES = `
  .save-lineup-button,
  .set-lineup-button {
    position: fixed;
    top: 6px;
    padding: 2px;
    background: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
    z-index: 9999;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    transition: all 0.2s ease-in-out;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .save-lineup-button {
    right: 210px;
    background-image: linear-gradient(45deg, #4ECDC4, #44A08D);
  }

  .set-lineup-button {
    right: 385px;
    background-image: linear-gradient(45deg, #F7971E, #FFD200);
  }

  .save-lineup-button:hover,
  .set-lineup-button:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
  }

  .save-lineup-button__inner {
    background: white;
    padding: 8px 18px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #2C5F5A;
  }

  .set-lineup-button__inner {
    background: white;
    padding: 8px 18px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
    color: #B8731A;
  }

  .save-lineup-button__inner:hover {
    background: #f0f9f7;
  }

  .set-lineup-button__inner:hover {
    background: #fff8f0;
  }

  .save-lineup-button__icon,
  .set-lineup-button__icon {
    width: 20px;
    height: 20px;
    flex-shrink: 0;
  }
`;
