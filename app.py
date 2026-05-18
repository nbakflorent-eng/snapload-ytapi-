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
    return jsonify({'status': 'ok', 'version': '5.0'})

def fetch_url(url, method='GET', data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    req.add_header('User-Agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def get_tiktok(url):
    body = urllib.parse.urlencode({'url': url, 'hd': '1', 'web': '1', 'count': '12', 'cursor': '0'}).encode()
    d = fetch_url('https://www.tikwm.com/api/', method='POST', data=body,
                  headers={'Content-Type': 'application/x-www-form-urlencoded'})
    if d.get('code') != 0:
        raise Exception(d.get('msg', 'TikTok error'))
    data = d['data']
    base = 'https://www.tikwm.com'
    video_url = base + data['hdplay'] if data.get('hdplay') else (base + data['play'] if data.get('play') else None)
    audio_url = data.get('music_info', {}).get('play') or data.get('music')
    formats = []
    if video_url: formats.append({'type': 'video', 'quality': 'HD 1080p', 'ext': 'mp4', 'url': video_url})
    if audio_url: formats.append({'type': 'audio', 'quality': 'Audio MP3', 'ext': 'mp3', 'url': audio_url})
    return {'title': data.get('title', 'TikTok'), 'thumbnail': data.get('cover', ''), 'duration': data.get('duration'), 'formats': formats, 'url': formats[0]['url'] if formats else None}

def get_instagram(url):
    api_url = 'https://snapinsta.app/api/ajaxSearch'
    body = urllib.parse.urlencode({'q': url, 't': 'media', 'lang': 'en'}).encode()
    d = fetch_url(api_url, method='POST', data=body,
                  headers={'Content-Type': 'application/x-www-form-urlencoded', 'Referer': 'https://snapinsta.app/'})
    if not d.get('data'):
        raise Exception('Instagram: no data')
    import re
    urls = re.findall(r'href="(https://[^"]+\.mp4[^"]*)"', d['data'])
    if not urls:
        raise Exception('No video URL found')
    formats = [{'type': 'video', 'quality': 'HD', 'ext': 'mp4', 'url': urls[0]}]
    return {'title': 'Video Instagram', 'thumbnail': '', 'duration': None, 'formats': formats, 'url': urls[0]}

def get_twitter(url):
    # Use twitsave
    api_url = 'https://twitsave.com/info?url=' + urllib.parse.quote(url)
    req = urllib.request.Request(api_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode()
    import re
    urls = re.findall(r'https://video\.twimg\.com/[^"\'> ]+\.mp4[^"\'> ]*', html)
    if not urls:
        raise Exception('No Twitter video found')
    formats = [{'type': 'video', 'quality': 'HD', 'ext': 'mp4', 'url': urls[0]}]
    return {'title': 'Video Twitter', 'thumbnail': '', 'duration': None, 'formats': formats, 'url': urls[0]}

def get_pinterest(url):
    api_url = 'https://www.pinterestdownloader.io/?url=' + urllib.parse.quote(url)
    req = urllib.request.Request(api_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    req.add_header('Referer', 'https://www.pinterestdownloader.io/')
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode()
    import re
    urls = re.findall(r'https://v1\.pinimg\.com/[^"\'> ]+\.mp4[^"\'> ]*', html)
    if not urls:
        raise Exception('No Pinterest video found')
    formats = [{'type': 'video', 'quality': 'HD', 'ext': 'mp4', 'url': urls[0]}]
    return {'title': 'Video Pinterest', 'thumbnail': '', 'duration': None, 'formats': formats, 'url': urls[0]}

def get_facebook(url):
    # Use yt-dlp for Facebook
    result = subprocess.run(
        ['yt-dlp', '--dump-json', '--no-playlist', '--format', 'best', '--no-warnings', url],
        capture_output=True, text=True, timeout=25
    )
    if result.returncode != 0:
        raise Exception(result.stderr.split('\n')[-2] if result.stderr else 'Facebook error')
    data = json.loads(result.stdout)
    dl_url = data.get('url', '')
    if not dl_url: raise Exception('No URL')
    formats = [{'type': 'video', 'quality': 'HD', 'ext': 'mp4', 'url': dl_url}]
    return {'title': data.get('title', 'Facebook'), 'thumbnail': data.get('thumbnail', ''), 'duration': data.get('duration'), 'formats': formats, 'url': dl_url}

@app.route('/info')
def info():
    url = request.args.get('url', '')
    quality = request.args.get('quality', '1080')
    if not url: return jsonify({'error': 'Missing url'}), 400
    try:
        if 'tiktok.com' in url: return jsonify(get_tiktok(url))
        if 'instagram.com' in url: return jsonify(get_instagram(url))
        if 'twitter.com' in url or 'x.com' in url: return jsonify(get_twitter(url))
        if 'pinterest.com' in url or 'pin.it' in url: return jsonify(get_pinterest(url))
        if 'facebook.com' in url or 'fb.watch' in url: return jsonify(get_facebook(url))
        return jsonify({'error': 'Plateforme non supportee'}), 400
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 422

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
