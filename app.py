from flask import Flask, request, jsonify
import subprocess, json

app = Flask(__name__)

@app.after_request
def cors(r):
    r.headers['Access-Control-Allow-Origin'] = '*'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return r

@app.route('/')
def health():
    return jsonify({'status': 'ok', 'version': '4.0'})

@app.route('/info')
def info():
    url = request.args.get('url', '')
    quality = request.args.get('quality', '1080')
    if not url:
        return jsonify({'error': 'Missing url'}), 400
    try:
        is_audio = quality == 'mp3'
        fmt = 'bestaudio/best' if is_audio else 'best'
        ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)'
        cmd = [
            'yt-dlp', '--dump-json', '--no-playlist',
            '--format', fmt, '--no-warnings',
            '--no-check-certificates',
            '--user-agent', ua,
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if result.returncode != 0:
            lines = result.stderr.strip().split('\n')
            err = lines[-1] if lines else 'Unknown error'
            return jsonify({'error': err[:200]}), 422
        data = json.loads(result.stdout)
        dl_url = data.get('url', '')
        if not dl_url:
            return jsonify({'error': 'No URL found'}), 422
        label = {'mp3': 'Audio MP3', '4k': '4K UHD', '8k': '8K MAX'}.get(quality, 'HD 1080p')
        ftype = 'audio' if is_audio else 'video'
        ext = 'mp3' if is_audio else 'mp4'
        formats = [{'type': ftype, 'quality': label, 'ext': ext, 'url': dl_url}]
        return jsonify({
            'title': data.get('title', 'Video'),
            'thumbnail': data.get('thumbnail', ''),
            'duration': data.get('duration'),
            'formats': formats,
            'url': dl_url
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout'}), 422
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 422

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
