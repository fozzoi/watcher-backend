from fastapi import FastAPI
from fastapi.responses import Response
from resolver import StreamResolver

app = FastAPI(title="The Watcher - Docker Scraper Engine")
resolver = StreamResolver()

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(content="", media_type="image/x-icon")

@app.get("/")
def health():
    return {"status": "online", "mode": "Docker Scraper"}

@app.get("/api/get_stream")
async def get_stream(tmdb_id: str, media_type: str = "movie", season: int = 1, episode: int = 1):
    print(f"🕵️ Scraping link for {media_type.upper()} ID: {tmdb_id}...", flush=True)
    
    # 1. Try to magically extract the real link
    final_link = resolver.resolve(tmdb_id, media_type, season, episode)
    
    if final_link:
        print(f"✅ Extracted Link: {final_link}", flush=True)
        return {
            "status": "success",
            "stream_url": final_link,
            "is_m3u8": final_link.endswith(".m3u8")
        }
    
    # 2. If the scraper fails (site changed code), use the Iframe Fallback
    print("⚠️ Scraping failed, engaging iframe fallback...", flush=True)
    if media_type == "movie":
        fallback_url = f"https://vidsrc.me/embed/movie?tmdb={tmdb_id}"
    else:
        fallback_url = f"https://vidsrc.me/embed/tv?tmdb={tmdb_id}&s={season}&e={episode}"
        
    return {"status": "success", "stream_url": fallback_url, "is_m3u8": False}