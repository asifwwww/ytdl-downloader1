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
        # High-speed reliable extraction bridge request
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        payload = {
            "url": video_url
        }
        
        response = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=20)
        res_data = response.json()

        if response.status_code == 200 and res_data.get("status") in ["stream", "redirect", "picker"]:
            formats = []
            
            # Handle multiple qualities / picker options
            if res_data.get("status") == "picker":
                for item in res_data.get("picker", []):
                    formats.append({
                        'resolution': item.get('type', 'HD'),
                        'ext': 'mp4',
                        'url': item.get('url'),
                        'has_video': True,
                        'has_audio': True
                    })
            elif res_data.get("url"):
                formats.append({
                    'resolution': 'HD',
                    'ext': 'mp4',
                    'url': res_data.get('url'),
                    'has_video': True,
                    'has_audio': True
                })

            result = {
                'title': res_data.get('filename', 'YouTube Video'),
                'thumbnail': res_data.get('thumbnail', ''),
                'duration': 0,
                'channel': 'YouTube',
                'views': 0,
                'description': '',
                'formats': formats
            }
            return jsonify(result), 200
        else:
            err_text = res_data.get("text") or res_data.get("error") or "Extraction failed."
            return jsonify({"error": err_text}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
