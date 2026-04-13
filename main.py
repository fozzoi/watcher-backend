import time
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import Response

# --- 1. MEMORY CACHE SETUP ---
# Stores links in RAM for 6 hours so popular movies load instantly
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
# Keeps a single, highly efficient HTTP connection open 
http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    # Limits max connections to save Render RAM
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    http_client = httpx.AsyncClient(timeout=8.0, follow_redirects=True, limits=limits)
    print("🚀 API Lifespan Started: HTTP Client Pool Ready", flush=True)
    yield
    await http_client.aclose()
    print("🛑 API Lifespan Ended: HTTP Client Closed", flush=True)

app = FastAPI(title="The Watcher - Pro Backend", lifespan=lifespan)

CONSUMET_BASE = "https://api.consumet.org/meta/tmdb"

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")

@app.get("/")
def health():
    return {"status": "online", "cache_items": len(CACHE)}

def get_fallback_link(tmdb_id: str, media_type: str, season: int, episode: int):
    """Multi-Mirror Fallback: Tries multiple iframe providers to bypass blocks."""
    print("⚠️ API failed. Generating Embed Fallbacks...", flush=True)
    
    # If one domain is blocked, the frontend can try the others
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
    print(f"\n--- 🎬 STARTING FETCH FOR {media_type.upper()} {tmdb_id} ---", flush=True)
    
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            
            # STEP 1: Ask Consumet for the Movie/Show Info
            info_url = f"{CONSUMET_BASE}/info/{tmdb_id}?type={media_type}"
            print(f"🔍 1. Asking Consumet: {info_url}", flush=True)
            info_res = await client.get(info_url)
            
            if info_res.status_code != 200:
                print(f"❌ Consumet Info Failed! Status Code: {info_res.status_code}", flush=True)
                print(f"❌ Consumet Server says: {info_res.text}", flush=True)
                return get_fallback_link(tmdb_id, media_type, season, episode)

            info_data = info_res.json()
            print(f"✅ 1. Consumet Info Success! Found title: {info_data.get('title', 'Unknown')}", flush=True)
            
            # STEP 2: Find TV Episode
            episode_id = tmdb_id 
            if media_type == "tv":
                episodes = info_data.get("episodes", [])
                target_ep = next((ep for ep in episodes if ep.get("season") == season and ep.get("number") == episode), None)
                if not target_ep:
                    print(f"❌ Episode S{season}E{episode} not found in Consumet's database!", flush=True)
                    return get_fallback_link(tmdb_id, media_type, season, episode)
                
                episode_id = target_ep["id"]
                print(f"✅ 2. Found Episode ID: {episode_id}", flush=True)

            # STEP 3: Get the .m3u8 Link
            watch_url = f"{CONSUMET_BASE}/watch/{episode_id}?id={tmdb_id}"
            print(f"🔍 3. Asking for Video Link: {watch_url}", flush=True)
            watch_res = await client.get(watch_url)
            
            if watch_res.status_code != 200:
                print(f"❌ Consumet Watch Failed! Status Code: {watch_res.status_code}", flush=True)
                print(f"❌ Consumet Server says: {watch_res.text}", flush=True)
                return get_fallback_link(tmdb_id, media_type, season, episode)
                
            watch_data = watch_res.json()
            if "sources" in watch_data and len(watch_data["sources"]) > 0:
                stream_url = watch_data["sources"][0]["url"]
                print(f"🎉 SUCCESS! Found direct .m3u8 stream: {stream_url}", flush=True)
                return {
                    "status": "success",
                    "stream_url": stream_url,
                    "is_m3u8": True
                }
            else:
                print("❌ Consumet returned 200 OK, but the 'sources' array was empty (no video link).", flush=True)
            
            return get_fallback_link(tmdb_id, media_type, season, episode)

    except Exception as e:
        print(f"🔥 FATAL API Error: {str(e)}", flush=True)
        return get_fallback_link(tmdb_id, media_type, season, episode)