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
    return jsonify({'status': 'ok', 'version': '2.0'})

@app.route('/info')
def info():
    url = request.args.get('url', '')
    quality = request.args.get('quality', '1080')
    if not url:
        return jsonify({'error': 'Missing url'}), 400
    try:
        is_tiktok = 'tiktok.com' in url
        is_audio = quality == 'mp3'
        fmt = 'bestaudio/best' if is_audio else ('bestvideo[height<=2160]+bestaudio/best' if quality == '4k' else 'bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]/best')
        cmd = ['yt-dlp', '--dump-json', '--no-playlist', '--format', fmt, '--no-warnings', '--no-check-certificates', '--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15']
        if is_tiktok:
            cmd += ['--extractor-args', 'tiktok:api_hostname=api22-normal-c-useast2a.tiktokv.com']
        cmd.append(url)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if result.returncode != 0:
            return jsonify({'error': 'Impossible de récupérer cette vidéo.'}), 422
        data = json.loads(result.stdout)
        dl_url = data.get('url', '')
        label = {'1080': 'HD 1080p', '4k': '4K UHD', '8k': '8K MAX', 'mp3': 'Audio MP3'}.get(quality, 'HD 1080p')
        ftype = 'audio' if is_audio else 'video'
        ext = 'mp3' if is_audio else 'mp4'
        formats = [{'type': ftype, 'quality': label, 'ext': ext, 'url': dl_url}] if dl_url else []
        if not is_audio and dl_url:
            a = subprocess.run(cmd[:-2] + ['--format', 'bestaudio/best', url], capture_output=True, text=True, timeout=15)
            if a.returncode == 0:
                au = json.loads(a.stdout).get('url', '')
                if au and au != dl_url:
                    formats.append({'type': 'audio', 'quality': 'Audio MP3', 'ext': 'mp3', 'url': au})
        if not formats:
            return jsonify({'error': 'Aucun format disponible.'}), 422
        return jsonify({'title': data.get('title', 'Vidéo'), 'thumbnail': data.get('thumbnail', ''), 'duration': data.get('duration'), 'formats': formats, 'url': formats[0]['url']})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout — réessaie.'}), 422
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 422

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
