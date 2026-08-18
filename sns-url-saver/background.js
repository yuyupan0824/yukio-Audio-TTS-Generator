chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "saveUrlContextMenu",
    title: "このURLをスプレッドシートに保存",
    contexts: ["page", "link", "selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "saveUrlContextMenu") {
    // Content scriptに問い合わせて正確なURLを取得
    chrome.tabs.sendMessage(tab.id, { action: "getPageInfo", trigger: "contextMenu" }, (response) => {
      // Content scriptが読み込まれていない場合はフォールバック
      if (chrome.runtime.lastError || !response) {
        const fallbackUrl = info.linkUrl || info.pageUrl || tab.url;
        saveData(fallbackUrl, tab.title || "");
      } else {
        saveData(response.url, response.title);
      }
    });
  }
});

chrome.commands.onCommand.addListener((command, tab) => {
  if (command === "save-url") {
    chrome.tabs.sendMessage(tab.id, { action: "getPageInfo", trigger: "shortcut" }, (response) => {
      if (chrome.runtime.lastError || !response) {
        saveData(tab.url, tab.title || "");
      } else {
        saveData(response.url, response.title);
      }
    });
  }
});

const dummyIconUrl = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';

function saveData(url, title) {
  chrome.storage.local.get(['gasUrl', 'spreadsheetUrl', 'sheetName', 'assignee'], (result) => {
    if (!result.gasUrl || !result.spreadsheetUrl || !result.sheetName) {
      showNotification("設定エラー", "拡張機能のアイコンからGAS URL等を設定してください。");
      return;
    }

    const payload = {
      spreadsheetUrl: result.spreadsheetUrl,
      sheetName: result.sheetName,
      url: url,
      title: title,
      assignee: result.assignee || ""
    };

    fetch(result.gasUrl, {
      method: 'POST',
      mode: 'no-cors',
      body: JSON.stringify(payload)
    })
    .then(() => {
      showNotification("送信完了", "URLをスプレッドシートへ送信しました。");
    })
    .catch(error => {
      console.error('Fetch Error:', error);
      showNotification("通信エラー", "データの送信に失敗しました。");
    });
  });
}

function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: dummyIconUrl,
    title: title,
    message: message
  });
}
