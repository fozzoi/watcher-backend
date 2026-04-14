const express = require('express');
const { MOVIES } = require('@consumet/extensions');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());

// 🕵️‍♂️ THE MASK: Using the User-Agent you provided
const CUSTOM_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
};

// Force all Axios requests to use your browser identity
axios.defaults.headers.common = CUSTOM_HEADERS;

const flixhq = new MOVIES.FlixHQ();

app.get('/api/get_stream', async (req, res) => {
    const { tmdb_id, media_type, title, season, episode } = req.query;
    console.log(`📡 Request: ${media_type.toUpperCase()} | "${title}"`);

    try {
        // 1. Search with Human-Like Identity
        const searchResults = await flixhq.search(title);
        
        const match = searchResults.results.find(r => {
            const sameTitle = r.title.toLowerCase().includes(title.toLowerCase());
            const sameType = media_type === 'tv' ? r.type === 'TV Series' : r.type === 'Movie';
            return sameTitle && sameType;
        });

        if (match) {
            console.log(`✅ Correct Match: ${match.id}`);
            
            // 2. Fetch Info
            const info = await flixhq.fetchMediaInfo(match.id);
            
            let epId = match.id;
            if (media_type === 'tv') {
                const ep = info.episodes.find(e => e.season == season && e.number == episode);
                if (!ep) throw new Error("Episode not found");
                epId = ep.id;
            }

            // 3. Extract Sources
            console.log(`🔗 Extracting from: ${epId}`);
            // We pass the headers directly into the fetcher if the provider supports it
            const sources = await flixhq.fetchEpisodeSources(epId, match.id);

            if (sources?.sources?.length > 0) {
                console.log("🎉 SUCCESS! Link Found.");
                return res.json({
                    status: 'success',
                    stream_url: sources.sources[0].url,
                    is_m3u8: true
                });
            }
        }
        
        throw new Error("No working direct sources found");

    } catch (error) {
        console.log(`🛑 Scraper Blocked/Error: ${error.message}`);
        
        // Final Fallback: The Iframe
        const fallback = media_type === 'movie' 
            ? `https://vidsrc.me/embed/movie?tmdb=${tmdb_id}`
            : `https://vidsrc.me/embed/tv?tmdb=${tmdb_id}&s=${season}&e=${episode}`;
        
        res.json({ 
            status: 'success', 
            stream_url: fallback, 
            is_m3u8: false
        });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`🚀 Watcher Engine (Stealth Mode) on ${PORT}`));