// Tmura - Content Script v3.0
(function() {
    let pendingFiles = [];
    let compressionInProgress = false;
    let isDisabledOnSite = false;
    let sourceMode = null;
    let capturedFileInput = null;
    let capturedDropTarget = null;
    let capturedDropXY = null;
    let settings = { lang: 'he', mode: 'all', videoEnabled: true };

    const currentDomain = window.location.hostname;

    function loadSettings(cb) {
        chrome.storage.local.get(['tmura_lang', 'tmura_mode', 'tmura_video', 'disabledSites'], (result) => {
            settings.lang = result.tmura_lang || 'he';
            settings.mode = result.tmura_mode || 'all';
            settings.videoEnabled = result.tmura_video !== false;
            isDisabledOnSite = !!(result.disabledSites || {})[currentDomain];
            if (cb) cb();
        });
    }

    loadSettings();

    // Returns true when Tmura should be active on the current page
    function isTmuraActiveOnPage() {
        if (isDisabledOnSite) return false;
        if (settings.mode === 'gmail') {
            return /(^|\.)mail\.google\.com$/.test(currentDomain);
        }
        return true;
    }

    const i18n = {
        he: {
            title: 'תְּמוּרָה',
            subtitle: 'כיווץ והמרת קבצים חכמה',
            compress_btn: 'כיווץ והעתקה ללוח',
            convert_save_btn: 'המר ושמור בתיקייה',
            cancel_btn: 'המשך עם הקובץ המקורי',
            quality_high: 'איכות גבוהה (70%)',
            quality_medium: 'בינונית - מומלץ (35%)',
            quality_low: 'נמוכה - חסכון מרבי (15%)',
            processing: 'מעבד...',
            done: 'הכל הועתק! Ctrl+V',
            done_saved: 'הקבצים נשמרו בתיקייה',
            error_process: 'לא היתה אפשרות לעבד את הקבצים',
            error_comm: 'שגיאה בתקשורת עם התוכנה',
            progress: 'מעבד {current} מתוך {total}...',
            detected_images: 'זוהו {count} תמונות לכיווץ',
            detected_videos: 'זוהו {count} סרטונים להמרה',
            detected_mixed: 'זוהו {count} קבצים להמרה',
            video_detected: 'זוהו סרטונים - יומרו ויישמרו בתיקייה',
            format_video: 'פורמט וידאו:',
        },
        yi: {
            title: 'תְּמוּרָה',
            subtitle: 'קאַמפּרעסיר און פֿאַרוואַנדל טעקעס',
            compress_btn: 'קאַמפּרעסיר און קאָפּיר',
            convert_save_btn: 'פֿאַרוואַנדל און שפּאַר',
            cancel_btn: 'ווייטער מיט אָריגינעל',
            quality_high: 'הויך קוואַליטעט (70%)',
            quality_medium: 'מיטל - רעקאַמענדירט (35%)',
            quality_low: 'נידעריק - מאַקס שפּאָר (15%)',
            processing: 'פּראָצעסירט...',
            done: 'אַלע קאָפּירט! Ctrl+V',
            done_saved: 'טעקעס געהיטן',
            error_process: 'נישט מעגלעך צו פּראָצעסירן',
            error_comm: 'טעות קאָמוניקאַציע',
            progress: 'פּראָצעסירט {current} פֿון {total}...',
            detected_images: 'געפֿונען {count} בילדער',
            detected_videos: 'געפֿונען {count} ווידעאס',
            detected_mixed: 'געפֿונען {count} טעקעס',
            video_detected: 'ווידעא געפֿונען - וועט געהיטן ווערן',
            format_video: 'ווידעא פֿאָרמאַט:',
        },
        en: {
            title: 'Tmura',
            subtitle: 'Smart File Compression & Conversion',
            compress_btn: 'Compress & Copy to Clipboard',
            convert_save_btn: 'Convert & Save to Folder',
            cancel_btn: 'Continue with original file',
            quality_high: 'High quality (70%)',
            quality_medium: 'Medium - Recommended (35%)',
            quality_low: 'Low - Max savings (15%)',
            processing: 'Processing...',
            done: 'All copied! Ctrl+V',
            done_saved: 'Files saved to folder',
            error_process: 'Could not process the files',
            error_comm: 'Communication error with app',
            progress: 'Processing {current} of {total}...',
            detected_images: 'Detected {count} images to compress',
            detected_videos: 'Detected {count} videos to convert',
            detected_mixed: 'Detected {count} files to process',
            video_detected: 'Videos detected - will be converted and saved',
            format_video: 'Video format:',
        }
    };

    function t(key, vars) {
        let text = (i18n[settings.lang] || i18n.he)[key] || i18n.he[key] || key;
        if (vars) {
            Object.keys(vars).forEach(k => {
                text = text.replace(`{${k}}`, vars[k]);
            });
        }
        return text;
    }

    const isRTL = settings.lang === 'he' || settings.lang === 'yi';
    const dir = isRTL ? 'rtl' : 'ltr';

    const style = document.createElement('style');
    style.textContent = `
        #tmura-modal-overlay {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background: rgba(0,0,0,0.4); backdrop-filter: blur(4px);
            display: none; align-items: center; justify-content: center; z-index: 999999999;
            font-family: 'Segoe UI', system-ui, sans-serif; direction: ${dir};
        }
        #tmura-modal-overlay.active { display: flex; animation: tmuraFadeIn 0.3s ease; }
        .tmura-popup {
            background: white; width: 380px; border-radius: 20px; padding: 28px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.2); text-align: center;
            animation: tmuraSlideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .tmura-title {
            font-size: 20px; font-weight: 800; color: #1d1d1f; margin-bottom: 8px; display: block;
        }
        .tmura-subtitle {
            font-size: 11px; color: #86868b; margin-bottom: 12px; display: block;
        }
        .tmura-file-info {
            background: #f5f5f7; padding: 10px 12px; border-radius: 12px; margin-bottom: 16px;
            font-size: 14px; color: #1d1d1f; max-height: 80px; overflow-y: auto;
            direction: ltr; text-align: center;
        }
        .tmura-select {
            width: 100%; padding: 10px 14px; border-radius: 10px; border: 1.5px solid #d2d2d7;
            margin-bottom: 12px; font-size: 15px; box-sizing: border-box;
            font-family: 'Segoe UI', system-ui, sans-serif; direction: ${dir};
            appearance: none; -webkit-appearance: none;
            background: white url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%2386868b' stroke-width='2' fill='none'/%3E%3C/svg%3E") no-repeat ${isRTL ? 'left' : 'right'} 14px center;
        }
        .tmura-btn-primary {
            width: 100%; padding: 12px; background: #0071e3; color: white; border: none;
            border-radius: 12px; font-size: 15px; font-weight: 600; cursor: pointer;
            box-sizing: border-box; transition: all 0.2s ease;
            font-family: 'Segoe UI', system-ui, sans-serif; margin-bottom: 8px;
        }
        .tmura-btn-primary:hover { background: #0059c4; }
        .tmura-btn-primary:disabled { background: #c7c7cc; cursor: not-allowed; }
        .tmura-btn-secondary {
            background: none; border: none; color: #86868b; margin-top: 8px; cursor: pointer;
            font-size: 13px; padding: 6px; font-family: 'Segoe UI', system-ui, sans-serif;
        }
        .tmura-btn-secondary:hover { color: #0071e3; }
        .tmura-btn-save {
            width: 100%; padding: 12px; background: #34c759; color: white; border: none;
            border-radius: 12px; font-size: 15px; font-weight: 600; cursor: pointer;
            box-sizing: border-box; transition: all 0.2s ease;
            font-family: 'Segoe UI', system-ui, sans-serif; margin-bottom: 8px;
        }
        .tmura-btn-save:hover { background: #2db84d; }
        .tmura-btn-save:disabled { background: #c7c7cc; cursor: not-allowed; }
        .tmura-progress-wrap {
            width: 100%; height: 6px; background: #e5e5ea; border-radius: 3px;
            margin-bottom: 16px; overflow: hidden; display: none;
        }
        .tmura-progress-wrap.visible { display: block; }
        .tmura-progress-bar {
            height: 100%; width: 0%; background: #0071e3; border-radius: 3px;
            transition: width 0.3s ease;
        }
        .tmura-progress-label {
            font-size: 11px; color: #86868b; margin-bottom: 6px; display: none;
        }
        .tmura-progress-label.visible { display: block; }
        .tmura-video-note {
            font-size: 11px; color: #ff9500; margin-bottom: 8px; display: none;
        }
        .tmura-video-note.visible { display: block; }
        @keyframes tmuraFadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes tmuraSlideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @media (max-width: 480px) {
            .tmura-popup { width: 92%; max-width: 380px; padding: 20px; }
        }
    `;
    document.head.appendChild(style);

    const overlay = document.createElement('div');
    overlay.id = 'tmura-modal-overlay';
    overlay.innerHTML = `
        <div class="tmura-popup">
            <span class="tmura-title">${t('title')}</span>
            <span class="tmura-subtitle">${t('subtitle')}</span>
            <div class="tmura-file-info" id="tmura-info-text"></div>
            <div class="tmura-video-note" id="tmura-video-note">${t('video_detected')}</div>
            <select class="tmura-select" id="tmura-quality-val">
                <option value="high">${t('quality_high')}</option>
                <option value="medium" selected>${t('quality_medium')}</option>
                <option value="low">${t('quality_low')}</option>
            </select>
            <select class="tmura-select" id="tmura-video-format" style="display:none">
                <option value="mp4">MP4</option>
                <option value="webm">WebM</option>
                <option value="mkv">MKV</option>
            </select>
            <div class="tmura-progress-label" id="tmura-progress-label">${t('progress', {current:0,total:0})}</div>
            <div class="tmura-progress-wrap" id="tmura-progress-wrap">
                <div class="tmura-progress-bar" id="tmura-progress-bar"></div>
            </div>
            <button class="tmura-btn-primary" id="tmura-process-btn">${t('compress_btn')}</button>
            <button class="tmura-btn-save" id="tmura-save-btn">${t('convert_save_btn')}</button>
            <button class="tmura-btn-secondary" id="tmura-cancel-btn">${t('cancel_btn')}</button>
        </div>
    `;
    document.body.appendChild(overlay);

    // Drag prevention - only when Tmura is active on this page.
    // When inactive, we deliberately do NOT preventDefault, so the site's
    // native drag&drop keeps working.
    window.addEventListener('dragover', (e) => {
        if (!isTmuraActiveOnPage()) return;
        e.preventDefault(); e.stopPropagation();
    }, true);
    window.addEventListener('dragenter', (e) => {
        if (!isTmuraActiveOnPage()) return;
        e.preventDefault(); e.stopPropagation();
    }, true);
    window.addEventListener('dragleave', (e) => {
        if (!isTmuraActiveOnPage()) return;
        e.preventDefault(); e.stopPropagation();
    }, true);

    function hasVideoFiles(files) {
        return files.some(f => f.type.startsWith('video/'));
    }

    function hasImageFiles(files) {
        return files.some(f => f.type.startsWith('image/'));
    }

    window.addEventListener('drop', (e) => {
        if (!isTmuraActiveOnPage()) return;
        e.preventDefault();
        e.stopPropagation();

        const allFiles = Array.from(e.dataTransfer.files);
        const imageFiles = allFiles.filter(f => f.type.startsWith('image/'));
        const videoFiles = settings.videoEnabled ? allFiles.filter(f => f.type.startsWith('video/')) : [];
        const files = [...imageFiles, ...videoFiles];

        if (files.length > 0) {
            pendingFiles = files;
            sourceMode = 'drop';
            capturedFileInput = e.target.closest('input[type="file"]') || null;
            capturedDropTarget = e.target;
            capturedDropXY = { clientX: e.clientX, clientY: e.clientY };

            const hasVideo = hasVideoFiles(files);
            const hasImage = hasImageFiles(files);

            let text;
            if (files.length === 1) {
                text = files[0].name;
            } else if (hasVideo && !hasImage) {
                text = t('detected_videos', {count: files.length});
            } else if (hasImage && !hasVideo) {
                text = t('detected_images', {count: files.length});
            } else {
                text = t('detected_mixed', {count: files.length});
            }

            document.getElementById('tmura-info-text').innerText = text;

            const videoFormatSelect = document.getElementById('tmura-video-format');
            const videoNote = document.getElementById('tmura-video-note');
            const processBtn = document.getElementById('tmura-process-btn');
            const saveBtn = document.getElementById('tmura-save-btn');

            if (hasVideo) {
                videoFormatSelect.style.display = 'block';
                videoNote.classList.add('visible');
                processBtn.style.display = 'none';
                saveBtn.style.display = 'block';
            } else {
                videoFormatSelect.style.display = 'none';
                videoNote.classList.remove('visible');
                processBtn.style.display = 'block';
                saveBtn.style.display = 'block';
            }

            overlay.classList.add('active');
        }
    }, true);

    function updateProgress(current, total) {
        const pct = Math.round((current / total) * 100);
        document.getElementById('tmura-progress-bar').style.width = pct + '%';
        document.getElementById('tmura-progress-label').innerText = t('progress', {current, total});
    }

    document.getElementById('tmura-process-btn').onclick = async () => {
        if (compressionInProgress) return;
        const btn = document.getElementById('tmura-process-btn');
        const quality = document.getElementById('tmura-quality-val').value;
        btn.innerText = t('processing');
        btn.disabled = true;
        compressionInProgress = true;

        const imageFiles = pendingFiles.filter(f => f.type.startsWith('image/'));
        const filesToProcess = [...imageFiles];

        document.getElementById('tmura-progress-wrap').classList.add('visible');
        document.getElementById('tmura-progress-label').classList.add('visible');

        try {
            const results = [];
            const total = filesToProcess.length;
            for (let i = 0; i < total; i++) {
                updateProgress(i + 1, total);
                const base64 = await fileToBase64(filesToProcess[i]);
                const res = await sendToPython(base64, quality, 'image');
                if (res.success) results.push(res.fileBase64);
            }
            if (results.length > 0) {
                await copyToClipboard(results);
                btn.innerText = t('done');
                btn.style.background = "#34c759";
                setTimeout(() => { overlay.classList.remove('active'); resetPopup(); }, 1500);
            } else {
                alert(t('error_process'));
                resetPopup();
            }
        } catch (err) {
            alert(t('error_comm'));
            overlay.classList.remove('active');
            resetPopup();
        }
    };

    document.getElementById('tmura-save-btn').onclick = async () => {
        if (compressionInProgress) return;
        const btn = document.getElementById('tmura-save-btn');
        const quality = document.getElementById('tmura-quality-val').value;
        const videoFormat = document.getElementById('tmura-video-format').value;
        btn.innerText = t('processing');
        btn.disabled = true;
        compressionInProgress = true;

        const filesToProcess = [...pendingFiles];

        document.getElementById('tmura-progress-wrap').classList.add('visible');
        document.getElementById('tmura-progress-label').classList.add('visible');

        try {
            const total = filesToProcess.length;
            for (let i = 0; i < total; i++) {
                updateProgress(i + 1, total);
                const base64 = await fileToBase64(filesToProcess[i]);
                const mediaType = filesToProcess[i].type.startsWith('video/') ? 'video' : 'image';
                const format = mediaType === 'video' ? videoFormat : '';
                const res = await sendToPython(base64, quality, mediaType, format);
                if (!res.success) {
                    console.error('Conversion failed:', res.error);
                }
            }
            btn.innerText = t('done_saved');
            btn.style.background = "#0071e3";
            setTimeout(() => { overlay.classList.remove('active'); resetPopup(); }, 1500);
        } catch (err) {
            alert(t('error_comm'));
            overlay.classList.remove('active');
            resetPopup();
        }
    };

    function fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.onerror = () => reject(new Error('File read error'));
            reader.readAsDataURL(file);
        });
    }

    function sendToPython(base64, quality, mediaType, format) {
        return new Promise((resolve) => {
            const msg = {
                action: 'compress',
                fileBase64: base64,
                quality: quality,
                mediaType: mediaType || 'image',
                format: format || ''
            };
            chrome.runtime.sendMessage(msg, (response) => resolve(response || { success: false, error: 'No response' }));
        });
    }

    async function copyToClipboard(base64Array) {
        try {
            const htmlContent = base64Array
                .map(b64 => `<img src="data:image/jpeg;base64,${b64}" style="max-width: 100%;">`)
                .join('');
            const blobHtml = new Blob([htmlContent], { type: "text/html" });
            const clipboardData = { "text/html": blobHtml };
            if (base64Array.length === 1) {
                const pngBlob = await jpegBase64ToPngBlob(base64Array[0]);
                clipboardData["image/png"] = pngBlob;
            }
            await navigator.clipboard.write([new ClipboardItem(clipboardData)]);
        } catch (err) {
            console.error('Clipboard error:', err);
        }
    }

    async function jpegBase64ToPngBlob(base64) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                const canvas = document.createElement('canvas');
                canvas.width = img.width; canvas.height = img.height;
                canvas.getContext('2d').drawImage(img, 0, 0);
                canvas.toBlob(resolve, 'image/png');
            };
            img.onerror = () => reject(new Error('Image load error'));
            img.src = "data:image/jpeg;base64," + base64;
        });
    }

    function resetPopup() {
        const processBtn = document.getElementById('tmura-process-btn');
        const saveBtn = document.getElementById('tmura-save-btn');
        processBtn.innerText = t('compress_btn');
        processBtn.style.background = "#0071e3";
        processBtn.disabled = false;
        processBtn.style.display = 'block';
        saveBtn.innerText = t('convert_save_btn');
        saveBtn.style.background = "#34c759";
        saveBtn.disabled = false;
        saveBtn.style.display = 'block';
        document.getElementById('tmura-progress-wrap').classList.remove('visible');
        document.getElementById('tmura-progress-label').classList.remove('visible');
        document.getElementById('tmura-progress-bar').style.width = '0%';
        document.getElementById('tmura-video-format').style.display = 'none';
        document.getElementById('tmura-video-note').classList.remove('visible');
        pendingFiles = [];
        compressionInProgress = false;
    }

    function continueUploadFlow(savedFiles) {
        if (!savedFiles || savedFiles.length === 0) return;
        if (sourceMode === 'input' && capturedFileInput) {
            const dt = new DataTransfer();
            savedFiles.forEach(f => dt.items.add(f));
            capturedFileInput.files = dt.files;
            capturedFileInput.dispatchEvent(new Event('change', { bubbles: true }));
            capturedFileInput.dispatchEvent(new Event('input', { bubbles: true }));
            capturedFileInput = null;
        } else if (sourceMode === 'drop') {
            const prevDisabled = isDisabledOnSite;
            isDisabledOnSite = true;
            const target = capturedDropTarget;
            if (target) {
                const dt = new DataTransfer();
                savedFiles.forEach(f => dt.items.add(f));
                const dropEvent = new DragEvent('drop', {
                    bubbles: true, cancelable: true, dataTransfer: dt,
                    clientX: capturedDropXY?.clientX || 0, clientY: capturedDropXY?.clientY || 0
                });
                target.dispatchEvent(dropEvent);
            }
            const fileInput = (target && target.closest('input[type="file"]')) ||
                (target && target.querySelector('input[type="file"]')) ||
                document.querySelector('input[type="file"]');
            if (fileInput) {
                const dt2 = new DataTransfer();
                savedFiles.forEach(f => dt2.items.add(f));
                fileInput.files = dt2.files;
                fileInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
            isDisabledOnSite = prevDisabled;
        }
        capturedDropTarget = null;
        capturedDropXY = null;
        sourceMode = null;
    }

    document.getElementById('tmura-cancel-btn').onclick = () => {
        const savedFiles = [...pendingFiles];
        overlay.classList.remove('active');
        resetPopup();
        continueUploadFlow(savedFiles);
    };

    document.addEventListener('change', (e) => {
        if (!isTmuraActiveOnPage()) return;
        if (e.target && e.target.type === 'file') {
            const allFiles = Array.from(e.target.files || []);
            const imageFiles = allFiles.filter(f => f.type.startsWith('image/'));
            const videoFiles = settings.videoEnabled ? allFiles.filter(f => f.type.startsWith('video/')) : [];
            const files = [...imageFiles, ...videoFiles];

            if (files.length > 0) {
                pendingFiles = files;
                sourceMode = 'input';
                capturedFileInput = e.target;
                e.target.value = '';

                const hasVideo = hasVideoFiles(files);
                let text;
                if (files.length === 1) text = files[0].name;
                else if (hasVideo) text = t('detected_mixed', {count: files.length});
                else text = t('detected_images', {count: files.length});

                document.getElementById('tmura-info-text').innerText = text;

                const videoFormatSelect = document.getElementById('tmura-video-format');
                const videoNote = document.getElementById('tmura-video-note');
                const processBtn = document.getElementById('tmura-process-btn');
                const saveBtn = document.getElementById('tmura-save-btn');

                if (hasVideo) {
                    videoFormatSelect.style.display = 'block';
                    videoNote.classList.add('visible');
                    processBtn.style.display = 'none';
                    saveBtn.style.display = 'block';
                } else {
                    videoFormatSelect.style.display = 'none';
                    videoNote.classList.remove('visible');
                    processBtn.style.display = 'block';
                    saveBtn.style.display = 'block';
                }

                overlay.classList.add('active');
            }
        }
    }, true);

    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === 'toggleSite') {
            isDisabledOnSite = request.disabled;
            sendResponse({ success: true });
        } else if (request.action === 'settingsUpdated') {
            loadSettings(() => {
                const titleEl = overlay.querySelector('.tmura-title');
                const subtitleEl = overlay.querySelector('.tmura-subtitle');
                if (titleEl) titleEl.textContent = t('title');
                if (subtitleEl) subtitleEl.textContent = t('subtitle');
                resetPopup();
                sendResponse({ success: true });
            });
            return true;
        }
    });
})();
