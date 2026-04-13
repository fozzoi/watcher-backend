import asyncio
from fastapi import FastAPI, HTTPException
from playwright.async_api import async_playwright

app = FastAPI()

@app.get("/api/get_stream")
async def get_stream(tmdb_id: str):
    print(f"🚀 Launching browser for ID: {tmdb_id}", flush=True)
    
    async with async_playwright() as p:
        # Launching Chromium with specific flags to save memory
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = await browser.new_page()

        try:
            # 1. Go to the embed site
            url = f"https://vsembed.ru/embed/movie/{tmdb_id}"
            print(f"🌐 Navigating to: {url}", flush=True)
            await page.goto(url, timeout=30000)

            # 2. Wait for the video link to appear in the code
            # Playwright is smart: it executes the site's JS for us
            await page.wait_for_selector("video", timeout=15000)
            
            # 3. Pull the src from the video tag
            stream_url = await page.eval_on_selector("video", "el => el.src")
            
            print(f"✅ Found Link: {stream_url}", flush=True)
            return {"status": "success", "stream_url": stream_url, "is_m3u8": True}

        except Exception as e:
            print(f"❌ Browser Error: {e}", flush=True)
            return {"status": "error", "message": str(e)}
        finally:
            await browser.close()

@app.get("/")
def health():
    return {"status": "online"}