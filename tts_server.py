import io, re, asyncio, edge_tts, logging
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, JSONResponse

# ── 日志配置 ──────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"edge_tts_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),  # 同时输出到终端
    ]
)
log = logging.getLogger("edge-tts")

app = FastAPI(title="edge-tts service", version="1.3")

_SILENCE_HEADER = bytes([
    0xFF,0xFB,0x90,0x00, 0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,
]) * 4

_READABLE = re.compile(r'[\w\u3000-\u9fff\uac00-\ud7af\u3040-\u30ff]', re.UNICODE)

def _is_readable(text: str) -> bool:
    return bool(_READABLE.search(text))


@app.get("/tts")
async def tts(
    text:  str = Query(...),
    voice: str = Query("zh-CN-XiaoxiaoNeural"),
    rate:  str = Query("+0%"),
    pitch: str = Query("+0Hz"),
):
    # 过滤无意义文本
    if not _is_readable(text):
        log.info(f"SKIP  voice={voice} rate={rate} text={repr(text)}")
        return StreamingResponse(io.BytesIO(b""), media_type="audio/mpeg")

    log.info(f"TTS   voice={voice} rate={rate} pitch={pitch} text={text[:60]}")

    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])

        if not chunks:
            log.warning(f"EMPTY 微软未返回音频 voice={voice} text={text[:60]}")
            return StreamingResponse(io.BytesIO(b""), media_type="audio/mpeg")

        audio = _SILENCE_HEADER + b"".join(chunks) + _SILENCE_HEADER
        log.info(f"OK    {len(audio)} bytes")
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg")

    except Exception as e:
        log.error(f"ERROR {type(e).__name__}: {e} | text={text[:60]}")
        raise


@app.get("/voices")
async def list_voices(locale: str = Query("")):
    voices = await edge_tts.list_voices()
    if locale:
        voices = [v for v in voices if v["Locale"].startswith(locale)]
    return JSONResponse(voices)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    log.info(f"启动 edge-tts 服务，日志写入: {LOG_FILE}")
    uvicorn.run(app, host="0.0.0.0", port=9527)