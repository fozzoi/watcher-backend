import httpx
from fastapi import FastAPI
from fastapi.responses import Response

app = FastAPI(title="The Watcher - Failsafe Backend")

# The public Consumet instance
CONSUMET_BASE = "https://api.consumet.org/meta/tmdb"

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")

@app.get("/")
def health():
    return {"status": "online", "message": "The Watcher API is active."}

def get_fallback_link(tmdb_id: str, media_type: str, season: int, episode: int):
    """The Safety Net: Returns a working iframe if the API fails."""
    print("⚠️ API failed. Engaging Vidsrc Embed Fallback...", flush=True)
    if media_type == "movie":
        url = f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}"
    else:
        url = f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&s={season}&e={episode}"
    return {"status": "success", "stream_url": url, "is_m3u8": False}

@app.get("/api/get_stream")
async def get_stream(tmdb_id: str, media_type: str = "movie", season: int = 1, episode: int = 1):
    print(f"📡 Requesting: {media_type.upper()} {tmdb_id}", flush=True)
    
    try:
        # Fast timeout so the mobile app doesn't hang
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            
            # 1. Get Internal ID
            info_url = f"{CONSUMET_BASE}/info/{tmdb_id}?type={media_type}"
            info_res = await client.get(info_url)
            
            if info_res.status_code != 200:
                return get_fallback_link(tmdb_id, media_type, season, episode)

            info_data = info_res.json()
            
            # 2. Find TV Episode ID
            episode_id = tmdb_id 
            if media_type == "tv":
                episodes = info_data.get("episodes", [])
                target_ep = next((ep for ep in episodes if ep.get("season") == season and ep.get("number") == episode), None)
                if not target_ep:
                    return get_fallback_link(tmdb_id, media_type, season, episode)
                episode_id = target_ep["id"]

            # 3. Get Stream Link
            watch_url = f"{CONSUMET_BASE}/watch/{episode_id}?id={tmdb_id}"
            watch_res = await client.get(watch_url)
            
            if watch_res.status_code == 200:
                watch_data = watch_res.json()
                if "sources" in watch_data and len(watch_data["sources"]) > 0:
                    stream_url = watch_data["sources"][0]["url"]
                    print(f"✅ Found direct stream: {stream_url}", flush=True)
                    return {
                        "status": "success",
                        "stream_url": stream_url,
                        "is_m3u8": True
                    }
            
            return get_fallback_link(tmdb_id, media_type, season, episode)

    except Exception as e:
        print(f"🔥 API Error caught: {str(e)}", flush=True)
        return get_fallback_link(tmdb_id, media_type, season, episode)