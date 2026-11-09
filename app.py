from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

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

    try:
        # Using a reliable public multi-extractor endpoint
        api_url = f"https://tikwm.com/api/?url={video_url}"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(api_url, headers=headers, timeout=25)
        
        if not response.text or not response.text.strip():
            return jsonify({"error": "Server returned empty response."}), 500

        try:
            res_data = response.json()
        except Exception:
            return jsonify({"error": "Failed to parse API response."}), 500

        # Universal fallback extraction formatting for YouTube / Social media
        if res_data.get("code") == 0 and "data" in res_data:
            v_data = res_data["data"]
            formats = []
            
            if v_data.get("play"):
                formats.append({
                    'resolution': 'HD',
                    'ext': 'mp4',
                    'url': v_data.get('play'),
                    'has_video': True,
                    'has_audio': True
                })
            
            if v_data.get("music"):
                formats.append({
                    'resolution': 'Audio (.mp3)',
                    'ext': 'mp3',
                    'url': v_data.get('music'),
                    'has_video': False,
                    'has_audio': True
                })

            result = {
                'title': v_data.get('title', 'Downloaded Media'),
                'thumbnail': v_data.get('cover', ''),
                'duration': v_data.get('duration', 0),
                'channel': v_data.get('author', {}).get('nickname', 'Creator'),
                'views': v_data.get('play_count', 0),
                'description': '',
                'formats': formats
            }
            return jsonify(result), 200
        else:
            # Fallback to direct cobalt alternative if needed, or return clear error
            return jsonify({"error": "Could not extract video details from this link. Try another YouTube link."}), 500

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
