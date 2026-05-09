from flask import Flask, request, jsonify
from pytubefix import YouTube

app = Flask(__name__)

@app.route('/')
def health():
    return jsonify({'status': 'ok'})

@app.route('/info')
def info():
    url = request.args.get('url', '')
    quality = request.args.get('quality', '1080')
    if not url:
        return jsonify({'error': 'Missing url'}), 400
    try:
        yt = YouTube(url)
        formats = []
        if quality == 'mp3':
            audio = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if audio:
                formats.append({'type': 'audio', 'quality': 'Audio MP3', 'ext': 'mp3', 'url': audio.url})
        else:
            prog = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            if prog:
                label = {'1080': 'HD 1080p', '4k': '4K UHD', '8k': '8K MAX'}.get(quality, 'HD 1080p')
                formats.append({'type': 'video', 'quality': label, 'ext': 'mp4', 'url': prog.url})
            audio = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if audio:
                formats.append({'type': 'audio', 'quality': 'Audio MP3', 'ext': 'mp3', 'url': audio.url})
        return jsonify({'title': yt.title, 'thumbnail': yt.thumbnail_url, 'duration': yt.length, 'formats': formats, 'url': formats[0]['url'] if formats else None})
    except Exception as e:
        return jsonify({'error': str(e)}), 422

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
