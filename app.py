from flask import Flask, request, render_template, redirect, url_for, flash
from gtts import gTTS
from supabase import create_client
from dotenv import load_dotenv
import os
import io
import time

# Load .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "supersecretkey")

# Supabase config (set these in your .env or environment)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET = os.environ.get("SUPABASE_BUCKET", "audio")  # default: audio


def list_storage_files():
    """
    Fetch list of objects from Supabase Storage and return a list sorted newest-first if possible.
    Each item: {"name": ..., "url": ... , "created_at": ... (optional)}
    """
    try:
        objs = supabase.storage.from_(BUCKET).list()
    except Exception as e:
        # Return empty list and flash error from caller
        return None, str(e)

    files = []
    for o in objs:
        # o typically contains keys such as "name", maybe "updated_at"/"created_at"
        name = o.get("name") if isinstance(o, dict) else str(o)
        # Build public url (the SDK method typically returns a dict or string depending on version)
        try:
            public = supabase.storage.from_(BUCKET).get_public_url(name)
            # get_public_url may return a dict like {"publicUrl": "..."} or a string.
            if isinstance(public, dict):
                url = public.get("publicUrl") or public.get("public_url") or ""
            else:
                url = public
        except Exception:
            url = ""

        created_at = o.get("created_at") or o.get("updated_at") or None
        files.append({"name": name, "url": url, "created_at": created_at})

    # Try to sort by created_at/updated_at if available, else by filename (assuming timestamp in name)
    def sort_key(x):
        if x["created_at"]:
            return x["created_at"]
        # fallback: use filename (timestamps in filename like output_123456789)
        return x["name"]

    try:
        files.sort(key=sort_key, reverse=True)
    except Exception:
        # fallback: no sorting
        pass

    return files, None


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if not text:
            flash("Text cannot be empty.", "error")
            return redirect(url_for("index"))

        filename = f"output_{int(time.time() * 1000)}.mp3"

        # Generate mp3 in memory
        buffer = io.BytesIO()
        try:
            tts = gTTS(text=text, lang="en")
            tts.write_to_fp(buffer)
            buffer.seek(0)
        except Exception as e:
            flash(f"Failed to generate audio: {e}", "error")
            return redirect(url_for("index"))

        # Upload bytes to Supabase Storage
        try:
            result = supabase.storage.from_(BUCKET).upload(
                path=filename,
                file=buffer.getvalue(),
                file_options={"content-type": "audio/mpeg"},
            )
        except Exception as e:
            flash(f"Upload failed: {e}", "error")
            return redirect(url_for("index"))

        # Some SDK versions return dict with "error" key, some raise exceptions — handle both
        if isinstance(result, dict) and result.get("error"):
            flash(f"Upload failed: {result.get('error')}", "error")
        else:
            flash("Audio uploaded to storage successfully!", "success")

        return redirect(url_for("index"))

    # GET: list files from storage
    files, err = list_storage_files()
    if err:
        flash(f"Could not list storage files: {err}", "error")
        files = []

    return render_template("index.html", files=files)


@app.route("/delete/<path:filename>", methods=["POST"])
def delete(filename):
    if not filename:
        flash("Filename required", "error")
        return redirect(url_for("index"))

    try:
        result = supabase.storage.from_(BUCKET).remove([filename])
    except Exception as e:
        flash(f"Delete failed: {e}", "error")
        return redirect(url_for("index"))

    # SDK might return dict with "error" key or an empty list/object on success
    if isinstance(result, dict) and result.get("error"):
        flash(f"Delete failed: {result.get('error')}", "error")
    else:
        flash(f"Deleted {filename} from storage.", "success")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)