#!/usr/bin/env python3
"""
Tmura - Translations
Hebrew (default), Yiddish, English
"""

from typing import Dict

LANG_HE = "he"
LANG_YI = "yi"
LANG_EN = "en"
DEFAULT_LANG = LANG_HE

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    LANG_HE: {
        # Window
        "app_name": "תְּמוּרָה",
        "app_title": "תְּמוּרָה - ממיר קבצים חכם",

        # Tabs
        "tab_images": "תמונות",
        "tab_video": "וידאו",
        "tab_audio": "אודיו",
        "tab_pdf": "PDF",
        "tab_extension": "תוסף",
        "tab_settings": "הגדרות",

        # Converter tab
        "files_to_convert": "קבצים להמרה",
        "add_files": "הוסף קבצים",
        "clear": "נקה",
        "drag_files_here": "גרור קבצים לכאן",
        "files_count": "{count} קבצים",
        "settings": "הגדרות",
        "output_format": "פורמט פלט:",
        "quality": "איכות:",
        "output_folder": "תיקיית פלט:",
        "browse": "בחר...",
        "convert": "המר",
        "converting": "ממיר...",
        "converting_file": "ממיר: {file}",
        "done": "הושלם!",
        "converted_count": "הומרו {success} מתוך {total} קבצים",
        "error_no_files": "נא להוסיף קבצים להמרה",
        "success": "הצלחה",
        "error": "שגיאה",

        # Resolution settings
        "resolution_settings": "הגדרות רזולוציה",
        "keep_original_size": "שמור על הגודל המקורי",
        "width": "רוחב:",
        "height": "גובה:",
        "auto": "אוטומטי",

        # Extension tab
        "extension_title": "תוסף Chrome",
        "extension_desc": "תוסף תְּמוּרָה מאפשר כיווץ תמונות\n"
                          "ישירות מכל אתר - גרירה ושחרור או העלאת קבצים.",
        "extension_id": "מזהה תוסף:",
        "install_from_store": "התקן תוסף מחנות Chrome",
        "native_host_title": "חיבור Native Host",
        "connection_status": "סטטוס חיבור:",
        "checking": "בודק...",
        "connected": "מחובר",
        "not_connected": "לא מחובר",
        "connected_responding": "מחובר - Host מגיב",
        "host_not_responding": "Host לא מגיב",
        "host_timeout": "Host לא ענה בזמן",
        "connection_error": "שגיאת חיבור",
        "error_in_response": "שגיאה בתגובת Host",
        "setup_native_host": "הגדר Native Host אוטומטית",
        "reinstall_native_host": "התקן Native Host מחדש",
        "check_connection": "בדוק חיבור",
        "setup_success": "Native Host נרשם בהצלחה.\nמניפסט: {path}\n\nנא להפעיל מחדש את Chrome לחלוטין.",
        "setup_fail": "שגיאת רישום: {error}",
        "setup_fail_permission": "אין הרשאת כתיבה. הפעל את התוכנה כמנהל או בחר תיקייה אחרת.",
        "setup_fail_write": "שגיאה בכתיבת קבצי ה-Host. בדוק הרשאות.",
        "setup_fail_registry": "שגיאת רישום בעורך הרישום.",
        "host_check_fail": "Native Host לא מגיב. ודא שההתקנה הושלמה.",
        "host_check_timeout": "חיבור Native Host עבר זמן.",
        "host_check_error": "בדיקת חיבור נכשלה: {error}",
        "how_it_works": "איך זה עובד",
        "step1": "1. התקן את התוסף מחנות Chrome",
        "step2": "2. לחץ 'הגדר Native Host אוטומטית' לקשר את התוסף לתוכנה",
        "step3": "3. הפעל מחדש את Chrome לחלוטין (סגור את כל החלונות)",
        "step4": "4. גרור תמונות לכל אתר - התוסף יציע כיווץ",
        "step5": "5. בחר איכות ולחץ כיווץ - תמונות מועתקות ללוח",

        # Settings tab
        "app_settings": "הגדרות יישום",
        "server_status": "סטטוס שרת:",
        "server_active": "פעיל",
        "server_not_active": "לא פעיל",
        "start_with_windows": "הפעל עם Windows",
        "minimize_to_tray": "הקטן ל-tray בסגירה",
        "background_server": "שרת המרה ברקע",
        "enable_background_server": "הפעל שרת המרה ברקע",
        "disable_background_server": "כבה שרת המרה ברקע",
        "shortcuts": "קיצורי דרך",
        "shortcut_add": "הוספת קבצים",
        "shortcut_convert": "התחל המרה",
        "shortcut_close": "סגור חלון",
        "shortcut_quit": "יציאה מהתוכנה",
        "language": "שפה:",
        "lang_hebrew": "עברית",
        "lang_yiddish": "אידיש",
        "lang_english": "English",

        # Tray
        "tray_show": "הצג",
        "tray_quit": "יציאה",
        "tray_message": "התוכנה ממשיכה לרוץ ברקע",

        # File dialogs
        "select_files": "בחר קבצים",
        "select_output_folder": "בחר תיקיית פלט",

        # Native host
        "host_installed_msg": "Native Host הותקן בהצלחה",
        "host_manifest": "מניפסט: {path}",
        "host_not_configured": "Host לא מוגדר ב-Registry או שקוד Python לא תקין",
        "host_invalid_response": "תגובה לא תקינה מה-Host",
        "host_connection_ok": "חיבור תקין! Python מגיב.",

        # Auto output folder
        "output_auto_hint": "ריק = תיקיית הקובץ המקורי",
        "auto_folder_info": "הקבצים יישמרו בתיקיית 'קבצים שהומרו' ליד הקובץ המקורי, עם שם התוכנה בשם הקובץ.",

        # PDF features
        "pdf_convert": "המרת PDF",
        "pdf_merge": "איחוד קבצי PDF",
        "merge_info": "אחד את כל קבצי ה-PDF שהוספת לקובץ אחד.",
        "merge_btn": "אחד קבצים",
        "error_merge_min": "נא להוסיף לפחות 2 קבצי PDF לאיחוד",
        "merge_success": "הקבצים אוחדו בהצלחה: {path}",
        "pdf_crop_marks": "סימון קווי חיתוך",
        "crop_margin_cm": "שוליים (ס\"מ):",
        "crop_info": "מוסיף קווי חיתוך מסביב לדפים לפי השוליים שנבחרו.",
        "add_crop_marks": "הוסף קווי חיתוך",
        "error_no_library": "חסרה ספריית {lib}. נא להתקין אותה.",

        # Audio features
        "audio_convert": "המרת אודיו",
        "audio_cover": "תמונת עטיפה",
        "no_cover": "אין עטיפה",
        "extract_cover": "חלץ עטיפה",
        "add_cover": "הוסף עטיפה",
        "audio_metadata": "פרטי שיר",
        "meta_title": "שם שיר:",
        "meta_artist": "אמן:",
        "meta_album": "אלבום:",
        "meta_year": "שנה:",
        "meta_track": "רצועה:",
        "meta_genre": "ז'אנר:",
        "save_metadata": "שמור פרטים",
        "metadata_saved": "פרטי השיר נשמרו בהצלחה",
        "error_metadata_save": "שגיאה בשמירת פרטי השיר",
        "cover_extracted": "תמונת העטיפה חולצה: {path}",
        "error_no_cover": "אין תמונת עטיפה בקובץ זה",
        "cover_added": "תמונת העטיפה נוספה בהצלחה",
        "error_cover_add": "שגיאה בהוספת תמונת עטיפה",
        "select_cover_image": "בחר תמונת עטיפה",
        "remove_selected": "הסר נבחרים",
        "error_select_file": "נא לבחור קובץ מהרשימה",
        "conversion_errors": "שגיאות המרה",
        "error_output_empty": "קובץ הפלט ריק",
        "error_unsupported_format": "פורמט לא נתמך",
        "error_timeout": "תם הזמן המוקצב",
        "error_log": "לוג שגיאות",
        "refresh_log": "רענן לוג",
        "cpu_threads": "מעבדים:",
    },

    LANG_YI: {
        "app_name": "תְּמוּרָה",
        "app_title": "תְּמוּרָה - פֿאַרעמלער פֿון טעקעס",

        "tab_images": "בילדער",
        "tab_video": "ווידעא",
        "tab_audio": "אַודיא",
        "tab_pdf": "PDF",
        "tab_extension": "עקסטענשאַן",
        "tab_settings": "אײַנשטעלונגען",

        "files_to_convert": "טעקעס צו פֿאַרוואַנדלען",
        "add_files": "לייג צו טעקעס",
        "clear": "ריין",
        "drag_files_here": "שלעפּ טעקעס דאָ",
        "files_count": "{count} טעקעס",
        "settings": "אײַנשטעלונגען",
        "output_format": "אַרויספֿאָרמאַט:",
        "quality": "קוואַליטעט:",
        "output_folder": "אַרויסמאַפּע:",
        "browse": "ווייל...",
        "convert": "פֿאַרוואַנדל",
        "converting": "פֿאַרוואַנדלט...",
        "converting_file": "פֿאַרוואַנדלט: {file}",
        "done": "געטאָן!",
        "converted_count": "פֿאַרוואַנדלט {success} פֿון {total} טעקעס",
        "error_no_files": "לייג צו טעקעס צו פֿאַרוואַנדלען",
        "success": "הצלחה",
        "error": "טעות",

        "resolution_settings": "רעזאָלוציע אײַנשטעלונגען",
        "keep_original_size": "האַלט אָריגינעל גרייס",
        "width": "ברייט:",
        "height": "הייך:",
        "auto": "אויטאָמאַטיש",

        "extension_title": "Chrome עקסטענשאַן",
        "extension_desc": "תְּמוּרָה עקסטענשאַן לאָזט קאַמפּרעסירן בילדער\n"
                          "פֿון יעדער וועבזייטל - שלעפּן און אָפּלייגן אָדער אַרויפֿלאָדן טעקעס.",
        "extension_id": "עקסטענשאַן ID:",
        "install_from_store": "אינסטאַליר עקסטענשאַן פֿון Chrome סטאָר",
        "native_host_title": "Native Host פֿאַרבינדונג",
        "connection_status": "פֿאַרבינדונג סטאַטוס:",
        "checking": "קאָנטראָלירט...",
        "connected": "פֿאַרבונדן",
        "not_connected": "נישט פֿאַרבונדן",
        "connected_responding": "פֿאַרבונדן - Host ענטפֿערט",
        "host_not_responding": "Host ענטפֿערט נישט",
        "host_timeout": "Host האָט נישט געענטפֿערט אין צײַט",
        "connection_error": "פֿאַרבינדונג טעות",
        "error_in_response": "טעות אין Host ענטפֿער",
        "setup_native_host": "שטעל אָן Native Host אויטאָמאַטיש",
        "reinstall_native_host": "אינסטאַליר Native Host איבער",
        "check_connection": "קאָנטראָליר פֿאַרבינדונג",
        "setup_success": "Native Host איינגעשריבן מיט הצלחה.\nמאַניפֿעסט: {path}\n\nביטע רעסטאַרט Chrome גאַנץ.",
        "setup_fail": "רעגיסטרי טעות: {error}",
        "setup_fail_permission": "קיין שרייב רשות נישט. לויף די פּראָגראַם אלס אַדמין.",
        "setup_fail_write": "טעות שרייבן Host טעקעס. קאָנטראָליר רשימות.",
        "setup_fail_registry": "רעגיסטרי רעגיסטראַציע טעות.",
        "host_check_fail": "Native Host ענטפֿערט נישט. זיכער אַז אינסטאַלאַציע איז געטאָן.",
        "host_check_timeout": "Native Host פֿאַרבינדונג איז איבער צײַט.",
        "host_check_error": "קאָנטראָל פֿאַרבינדונג דורכגעפֿאַלט: {error}",
        "how_it_works": "ווי עס אַרבעט",
        "step1": "1. אינסטאַליר די עקסטענשאַן פֿון Chrome סטאָר",
        "step2": "2. דריק 'שטעל אָן Native Host אויטאָמאַטיש' צו פֿאַרבינדן",
        "step3": "3. רעסטאַרט Chrome גאַנץ (פֿאַרמאַך אַלע פֿענצטער)",
        "step4": "4. שלעפּ בילדער צו יעדער וועבזייטל",
        "step5": "5. ווייל קוואַליטעט און דריק קאַמפּרעס - בילדער קאָפּירט צו קליפּבאָרד",

        "app_settings": "אײַנשטעלונגען",
        "server_status": "סערווער סטאַטוס:",
        "server_active": "אַקטיוו",
        "server_not_active": "נישט אַקטיוו",
        "start_with_windows": "זטאַרט מיט Windows",
        "minimize_to_tray": "מינימיר צו tray בײַ פֿאַרמאַך",
        "background_server": "קאַנווערט סערווער אין הינטערגרונט",
        "enable_background_server": "שטעל אָן סערווער אין הינטערגרונט",
        "disable_background_server": "שטעל אָפּ סערווער אין הינטערגרונט",
        "shortcuts": "קירצע שליסלעך",
        "shortcut_add": "לייג צו טעקעס",
        "shortcut_convert": "הייב אָן פֿאַרוואַנדלונג",
        "shortcut_close": "פֿאַרמאַך פֿענצטער",
        "shortcut_quit": "גיי אַרויס",
        "language": "שפּראַך:",
        "lang_hebrew": "עברית",
        "lang_yiddish": "אידיש",
        "lang_english": "English",

        "tray_show": "ווייז",
        "tray_quit": "גיי אַרויס",
        "tray_message": "די פּראָגראַם לויפֿט אין הינטערגרונט",

        "select_files": "ווייל טעקעס",
        "select_output_folder": "ווייל אַרויסמאַפּע",

        "host_installed_msg": "Native Host אינסטאַלירט מיט הצלחה",
        "host_manifest": "מאַניפֿעסט: {path}",
        "host_not_configured": "Host נישט קאָנפֿיגורירט אין Registry",
        "host_invalid_response": "אומגילטיק ענטפֿער פֿון Host",
        "host_connection_ok": "פֿאַרבינדונג גוט! Python ענטפֿערט.",

        "output_auto_hint": "ליידיק = טעקע פֿון מקור טעקע",
        "auto_folder_info": "טעקעס וועלן געהיטן אין 'קבצים שהומרו' מאַפּע לעבן מקור טעקע, מיט נאָמען פֿון פּראָגראַם.",

        "pdf_convert": "פֿאַרוואַנדל PDF",
        "pdf_merge": "פֿאַראייניקן PDF טעקעס",
        "merge_info": "פֿאַראייניקן אַלע PDF טעקעס צו איין טעקע.",
        "merge_btn": "פֿאַראייניקן טעקעס",
        "error_merge_min": "לייג צו מינדסטענס 2 PDF טעקעס צו פֿאַראייניקן",
        "merge_success": "טעקעס פֿאַראייניקט: {path}",
        "pdf_crop_marks": "שנייד ליניעס מאַרקירונג",
        "crop_margin_cm": "מאַרגינ (ס\"מ):",
        "crop_info": "לייגט שנייד ליניעס אַרום בלעטער לויט די מאַרגינ.",
        "add_crop_marks": "לייג צו שנייד ליניעס",
        "error_no_library": "פֿעלט {lib} ביבליאָטעק. ביטע אינסטאַליר עס.",

        "audio_convert": "פֿאַרוואַנדל אַודיא",
        "audio_cover": "קאָווער בילד",
        "no_cover": "קיין קאָווער",
        "extract_cover": "עקסטראַקט קאָווער",
        "add_cover": "לייג צו קאָווער",
        "audio_metadata": "ליד דעטאַלן",
        "meta_title": "ליד נאָמען:",
        "meta_artist": "קינסטלער:",
        "meta_album": "אַלבאָם:",
        "meta_year": "יאָר:",
        "meta_track": "שפּור:",
        "meta_genre": "זשאַנער:",
        "save_metadata": "שפּאַר דעטאַלן",
        "metadata_saved": "ליד דעטאַלן געהיטן מיט הצלחה",
        "error_metadata_save": "טעות היטן ליד דעטאַלן",
        "cover_extracted": "קאָווער בילד עקסטראַקטירט: {path}",
        "error_no_cover": "קיין קאָווער בילד אין די טעקע",
        "cover_added": "קאָווער בילד צוגעלייגט מיט הצלחה",
        "error_cover_add": "טעות צולייגן קאָווער בילד",
        "select_cover_image": "ווייל קאָווער בילד",
        "remove_selected": "וועף אויס געקליבן",
        "error_select_file": "ביטע ווייל אַ טעקע פֿון די רשימה",
        "conversion_errors": "פֿאַרוואַנדלונג טעות'ן",
        "error_output_empty": "אַרויס טעקע ליידיק",
        "error_unsupported_format": "נישט געשטיצט פֿאָרמאַט",
        "error_timeout": "איבער צײַט",
        "error_log": "טעות לאָג",
        "refresh_log": "רעפֿרעש לאָג",
        "cpu_threads": "פּראָצעסאָרן:",
    },

    LANG_EN: {
        "app_name": "Tmura",
        "app_title": "Tmura - Smart File Converter",

        "tab_images": "Images",
        "tab_video": "Video",
        "tab_audio": "Audio",
        "tab_pdf": "PDF",
        "tab_extension": "Extension",
        "tab_settings": "Settings",

        "files_to_convert": "Files to convert",
        "add_files": "Add files",
        "clear": "Clear",
        "drag_files_here": "Drag files here",
        "files_count": "{count} files",
        "settings": "Settings",
        "output_format": "Output format:",
        "quality": "Quality:",
        "output_folder": "Output folder:",
        "browse": "Browse...",
        "convert": "Convert",
        "converting": "Converting...",
        "converting_file": "Converting: {file}",
        "done": "Done!",
        "converted_count": "Converted {success} of {total} files",
        "error_no_files": "Please add files to convert",
        "success": "Success",
        "error": "Error",

        "resolution_settings": "Resolution Settings",
        "keep_original_size": "Keep original size",
        "width": "Width:",
        "height": "Height:",
        "auto": "Auto",

        "extension_title": "Chrome Extension",
        "extension_desc": "Tmura extension enables image compression\n"
                          "from any website - drag & drop or file uploads.",
        "extension_id": "Extension ID:",
        "install_from_store": "Install Extension from Chrome Web Store",
        "native_host_title": "Native Host Connection",
        "connection_status": "Connection status:",
        "checking": "Checking...",
        "connected": "Connected",
        "not_connected": "Not connected",
        "connected_responding": "Connected - Host responding",
        "host_not_responding": "Host not responding",
        "host_timeout": "Host timed out",
        "connection_error": "Connection error",
        "error_in_response": "Error in host response",
        "setup_native_host": "Setup Native Host Automatically",
        "reinstall_native_host": "Reinstall Native Host",
        "check_connection": "Check Connection",
        "setup_success": "Native Host registered successfully.\nManifest: {path}\n\nPlease restart Chrome completely.",
        "setup_fail": "Registry error: {error}",
        "setup_fail_permission": "No write permission. Run the app as administrator or choose a different folder.",
        "setup_fail_write": "Error writing host files. Check permissions.",
        "setup_fail_registry": "Registry registration error.",
        "host_check_fail": "Native Host is not responding. Make sure setup is complete.",
        "host_check_timeout": "Native Host connection timed out.",
        "host_check_error": "Connection check failed: {error}",
        "how_it_works": "How it works",
        "step1": "1. Install the extension from Chrome Web Store",
        "step2": "2. Click 'Setup Native Host Automatically' to link extension to app",
        "step3": "3. Restart Chrome completely (close all windows)",
        "step4": "4. Drag images to any website - extension will offer compression",
        "step5": "5. Choose quality and click Compress - images copied to clipboard",

        "app_settings": "App settings",
        "server_status": "Server status:",
        "server_active": "Active",
        "server_not_active": "Not active",
        "start_with_windows": "Start with Windows",
        "minimize_to_tray": "Minimize to tray on close",
        "background_server": "Background conversion server",
        "enable_background_server": "Enable background conversion server",
        "disable_background_server": "Disable background conversion server",
        "shortcuts": "Keyboard shortcuts",
        "shortcut_add": "Add files",
        "shortcut_convert": "Start conversion",
        "shortcut_close": "Close window",
        "shortcut_quit": "Quit application",
        "language": "Language:",
        "lang_hebrew": "עברית",
        "lang_yiddish": "אידיש",
        "lang_english": "English",

        "tray_show": "Show",
        "tray_quit": "Quit",
        "tray_message": "Application running in background",

        "select_files": "Select files",
        "select_output_folder": "Select output folder",

        "host_installed_msg": "Native Host installed successfully",
        "host_manifest": "Manifest: {path}",
        "host_not_configured": "Host not configured in Registry or Python code invalid",
        "host_invalid_response": "Invalid response from Host",
        "host_connection_ok": "Connection OK! Python is responding.",

        "output_auto_hint": "Empty = source file directory",
        "auto_folder_info": "Files will be saved in a 'Converted files' subfolder next to the source, with the app name in the filename.",

        "pdf_convert": "PDF Conversion",
        "pdf_merge": "Merge PDF Files",
        "merge_info": "Merge all added PDF files into a single document.",
        "merge_btn": "Merge Files",
        "error_merge_min": "Please add at least 2 PDF files to merge",
        "merge_success": "Files merged successfully: {path}",
        "pdf_crop_marks": "Crop Marks",
        "crop_margin_cm": "Margin (cm):",
        "crop_info": "Adds crop marks around pages based on the selected margin.",
        "add_crop_marks": "Add Crop Marks",
        "error_no_library": "Missing {lib} library. Please install it.",

        "audio_convert": "Audio Conversion",
        "audio_cover": "Cover Art",
        "no_cover": "No cover",
        "extract_cover": "Extract Cover",
        "add_cover": "Add Cover",
        "audio_metadata": "Song Details",
        "meta_title": "Title:",
        "meta_artist": "Artist:",
        "meta_album": "Album:",
        "meta_year": "Year:",
        "meta_track": "Track:",
        "meta_genre": "Genre:",
        "save_metadata": "Save Details",
        "metadata_saved": "Song details saved successfully",
        "error_metadata_save": "Error saving song details",
        "cover_extracted": "Cover art extracted: {path}",
        "error_no_cover": "No cover art in this file",
        "cover_added": "Cover art added successfully",
        "error_cover_add": "Error adding cover art",
        "select_cover_image": "Select cover image",
        "remove_selected": "Remove Selected",
        "error_select_file": "Please select a file from the list",
        "conversion_errors": "Conversion errors",
        "error_output_empty": "Output file is empty",
        "error_unsupported_format": "Unsupported format",
        "error_timeout": "Operation timed out",
        "error_log": "Error Log",
        "refresh_log": "Refresh Log",
        "cpu_threads": "CPU Threads:",
    },
}


class Translator:
    _instance = None

    def __init__(self, lang: str = DEFAULT_LANG):
        self._lang = lang
        self._observers = []

    @classmethod
    def instance(cls) -> "Translator":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def lang(self) -> str:
        return self._lang

    @lang.setter
    def lang(self, value: str):
        if value in TRANSLATIONS:
            self._lang = value
            for cb in self._observers:
                cb()

    def add_observer(self, callback):
        self._observers.append(callback)

    def t(self, key: str, **kwargs) -> str:
        text = TRANSLATIONS.get(self._lang, {}).get(key, TRANSLATIONS.get(DEFAULT_LANG, {}).get(key, key))
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                return text
        return text


def t(key: str, **kwargs) -> str:
    return Translator.instance().t(key, **kwargs)
