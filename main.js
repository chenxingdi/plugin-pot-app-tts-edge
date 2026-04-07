async function tts(text, _lang, options = {}) {
    const { config, utils } = options;
    const { http } = utils;
    const { fetch } = http;

    let { requestPath, voice, rate, pitch } = config;

    // ── 请求路径处理 ──────────────────────────────────────────────
    if (!requestPath) {
        requestPath = "http://localhost:9527";
    }
    if (!/https?:\/\/.+/.test(requestPath)) {
        requestPath = `http://${requestPath}`;
    }
    if (requestPath.endsWith('/')) {
        requestPath = requestPath.slice(0, -1);
    }
    if (!requestPath.endsWith('/tts')) {
        requestPath += '/tts';
    }

    // ── 参数默认值 ────────────────────────────────────────────────
    if (!voice) {
        voice = "zh-CN-XiaoxiaoNeural";
    }
    if (!rate) {
        rate = "+0%";
    }
    if (!pitch) {
        pitch = "+0Hz";
    }

    // ── 根据语言自动切换音色 ──────────────────────────────────────
    const langVoiceMap = {
        "zh":  "zh-CN-XiaoxiaoNeural", 
        "en":  "en-US-JennyNeural",
        "ja":  "ja-JP-NanamiNeural",
        "ko":  "ko-KR-SunHiNeural",
        "fr":  "fr-FR-DeniseNeural",
        "de":  "de-DE-KatjaNeural",
        "es":  "es-ES-ElviraNeural",
        "ru":  "ru-RU-SvetlanaNeural",
        "it":  "it-IT-ElsaNeural",
        "pt":  "pt-BR-FranciscaNeural",
        "tr":  "tr-TR-EmelNeural",
        "vi":  "vi-VN-HoaiMyNeural",
    };

    // 1. 优先检测文本：如果是英文文本，强制识别语言为 "en"
    let detectLang = _lang;
    if (/^[a-zA-Z0-9\s\p{P}]+$/u.test(text)) {
        detectLang = "en";
    }

    // 2. 获取并应用音色（只保留这一个 autoVoice 块）
    const autoVoice = langVoiceMap[detectLang];

    if (autoVoice) {
        const voiceLang = voice.substring(0, 5).toLowerCase(); 
        const targetLang = autoVoice.substring(0, 5).toLowerCase();
        // 仅当用户未手动选择对应语言的音色时才自动切换
        if (voiceLang !== targetLang) {
            console.log(`[EdgeTTS] 自动切换音色: ${voice} → ${autoVoice} (识别语种: ${detectLang})`);
            voice = autoVoice;
        }
    }

    // ── 构造请求 URL ──────────────────────────────────────────────
    const url = `${requestPath}?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voice)}&rate=${encodeURIComponent(rate)}&pitch=${encodeURIComponent(pitch)}`;

    console.log(`[EdgeTTS] url=${url}`);

    const res = await fetch(url, {
        method: "GET",
        responseType: 3   // 二进制
    });

    if (res.ok) {
        const result = res.data;
        if (result) {
            return result;
        } else {
            throw JSON.stringify(result);
        }
    } else {
        throw `Http Request Error\nHttp Status: ${res.status}\n${JSON.stringify(res.data)}`;
    }
}