// background.js - Service Worker for Tmura extension v3.0

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (!request || !request.action) {
        sendResponse({ success: false, error: 'Invalid request' });
        return false;
    }

    if (request.action === 'compress') {
        if (!request.fileBase64 || !request.quality) {
            sendResponse({ success: false, error: 'Missing compression parameters' });
            return true;
        }

        chrome.runtime.sendNativeMessage(
            'com.compressor.host',
            {
                action: 'compress',
                fileBase64: request.fileBase64,
                quality: request.quality,
                mediaType: request.mediaType || 'image',
                format: request.format || ''
            },
            (response) => {
                if (chrome.runtime.lastError) {
                    console.error('[Tmura] Native Host Error:', chrome.runtime.lastError.message);
                    sendResponse({
                        success: false,
                        error: chrome.runtime.lastError.message
                    });
                } else if (!response) {
                    console.warn('[Tmura] No response from Native Host');
                    sendResponse({
                        success: false,
                        error: 'No response from Native Host'
                    });
                } else {
                    sendResponse(response);
                }
            }
        );

        return true;
    }

    if (request.action === 'ping') {
        chrome.runtime.sendNativeMessage(
            'com.compressor.host',
            { action: 'ping' },
            (response) => {
                if (chrome.runtime.lastError) {
                    sendResponse({
                        success: false,
                        error: chrome.runtime.lastError.message
                    });
                } else {
                    sendResponse(response);
                }
            }
        );
        return true;
    }

    if (request.action === 'getSettings') {
        chrome.storage.local.get(['tmura_lang', 'tmura_mode', 'tmura_video'], (result) => {
            sendResponse({
                success: true,
                lang: result.tmura_lang || 'he',
                mode: result.tmura_mode || 'all',
                videoEnabled: result.tmura_video !== false
            });
        });
        return true;
    }

    if (request.action === 'saveSettings') {
        const updates = {};
        if (request.lang) updates.tmura_lang = request.lang;
        if (request.mode) updates.tmura_mode = request.mode;
        if (request.videoEnabled !== undefined) updates.tmura_video = request.videoEnabled;
        chrome.storage.local.set(updates, () => {
            chrome.tabs.query({}, (tabs) => {
                tabs.forEach(tab => {
                    chrome.tabs.sendMessage(tab.id, { action: 'settingsUpdated' }).catch(() => {});
                });
            });
            sendResponse({ success: true });
        });
        return true;
    }

    sendResponse({ success: false, error: 'Unknown action' });
    return false;
});

chrome.runtime.onConnect.addListener((port) => {
    port.onDisconnect.addListener(() => {
        if (chrome.runtime.lastError) {
            console.error('[Tmura] Connection Error:', chrome.runtime.lastError.message);
        }
    });
});
