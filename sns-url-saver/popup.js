document.addEventListener('DOMContentLoaded', () => {
  // 設定の読み込み
  chrome.storage.local.get(['gasUrl', 'spreadsheetUrl', 'sheetName', 'assignee'], (result) => {
    if (result.gasUrl) document.getElementById('gasUrl').value = result.gasUrl;
    if (result.spreadsheetUrl) document.getElementById('spreadsheetUrl').value = result.spreadsheetUrl;
    if (result.assignee) document.getElementById('assignee').value = result.assignee;
    
    // URLが設定済みならタブを自動読み込み
    if (result.gasUrl && result.spreadsheetUrl) {
      loadSheets(result.gasUrl, result.spreadsheetUrl, result.sheetName);
    }
  });

  // タブ読み込みボタン
  document.getElementById('loadSheetsBtn').addEventListener('click', () => {
    const gasUrl = document.getElementById('gasUrl').value.trim();
    const spreadsheetUrl = document.getElementById('spreadsheetUrl').value.trim();
    if (!gasUrl || !spreadsheetUrl) {
      showStatus('GAS URLとスプレッドシートURLを入力してください', true);
      return;
    }
    loadSheets(gasUrl, spreadsheetUrl);
  });

  // 設定の保存処理
  document.getElementById('saveBtn').addEventListener('click', () => {
    const gasUrl = document.getElementById('gasUrl').value.trim();
    const spreadsheetUrl = document.getElementById('spreadsheetUrl').value.trim();
    const sheetName = document.getElementById('sheetName').value;
    const assignee = document.getElementById('assignee').value.trim();

    chrome.storage.local.set({
      gasUrl, spreadsheetUrl, sheetName, assignee
    }, () => {
      showStatus('設定を保存しました。');
    });
  });
});

function loadSheets(gasUrl, spreadsheetUrl, selectedSheet = null) {
  const select = document.getElementById('sheetName');
  select.innerHTML = '<option value="">読み込み中...</option>';
  
  // GASにタブ一覧取得のリクエストを送る
  const fetchUrl = `${gasUrl}?action=getSheets&url=${encodeURIComponent(spreadsheetUrl)}`;
  
  fetch(fetchUrl)
    .then(response => response.json())
    .then(data => {
      if (data.status === 'success') {
        select.innerHTML = '';
        if (data.sheets.length === 0) {
          select.innerHTML = '<option value="">タブが見つかりません</option>';
        } else {
          data.sheets.forEach(sheet => {
            const option = document.createElement('option');
            option.value = sheet;
            option.textContent = sheet;
            if (sheet === selectedSheet) {
              option.selected = true;
            }
            select.appendChild(option);
          });
        }
        showStatus('タブを読み込みました');
      } else {
        select.innerHTML = '<option value="">エラーが発生しました</option>';
        showStatus('読み込み失敗: ' + data.message, true);
      }
    })
    .catch(err => {
      console.error(err);
      select.innerHTML = '<option value="">エラーが発生しました</option>';
      showStatus('通信エラー。GASのURLを確認してください。', true);
    });
}

function showStatus(message, isError = false) {
  const status = document.getElementById('status');
  status.textContent = message;
  status.style.color = isError ? 'red' : '#0f9d58';
  setTimeout(() => { status.textContent = ''; }, 3000);
}
