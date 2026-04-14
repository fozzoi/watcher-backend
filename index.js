const express = require('express');
const { MOVIES } = require('@consumet/extensions');
const cors = require('cors');

const app = express();
app.use(cors());

// We'll use two different providers now to beat the 404s
const flixhq = new MOVIES.FlixHQ();

app.get('/api/get_stream', async (req, res) => {
    const { tmdb_id, media_type, title, season, episode } = req.query;
    console.log(`📡 Requesting: ${media_type.toUpperCase()} | "${title}"`);

    try {
        // 1. Search FlixHQ
        const searchResults = await flixhq.search(title);
        
        // 🎯 ACCURACY FIX: Match Title AND Type (Movie/TV)
        // This stops "The Boys" from matching "The Boys in the Band"
        const match = searchResults.results.find(r => {
            const sameTitle = r.title.toLowerCase().includes(title.toLowerCase());
            const sameType = media_type === 'tv' ? r.type === 'TV Series' : r.type === 'Movie';
            return sameTitle && sameType;
        });

        if (match) {
            console.log(`✅ Correct Match Found: ${match.id} (${match.type})`);
            const info = await flixhq.fetchMediaInfo(match.id);
            
            let epId = match.id;
            if (media_type === 'tv') {
                const ep = info.episodes.find(e => e.season == season && e.number == episode);
                if (!ep) throw new Error("Episode not found in provider database");
                epId = ep.id;
            }

            console.log(`🔗 Extracting from: ${epId}`);
            // Attempt to get sources
            const sources = await flixhq.fetchEpisodeSources(epId, match.id);

            if (sources?.sources?.length > 0) {
                console.log("🎉 SUCCESS! Link extracted.");
                return res.json({
                    status: 'success',
                    stream_url: sources.sources[0].url,
                    is_m3u8: true
                });
            }
        }
        
        throw new Error("No working direct sources found");

    } catch (error) {
        console.log(`🛑 Scraper Error: ${error.message}`);
        
        // Final Fallback: The Iframe
        // If the scrapers are 404-ing, the iframe is our only hope!
        const fallback = media_type === 'movie' 
            ? `https://vidsrc.me/embed/movie?tmdb=${tmdb_id}`
            : `https://vidsrc.me/embed/tv?tmdb=${tmdb_id}&s=${season}&e=${episode}`;
        
        res.json({ 
            status: 'success', 
            stream_url: fallback, 
            is_m3u8: false,
            msg: error.message 
        });
    }
});

const PORT = process.env.PORT || 10000;
app.listen(PORT, () => console.log(`🚀 Watcher Engine running on ${PORT}`));