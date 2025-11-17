from flask import Flask, request, render_template, send_file, redirect, url_for, flash
from gtts import gTTS
import time
import os
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Serverless-writable directory
TEMP_FOLDER = "/tmp/audio"

# Public directory for serving (read-only in serverless deployments)
PUBLIC_AUDIO_FOLDER = "static/audio"

# Create folders if running locally
os.makedirs(TEMP_FOLDER, exist_ok=True)
os.makedirs(PUBLIC_AUDIO_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        timestamp = int(time.time() * 1000)
        filename = f"output_{timestamp}.mp3"

        # Save to writable /tmp folder
        temp_path = os.path.join(TEMP_FOLDER, filename)
        tts = gTTS(text=text, lang='en')
        tts.save(temp_path)

        # Copy to static folder for browser access (only works locally)
        public_path = os.path.join(PUBLIC_AUDIO_FOLDER, filename)
        try:
            shutil.copy(temp_path, public_path)
        except:
            pass  # Ignore in Vercel (read-only static dir)

        flash('Audio created successfully!', 'success')

        return redirect(url_for('index', new_audio=filename))

    new_audio = request.args.get('new_audio')

    # List existing files (from static/audio or empty on serverless)
    try:
        files = sorted(os.listdir(PUBLIC_AUDIO_FOLDER), reverse=True)
    except:
        files = []

    return render_template('index.html', audio_file=new_audio, files=files)

@app.route('/audio/<filename>')
def audio(filename):
    """Serve file directly from /tmp (serverless safe)."""
    temp_path = os.path.join(TEMP_FOLDER, filename)
    if os.path.exists(temp_path):
        return send_file(temp_path, as_attachment=False)

    # Fallback for local static folder
    public_path = os.path.join(PUBLIC_AUDIO_FOLDER, filename)
    if os.path.exists(public_path):
        return send_file(public_path, as_attachment=False)

    return "File not found", 404

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    temp_path = os.path.join(TEMP_FOLDER, filename)
    public_path = os.path.join(PUBLIC_AUDIO_FOLDER, filename)

    deleted = False

    if os.path.exists(temp_path):
        os.remove(temp_path)
        deleted = True

    if os.path.exists(public_path):
        os.remove(public_path)
        deleted = True

    if deleted:
        flash(f"{filename} deleted successfully!", "success")
    else:
        flash("File not found.", "warning")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)