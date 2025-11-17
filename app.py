from flask import Flask, request, render_template, send_from_directory, flash
from gtts import gTTS
import time
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

TEMP_FOLDER = '/tmp/audio'
os.makedirs(TEMP_FOLDER, exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    new_audio = None

    if request.method == 'POST':
        text = request.form['text']
        timestamp = int(time.time() * 1000)
        filename = f"output_{timestamp}.mp3"

        filepath = os.path.join(TEMP_FOLDER, filename)

        # Generate audio into /tmp
        tts = gTTS(text=text, lang='en')
        tts.save(filepath)

        flash("Audio created successfully!", "success")
        new_audio = filename  # keep it in same request

    # LIST CURRENT FILES (this request sees them!)
    try:
        files = sorted(os.listdir(TEMP_FOLDER), reverse=True)
    except:
        files = []

    return render_template("index.html", audio_file=new_audio, files=files)


@app.route('/audio/<filename>')
def audio(filename):
    return send_from_directory(TEMP_FOLDER, filename)


@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    filepath = os.path.join(TEMP_FOLDER, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        flash("File deleted successfully!", "success")
    else:
        flash("File not found.", "danger")

    # Render again without redirect (important!)
    try:
        files = sorted(os.listdir(TEMP_FOLDER), reverse=True)
    except:
        files = []

    return render_template("index.html", audio_file=None, files=files)


if __name__ == '__main__':
    app.run(debug=True)