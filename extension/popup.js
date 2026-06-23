// Tmura - Popup script v3.0

const i18n = {
    he: {
        title: 'תְּמוּרָה',
        subtitle: 'כיווץ והמרת קבצים חכמה',
        info: 'גרור תמונות ווידאו לכל דף ברשת',
        testHost: 'בדוק חיבור לתוכנה',
        checking: 'בודק חיבור...',
        connected: 'חיבור תקין! התוכנה מגיבה.',
        notConfigured: 'שגיאה: התוכנה לא מוגדרת או לא פעילה',
        invalidResponse: 'תגובה לא תקינה מהתוכנה',
        ready: 'מוכן לשימוש',
        siteControl: 'ניהול אתר',
        disableSite: 'בטל בעבור אתר זה',
        enableSite: 'הפעל בעבור אתר זה',
        settings: 'הגדרות תוסף',
        site: 'אתר:',
    },
    yi: {
        title: 'תְּמוּרָה',
        subtitle: 'קאַמפּרעסיר און פֿאַרוואַנדל',
        info: 'שלעפּ בילדער און ווידעא צו יעדער זייטל',
        testHost: 'קאָנטראָליר פֿאַרבינדונג',
        checking: 'קאָנטראָלירט...',
        connected: 'פֿאַרבינדונג גוט!',
        notConfigured: 'טעות: פּראָגראַם נישט קאָנפֿיגורירט',
        invalidResponse: 'אומגילטיק ענטפֿער',
        ready: 'גרייט',
        siteControl: 'זייטל קאָנטראָל',
        disableSite: 'אויסשאַלטן פֿאַר דעם זייטל',
        enableSite: 'איינשאַלטן פֿאַר דעם זייטל',
        settings: 'עקסטענשאַן אײַנשטעלונגען',
        site: 'זייטל:',
    },
    en: {
        title: 'Tmura',
        subtitle: 'Smart File Compression & Conversion',
        info: 'Drag images and videos to any web page',
        testHost: 'Test Connection',
        checking: 'Checking...',
        connected: 'Connection OK! App is responding.',
        notConfigured: 'Error: App not configured or not running',
        invalidResponse: 'Invalid response from app',
        ready: 'Ready',
        siteControl: 'Site Control',
        disableSite: 'Disable on this site',
        enableSite: 'Enable on this site',
        settings: 'Extension Settings',
        site: 'Site:',
    }
};

let currentLang = 'he';

function t(key) {
    return (i18n[currentLang] || i18n.he)[key] || i18n.he[key] || key;
}

function applyLang(lang) {
    currentLang = lang;
    const isRTL = lang === 'he' || lang === 'yi';
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
    document.getElementById('popupTitle').textContent = t('title');
    document.getElementById('popupSubtitle').textContent = t('subtitle');
    document.getElementById('popupInfo').textContent = t('info');
    document.getElementById('testHost').textContent = t('testHost');
    document.getElementById('siteControlLabel').textContent = t('siteControl');
    document.getElementById('settingsBtn').textContent = t('settings');
}

document.getElementById('testHost').onclick = () => {
    const status = document.getElementById('status');
    status.innerText = t('checking');
    status.className = 'status loading';

    chrome.runtime.sendNativeMessage(
        'com.compressor.host',
        { action: "ping" },
        (response) => {
            if (chrome.runtime.lastError) {
                status.innerText = t('notConfigured');
                status.className = 'status error';
                console.error('Connection Error:', chrome.runtime.lastError.message);
            } else if (response && response.success) {
                status.innerText = t('connected');
                status.className = 'status success';
            } else {
                status.innerText = t('invalidResponse');
                status.className = 'status error';
            }
        }
    );
};

document.getElementById('settingsBtn').onclick = () => {
    chrome.runtime.openOptionsPage();
};

chrome.runtime.sendMessage({ action: 'getSettings' }, (response) => {
    if (response && response.success) {
        applyLang(response.lang || 'he');
    }
});

chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const url = new URL(tabs[0].url);
    const domain = url.hostname;
    document.getElementById('siteInfo').innerText = `${t('site')} ${domain}`;

    chrome.storage.local.get('disabledSites', (result) => {
        const disabledSites = result.disabledSites || {};
        const btn = document.getElementById('toggleSiteBtn');

        if (disabledSites[domain]) {
            btn.innerText = t('enableSite');
            btn.className = 'success';
        } else {
            btn.innerText = t('disableSite');
            btn.className = 'danger';
        }

        btn.onclick = () => {
            disabledSites[domain] = !disabledSites[domain];
            chrome.storage.local.set({ disabledSites }, () => {
                chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'toggleSite',
                    disabled: disabledSites[domain]
                }).catch(() => {});

                if (disabledSites[domain]) {
                    btn.innerText = t('enableSite');
                    btn.className = 'success';
                } else {
                    btn.innerText = t('disableSite');
                    btn.className = 'danger';
                }
            });
        };
    });
});

document.addEventListener('DOMContentLoaded', () => {
    const status = document.getElementById('status');
    status.innerText = t('ready');
    status.className = 'status success';
});
