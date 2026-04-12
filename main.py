import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()

# A more reliable meta provider for TMDB IDs
CONSUMET_BASE = "https://api.consumet.org/meta/tmdb"

@app.get("/api/get_stream")
async def get_stream(tmdb_id: str, media_type: str = "movie", season: int = 1, episode: int = 1):
    print(f"📡 Requesting: {media_type} {tmdb_id}", flush=True)
    
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            # STEP 1: Get the Info (This maps TMDB ID to Consumet's internal system)
            info_url = f"{CONSUMET_BASE}/info/{tmdb_id}?type={media_type}"
            print(f"🔍 Info Check: {info_url}", flush=True)
            
            info_res = await client.get(info_url)
            
            # If Consumet is down or doesn't have the movie, use the Fallback
            if info_res.status_code != 200:
                print("⚠️ Consumet info failed, using Fallback Resolver", flush=True)
                return get_fallback_link(tmdb_id, media_type, season, episode)

            info_data = info_res.json()
            
            # STEP 2: Get the Episode ID
            episode_id = tmdb_id # Default for movies
            if media_type == "tv":
                episodes = info_data.get("episodes", [])
                target_ep = next((ep for ep in episodes if ep.get("season") == season and ep.get("number") == episode), None)
                if not target_ep:
                    return {"status": "error", "message": "Episode not found"}
                episode_id = target_ep["id"]

            # STEP 3: Get the Watch Link
            watch_url = f"{CONSUMET_BASE}/watch/{episode_id}?id={tmdb_id}"
            print(f"🎬 Watch Check: {watch_url}", flush=True)
            
            watch_res = await client.get(watch_url)
            watch_data = watch_res.json()
            
            if "sources" in watch_data:
                # We return the first high-quality source
                return {
                    "status": "success",
                    "stream_url": watch_data["sources"][0]["url"],
                    "is_m3u8": True
                }
            
            # Final Fallback if sources are empty
            return get_fallback_link(tmdb_id, media_type, season, episode)

    except Exception as e:
        print(f"🔥 Error: {str(e)}", flush=True)
        return get_fallback_link(tmdb_id, media_type, season, episode)

def get_fallback_link(tmdb_id, media_type, season, episode):
    # This ensures your app ALWAYS plays something, even if Consumet is down
    if media_type == "movie":
        url = f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}"
    else:
        url = f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&s={season}&e={episode}"
    return {"status": "success", "stream_url": url, "is_m3u8": False}