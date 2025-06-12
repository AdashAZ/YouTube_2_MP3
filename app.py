from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import yt_dlp
import re
import shutil
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Required for flash messages

# Download directory for PythonAnywhere
DOWNLOAD_DIR = Path('/home/' + os.environ.get('USERNAME', 'defaultuser') + '/youtube_downloads')
DOWNLOAD_DIR.mkdir(exist_ok=True)

VALID_FORMATS = ['mp3', 'wav', 'm4a', 'flac']
VALID_QUALITIES = ['128', '192', '256', '320']

def validate_url(url):
    """Validate if the input is a YouTube URL or playlist."""
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11}|playlist\?list=[\w-]+)'
    )
    return re.match(youtube_regex, url) is not None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        format_type = request.form.get('format')
        quality = request.form.get('quality')

        # Input validation
        if not url or not validate_url(url):
            flash('Invalid YouTube URL. Please provide a valid video or playlist URL.')
            return redirect(url_for('index'))
        if format_type not in VALID_FORMATS:
            flash(f'Invalid format. Choose from: {", ".join(VALID_FORMATS)}')
            return redirect(url_for('index'))
        if quality not in VALID_QUALITIES:
            flash(f'Invalid quality. Choose from: {", ".join(VALID_QUALITIES)}')
            return redirect(url_for('index'))

        # yt-dlp configuration
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_type,
                'preferredquality': quality,
            }],
            'noplaylist': False,  # Allow playlist downloads
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # For single video, return the downloaded file
                if 'entries' not in info:
                    filename = ydl.prepare_filename(info).replace('.webm', f'.{format_type}').replace('.m4a', f'.{format_type}')
                    return send_file(filename, as_attachment=True)
                else:
                    # For playlists, zip all files
                    zip_path = DOWNLOAD_DIR / 'playlist.zip'
                    shutil.make_archive(str(DOWNLOAD_DIR / 'playlist'), 'zip', DOWNLOAD_DIR)
                    return send_file(zip_path, as_attachment=True)
        except Exception as e:
            flash(f'Error during download: {str(e)}')
            return redirect(url_for('index'))

    return render_template('index.html', formats=VALID_FORMATS, qualities=VALID_QUALITIES)

if __name__ == '__main__':
    app.run(debug=True)
