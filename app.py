from flask import Flask, request, render_template, send_from_directory, redirect, url_for, flash
from gtts import gTTS
import time
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

AUDIO_FOLDER = 'static/audio'

if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form['text']
        timestamp = int(time.time() * 1000)
        filename = f"output_{timestamp}.mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        tts = gTTS(text=text, lang='en')
        tts.save(filepath)
        flash('Audio created successfully!', 'success')

        # Redirect to GET after POST-processing
        return redirect(url_for('index', new_audio=filename))  # Pass new file via query param

    # Handle GET request
    new_audio = request.args.get('new_audio')
    files = sorted(os.listdir(AUDIO_FOLDER), reverse=True)
    return render_template('index.html', audio_file=new_audio, files=files)

@app.route('/audio/<filename>')
def audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    filepath = os.path.join(AUDIO_FOLDER, filename)
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f"Deleted {filename}", "success")
        else:
            flash("File does not exist.", "warning")
    except Exception as e:
        flash(f"Error deleting file: {str(e)}", "danger")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
