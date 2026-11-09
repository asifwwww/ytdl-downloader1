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
        # Using public cobalt tools api endpoint directly
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        payload = {
            "url": video_url,
            "vQuality": "max",
            "dubLang": False
        }
        
        response = requests.post("https://co.wuk.sh/api/json", json=payload, headers=headers, timeout=25)
        
        if not response.text or not response.text.strip():
            return jsonify({"error": "Server returned empty response."}), 500

        try:
            res_data = response.json()
        except Exception:
            return jsonify({"error": "Failed to parse extraction response."}), 500

        status = res_data.get("status")
        
        if status in ["stream", "redirect", "picker"]:
            formats = []
            
            if status == "picker":
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
            err_text = res_data.get("text") or res_data.get("error") or "Extraction failed by upstream API."
            return jsonify({"error": err_text}), 500

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
