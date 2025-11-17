from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
from gtts import gTTS
import shutil
import time
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# STATIC (READ-ONLY ON VERCEL)
PUBLIC_AUDIO_FOLDER = 'static/audio'
os.makedirs(PUBLIC_AUDIO_FOLDER, exist_ok=True)

# SERVERLESS TEMP STORAGE (READ/WRITE)
TEMP_FOLDER = '/tmp/audio'
os.makedirs(TEMP_FOLDER, exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        timestamp = int(time.time() * 1000)
        filename = f"output_{timestamp}.mp3"

        temp_path = os.path.join(TEMP_FOLDER, filename)

        # Convert Text → Audio
        tts = gTTS(text=text, lang='en')
        tts.save(temp_path)

        # Try copying for local dev (static/audio is read-only on Vercel)
        try:
            shutil.copy(temp_path, os.path.join(PUBLIC_AUDIO_FOLDER, filename))
        except:
            pass

        flash("Audio created successfully!", "success")
        return redirect(url_for("index", new_audio=filename))

    # LIST FILES FROM /tmp (SERVERLESS)
    try:
        files = sorted(os.listdir(TEMP_FOLDER), reverse=True)
    except:
        files = []

    new_audio = request.args.get("new_audio")
    return render_template("index.html", audio_file=new_audio, files=files)


# Serve audio files from /tmp
@app.route('/audio/<filename>')
def audio(filename):
    return send_from_directory(TEMP_FOLDER, filename)


@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    temp_path = os.path.join(TEMP_FOLDER, filename)

    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            flash("Deleted successfully!", "success")
        else:
            flash("File not found.", "danger")
    except Exception as e:
        flash(f"Error deleting file: {e}", "danger")

    return redirect(url_for("index"))


if __name__ == '__main__':
    app.run(debug=True)