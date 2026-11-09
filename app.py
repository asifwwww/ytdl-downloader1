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

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
        # Only fetch formats that have both video and audio combined (No ffmpeg needed)
        'format': 'best[ext=mp4]/best',
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'tv']
            }
        },
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }

    # Optional: If cookies.txt exists in root directory
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            formats_data = []
            for fmt in info.get('formats', []):
                # Only include streams that have direct URLs and both video + audio
                if fmt.get('url') and fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                    formats_data.append({
                        'resolution': fmt.get('format_note') or fmt.get('resolution') or f"{fmt.get('height')}p",
                        'ext': fmt.get('ext', 'mp4'),
                        'url': fmt.get('url'),
                        'has_video': True,
                        'has_audio': True
                    })

            # Fallback if filtered list is empty
            if not formats_data and info.get('url'):
                formats_data.append({
                    'resolution': 'HD',
                    'ext': 'mp4',
                    'url': info.get('url'),
                    'has_video': True,
                    'has_audio': True
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
        return jsonify({"error": f"Extraction error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
