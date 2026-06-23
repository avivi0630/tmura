// Tmura - Settings page script

const i18n = {
    he: {
        headerTitle: 'תְּמוּרָה',
        headerSub: 'הגדרות תוסף',
        langTitle: 'שפה',
        langLabel: 'שפת ממשק:',
        modeTitle: 'מצב פעולה',
        modeLabel: 'פעולה באתרים:',
        modeAllOpt: 'כל האתרים',
        modeGmailOpt: 'רק Gmail',
        videoTitle: 'וידאו',
        videoLabel: 'תמיכה בוידאו:',
        saveBtn: 'שמור הגדרות',
        saved: 'ההגדרות נשמרו בהצלחה!',
    },
    yi: {
        headerTitle: 'תְּמוּרָה',
        headerSub: 'עקסטענשאַן אײַנשטעלונגען',
        langTitle: 'שפּראַך',
        langLabel: 'שפּראַך:',
        modeTitle: 'אַרבעט מאָדוס',
        modeLabel: 'אַרבעט אויף וועבזייטלעך:',
        modeAllOpt: 'אַלע וועבזייטלעך',
        modeGmailOpt: 'נאָר Gmail',
        videoTitle: 'ווידעא',
        videoLabel: 'ווידעא שטיצע:',
        saveBtn: 'שפּאַר אײַנשטעלונגען',
        saved: 'אײַנשטעלונגען געהיטן!',
    },
    en: {
        headerTitle: 'Tmura',
        headerSub: 'Extension Settings',
        langTitle: 'Language',
        langLabel: 'Interface language:',
        modeTitle: 'Operation Mode',
        modeLabel: 'Activate on:',
        modeAllOpt: 'All websites',
        modeGmailOpt: 'Gmail only',
        videoTitle: 'Video',
        videoLabel: 'Video support:',
        saveBtn: 'Save Settings',
        saved: 'Settings saved successfully!',
    }
};

function applyLang(lang) {
    const t = i18n[lang] || i18n.he;
    const isRTL = lang === 'he' || lang === 'yi';
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;

    document.getElementById('headerTitle').textContent = t.headerTitle;
    document.getElementById('headerSub').textContent = t.headerSub;
    document.getElementById('langTitle').textContent = t.langTitle;
    document.getElementById('langLabel').textContent = t.langLabel;
    document.getElementById('modeTitle').textContent = t.modeTitle;
    document.getElementById('modeLabel').textContent = t.modeLabel;
    document.getElementById('modeAllOpt').textContent = t.modeAllOpt;
    document.getElementById('modeGmailOpt').textContent = t.modeGmailOpt;
    document.getElementById('videoTitle').textContent = t.videoTitle;
    document.getElementById('videoLabel').textContent = t.videoLabel;
    document.getElementById('saveBtn').textContent = t.saveBtn;
}

chrome.runtime.sendMessage({ action: 'getSettings' }, (response) => {
    if (response && response.success) {
        const lang = response.lang || 'he';
        document.getElementById('langSelect').value = lang;
        document.getElementById('modeSelect').value = response.mode || 'all';
        document.getElementById('videoToggle').checked = response.videoEnabled !== false;
        applyLang(lang);
    }
});

document.getElementById('langSelect').addEventListener('change', (e) => {
    applyLang(e.target.value);
});

document.getElementById('saveBtn').addEventListener('click', () => {
    const lang = document.getElementById('langSelect').value;
    const mode = document.getElementById('modeSelect').value;
    const videoEnabled = document.getElementById('videoToggle').checked;

    chrome.runtime.sendMessage({
        action: 'saveSettings',
        lang: lang,
        mode: mode,
        videoEnabled: videoEnabled
    }, (response) => {
        const t = i18n[lang] || i18n.he;
        const status = document.getElementById('statusMsg');
        if (response && response.success) {
            status.textContent = t.saved;
            status.style.color = '#34c759';
        } else {
            status.textContent = 'Error';
            status.style.color = '#ff3b30';
        }
        setTimeout(() => { status.textContent = ''; }, 3000);
    });
});
