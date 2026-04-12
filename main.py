from fastapi import FastAPI
from resolver import StreamResolver

app = FastAPI()
resolver = StreamResolver()

@app.get("/api/get_stream")
async def get_stream(tmdb_id: str):
    print(f"Scraping real link for ID: {tmdb_id}...", flush=True)
    
    # Use our new lightweight resolver
    final_link = resolver.resolve(tmdb_id)
    
    if final_link:
        return {
            "status": "success",
            "stream_url": final_link,
            "is_m3u8": final_link.endswith(".m3u8")
        }
    
    return {"status": "error", "message": "Failed to extract link"}