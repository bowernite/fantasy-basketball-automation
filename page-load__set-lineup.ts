import { saveLineup } from "./src/page/page-interaction";

const style = document.createElement("style");
style.textContent = `
  .save-lineup-button {
    position: fixed;
    top: 6px;
    right: 210px;
    padding: 2px;
    background: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: bold;
    z-index: 9999;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    background-image: linear-gradient(45deg, #FF6B6B, #4ECDC4);
    transition: all 0.2s ease-in-out;
  }

  .save-lineup-button:hover {
    transform: scale(1.05);
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
  }

  .save-lineup-button__inner {
    background: white;
    padding: 8px 18px;
    border-radius: 6px;
  }

  .save-lineup-button__inner:hover {
    background: #f5f5f5;
  }
`;
document.head.appendChild(style);

const button = document.createElement("button");
button.className = "save-lineup-button";

const innerButton = document.createElement("div");
innerButton.className = "save-lineup-button__inner";
innerButton.textContent = "Save Lineup";

button.appendChild(innerButton);
document.body.appendChild(button);

button.addEventListener("click", () => {
  saveLineup();
});
