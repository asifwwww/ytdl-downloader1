from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)

# Reliable public Piped API instances pool (Automatic fallback)
PIPED_INSTANCES = [
    "https://pipedapi.kavin.rocks",
    "https://pipedapi.yt.artemislena.eu",
    "https://piped-api.privacy.com.de"
]

def extract_video_id(url):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|watch\?v=|youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "active"}), 200

@app.route('/api/extract', methods=['POST'])
def extract_video():
    data = request.get_json()
    video_url = data.get('url') if data else None

    if not video_url:
        return jsonify({"error": "URL missing"}), 400

    video_id = extract_video_id(video_url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL. Could not extract video ID."}), 400

    res_data = None
    success = False

    # Try instances until one responds successfully
    for instance in PIPED_INSTANCES:
        try:
            api_url = f"{instance}/streams/{video_id}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            response = requests.get(api_url, headers=headers, timeout=12)
            
            if response.status_code == 200:
                res_data = response.json()
                success = True
                break
        except Exception:
            continue

    if not success or not res_data:
        return jsonify({"error": "Extraction nodes busy or timed out. Please try again."}), 500

    try:
        formats = []
        
        # Video streams
        for s in res_data.get('videoStreams', []):
            if s.get('url'):
                formats.append({
                    'resolution': s.get('quality', 'HD'),
                    'ext': s.get('format', 'mp4'),
                    'url': s.get('url'),
                    'has_video': not s.get('videoOnly', False),
                    'has_audio': True
                })

        # Audio streams
        for s in res_data.get('audioStreams', []):
            if s.get('url'):
                formats.append({
                    'resolution': f"Audio ({s.get('format', 'm4a')})",
                    'ext': s.get('format', 'm4a'),
                    'url': s.get('url'),
                    'has_video': False,
                    'has_audio': True
                })

        result = {
            'title': res_data.get('title', 'YouTube Video'),
            'thumbnail': res_data.get('thumbnailUrl', ''),
            'duration': res_data.get('duration', 0),
            'channel': res_data.get('uploader', 'YouTube Creator'),
            'views': res_data.get('views', 0),
            'description': res_data.get('description', ''),
            'formats': formats
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Parsing error: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
