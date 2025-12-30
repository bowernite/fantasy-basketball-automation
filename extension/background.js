function runScript(tab) {
  if (!tab.id) return;

  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ["dist/main.js"],
  });
}

chrome.action.onClicked.addListener((tab) => {
  runScript(tab);
});

chrome.commands.onCommand.addListener((command) => {
  if (command === "run-script") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]) {
        runScript(tabs[0]);
      }
    });
  } else if (command === "save-lineup") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0] && tabs[0].id) {
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          func: () => {
            if (typeof window.saveLineup === "function") {
              window.saveLineup();
            }
          },
        });
      }
    });
  } else if (command === "previous-day") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0] && tabs[0].id) {
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          func: () => {
            if (typeof window.goToPreviousDay === "function") {
              window.goToPreviousDay();
            }
          },
        });
      }
    });
  } else if (command === "next-day") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0] && tabs[0].id) {
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          func: () => {
            if (typeof window.goToNextDay === "function") {
              window.goToNextDay();
            }
          },
        });
      }
    });
  }
});
