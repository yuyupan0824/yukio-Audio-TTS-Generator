let lastRightClickedElement = null;

// 右クリックした要素を記録
document.addEventListener('contextmenu', function(event) {
    lastRightClickedElement = event.target;
}, true);

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getPageInfo") {
        let url = window.location.href;
        let title = document.title;

        // 右クリックからの呼び出しの場合
        if (request.trigger === "contextMenu" && lastRightClickedElement) {
            let foundUrl = extractPostUrl(lastRightClickedElement);
            if (foundUrl) {
                url = foundUrl;
            }
        }
        
        sendResponse({ url: url, title: title });
    }
});

// クリックされた要素の周辺から投稿のURLを抽出する
function extractPostUrl(element) {
    let current = element;

    // 各SNSの個別投稿URLに含まれる特徴的な文字列
    const urlPatterns = [
        '/status/',     // X (Twitter)
        '/post/',       // Threads
        '/p/',          // Instagram
        '/reel/',       // Instagram Reels
        '/watch?v=',    // YouTube
        '/shorts/',     // YouTube Shorts
        '/video/',      // TikTok, Douyin
        '/explore/'     // Xiaohongshu (Rednote)
    ];

    function isPostUrl(href) {
        if (!href) return false;
        return urlPatterns.some(pattern => href.includes(pattern));
    }

    // 1. 自身が投稿リンクそのもの、または直近のリンクかチェック
    let closestA = current.closest('a');
    if (closestA && isPostUrl(closestA.href)) {
        return closestA.href;
    }

    // 2. X (Twitter) 等の <article> タグを探してその中のリンクを取る
    let article = current.closest('article');
    if (article) {
        let timeLink = article.querySelector('a[href*="/status/"]');
        if (timeLink) return timeLink.href;
    }

    // 3. 少しだけ親を遡って投稿のリンクを探す (最大10階層まで)
    current = element;
    for (let i = 0; i < 10; i++) {
        if (!current) break;
        // 親要素内に個別投稿を示すリンクがあるか探す
        let links = Array.from(current.querySelectorAll('a')).filter(a => isPostUrl(a.href));
        if (links.length > 0) {
            return links[0].href;
        }
        current = current.parentElement;
    }

    // 4. それでも見つからなければ、直近の適当なリンクを返す（何もなければnull）
    if (closestA && closestA.href) {
        return closestA.href;
    }

    return null;
}
