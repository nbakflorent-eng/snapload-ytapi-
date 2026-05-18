from flask import Flask, request, jsonify
import subprocess, json, urllib.request, urllib.parse

app = Flask(__name__)

@app.after_request
def cors(r):
    r.headers['Access-Control-Allow-Origin'] = '*'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return r

@app.route('/')
def health():
    return jsonify({'status': 'ok', 'version': '6.0'})

UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'

def ytdlp(url):
    cmd = [
        'yt-dlp', '--dump-json', '--no-playlist',
        '--format', 'best',
        '--no-warnings', '--no-check-certificates',
        '--user-agent', UA,
        '--add-headers', 'Accept-Language:fr-FR,fr;q=0.9',
        url
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    if r.returncode != 0:
        lines = [l for l in r.stderr.strip().split('\n') if l]
        raise Exception(lines[-1] if lines else 'yt-dlp error')
    d = json.loads(r.stdout)
    dl_url = d.get('url', '')
    if not dl_url:
        raise Exception('No URL found')
    return {
        'title': d.get('title', 'Video'),
        'thumbnail': d.get('thumbnail', ''),
        'duration': d.get('duration'),
        'formats': [{'type': 'video', 'quality': 'HD', 'ext': 'mp4', 'url': dl_url}],
        'url': dl_url
    }

def get_tiktok(url, quality):
    body = urllib.parse.urlencode({'url': url, 'hd': '1', 'web': '1', 'count': '12', 'cursor': '0'}).encode()
    req = urllib.request.Request('https://www.tikwm.com/api/', data=body, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    req.add_header('User-Agent', UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read().decode())
    if d.get('code') != 0:
        raise Exception(d.get('msg', 'TikTok error'))
    data = d['data']
    base = 'https://www.tikwm.com'
    video_url = (base + data['hdplay']) if data.get('hdplay') else ((base + data['play']) if data.get('play') else None)
    audio_url = data.get('music_info', {}).get('play') or data.get('music')
    formats = []
    if quality == 'mp3':
        if audio_url: formats.append({'type': 'audio', 'quality': 'Audio MP3', 'ext': 'mp3', 'url': audio_url})
    else:
        if video_url: formats.append({'type': 'video', 'quality': 'HD 1080p', 'ext': 'mp4', 'url': video_url})
        if audio_url: formats.append({'type': 'audio', 'quality': 'Audio MP3', 'ext': 'mp3', 'url': audio_url})
    if not formats: raise Exception('No TikTok formats')
    return {'title': data.get('title', 'TikTok'), 'thumbnail': data.get('cover', ''), 'duration': data.get('duration'), 'formats': formats, 'url': formats[0]['url']}

@app.route('/info')
def info():
    url = request.args.get('url', '')
    quality = request.args.get('quality', '1080')
    if not url: return jsonify({'error': 'Missing url'}), 400
    try:
        if 'tiktok.com' in url:
            return jsonify(get_tiktok(url, quality))
        # Instagram, Twitter, Pinterest, Facebook via yt-dlp
        return jsonify(ytdlp(url))
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 422

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
