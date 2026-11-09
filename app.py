from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "active"}), 200

@app.route('/api/extract', methods=['POST'])
def extract_video():
    data = request.get_json()
    video_url = data.get('url') if data else None

    if not video_url:
        return jsonify({"error": "URL missing"}), 400

    # Advanced options to bypass bot detection & JS player challenges
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
        'format': 'best',
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        # Extra extractor args to handle recent YouTube updates
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            formats_data = []
            for fmt in info.get('formats', []):
                if fmt.get('url'):
                    formats_data.append({
                        'format_id': fmt.get('format_id'),
                        'resolution': fmt.get('format_note') or fmt.get('resolution') or f"{fmt.get('height')}p",
                        'ext': fmt.get('ext'),
                        'filesize': fmt.get('filesize') or fmt.get('filesize_approx'),
                        'url': fmt.get('url'),
                        'has_video': fmt.get('vcodec') != 'none',
                        'has_audio': fmt.get('acodec') != 'none'
                    })

            result = {
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'channel': info.get('uploader'),
                'views': info.get('view_count'),
                'description': info.get('description'),
                'formats': formats_data
            }
            return jsonify(result), 200

    except Exception as e:
        error_msg = str(e)
        # Fallback mechanism if YouTube blocks standard extraction
        return jsonify({
            "error": f"Extraction blocked by YouTube signature rules. Please ensure cookies.txt is updated or try another video. Details: {error_msg}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
