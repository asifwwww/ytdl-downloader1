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

    # Using iOS client emulation which bypasses YouTube bot walls completely
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,
        'format': 'best',
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web']
            }
        },
        'user_agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU OS 17_5_1 like Mac OS X)',
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
        return jsonify({"error": f"Extraction error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
