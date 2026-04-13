import time
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import Response

# --- 1. MEMORY CACHE SETUP ---
CACHE = {}
CACHE_TTL = 21600  # Seconds (6 hours)

def get_cache(key: str):
    if key in CACHE:
        if time.time() - CACHE[key]['timestamp'] < CACHE_TTL:
            return CACHE[key]['data']
        else:
            del CACHE[key] # Expired
    return None

def set_cache(key: str, data: dict):
    CACHE[key] = {'timestamp': time.time(), 'data': data}

# --- 2. CONNECTION POOLING ---
http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    http_client = httpx.AsyncClient(timeout=8.0, follow_redirects=True, limits=limits)
    print("🚀 API Lifespan Started: HTTP Client Pool Ready", flush=True)
    yield
    await http_client.aclose()
    print("🛑 API Lifespan Ended: HTTP Client Closed", flush=True)

app = FastAPI(title="The Watcher - Pro Backend", lifespan=lifespan)

# 🚨 THE FIX: Swapped to an active community mirror! 🚨
CONSUMET_BASE = "https://c.delusionz.xyz/meta/tmdb"

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")

@app.get("/")
def health():
    return {"status": "online", "cache_items": len(CACHE)}

def get_fallback_link(tmdb_id: str, media_type: str, season: int, episode: int):
    print("⚠️ API failed. Generating Embed Fallbacks...", flush=True)
    if media_type == "movie":
        return {
            "status": "success",
            "is_m3u8": False,
            "stream_url": f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}",
            "backup_url_1": f"https://vidsrc.pro/embed/movie/{tmdb_id}",
            "backup_url_2": f"https://superembed.stream/movie?tmdb={tmdb_id}"
        }
    else:
        return {
            "status": "success",
            "is_m3u8": False,
            "stream_url": f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&s={season}&e={episode}",
            "backup_url_1": f"https://vidsrc.pro/embed/tv/{tmdb_id}/{season}/{episode}",
            "backup_url_2": f"https://superembed.stream/tv?tmdb={tmdb_id}&season={season}&episode={episode}"
        }

@app.get("/api/get_stream")
async def get_stream(tmdb_id: str, media_type: str = "movie", season: int = 1, episode: int = 1):
    cache_key = f"{media_type}_{tmdb_id}_{season}_{episode}"
    
    cached_result = get_cache(cache_key)
    if cached_result:
        print(f"⚡ Serving {cache_key} from CACHE", flush=True)
        return cached_result

    print(f"📡 Fetching fresh data for: {cache_key}", flush=True)
    
    try:
        info_url = f"{CONSUMET_BASE}/info/{tmdb_id}?type={media_type}"
        info_res = await http_client.get(info_url)
        
        if info_res.status_code != 200:
            return get_fallback_link(tmdb_id, media_type, season, episode)

        info_data = info_res.json()
        
        episode_id = tmdb_id 
        if media_type == "tv":
            episodes = info_data.get("episodes", [])
            target_ep = next((ep for ep in episodes if ep.get("season") == season and ep.get("number") == episode), None)
            if not target_ep:
                return get_fallback_link(tmdb_id, media_type, season, episode)
            episode_id = target_ep["id"]

        watch_url = f"{CONSUMET_BASE}/watch/{episode_id}?id={tmdb_id}"
        watch_res = await http_client.get(watch_url)
        
        if watch_res.status_code == 200:
            watch_data = watch_res.json()
            if "sources" in watch_data and len(watch_data["sources"]) > 0:
                stream_url = watch_data["sources"][0]["url"]
                print(f"✅ Found direct stream: {stream_url}", flush=True)
                
                result = {
                    "status": "success",
                    "stream_url": stream_url,
                    "is_m3u8": True
                }
                set_cache(cache_key, result)
                return result
        
        return get_fallback_link(tmdb_id, media_type, season, episode)

    except Exception as e:
        print(f"🔥 API Error caught: {str(e)}", flush=True)
        return get_fallback_link(tmdb_id, media_type, season, episode)