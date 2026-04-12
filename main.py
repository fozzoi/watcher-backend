import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI()

# A public consumet instance (Note: Public instances can be slow/unstable)
CONSUMET_URL = "https://api.consumet.org/movies/flixhq"

@app.get("/api/get_stream")
async def get_stream(tmdb_id: str, media_type: str = "movie"):
    print(f"📡 Consumet Request for TMDB: {tmdb_id}", flush=True)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # STEP 1: Search for the movie to get the Consumet internal ID
            # FlixHQ usually needs a title search or a mapping
            search_url = f"{CONSUMET_URL}/{tmdb_id}" 
            # Note: Some consumet instances use /info?id=...
            
            print(f"🔍 Searching: {search_url}", flush=True)
            res = await client.get(search_url)
            
            if res.status_code != 200:
                return {"status": "error", "message": "Could not find movie info"}
            
            data = res.json()
            
            # STEP 2: Get the Source Links
            # Consumet returns an array of sources (m3u8 files)
            if "sources" in data:
                # We grab the first high-quality source (usually index 0)
                stream_url = data["sources"][0]["url"]
                
                print(f"✅ Found Consumet Stream: {stream_url}", flush=True)
                return {
                    "status": "success",
                    "stream_url": stream_url
                }
            
            return {"status": "error", "message": "No links found for this ID"}

    except Exception as e:
        print(f"🔥 Consumet Error: {str(e)}", flush=True)
        return {"status": "error", "message": "Backend timeout or error"}