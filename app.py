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
    return jsonify({'status': 'ok', 'version': '3.0'})

@app.route('/info')
def info():
    url = request.args.get('url', '')
    quality = request.args.get('quality', '1080')
    if not url:
        return jsonify({'error': 'Missing url'}), 400
    try:
        is_audio = quality == 'mp3'
        fmt = 'bestaudio/best' if is_audio else 'best'
        cmd = [
            'yt-dlp', '--dump-json', '--no-playlist',
            '--format', fmt, '--no-warnings', '--no-check-certificates',
            '--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) Appl
