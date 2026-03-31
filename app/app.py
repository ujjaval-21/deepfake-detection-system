from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import uuid
from werkzeug.utils import secure_filename
from database import init_db
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
from detectors.detect_image import analyze_image
from detectors.detect_video import analyze_video


app = Flask(__name__)
app.secret_key = "UjjavalYadav@21"

init_db()

# PATH SETUP
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# SERVE UPLOADED FILES
@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# FILE TYPE CONFIG
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# NAVIGATION ROUTES
@app.route('/')
def landing_page():
    return render_template('index.html')

from flask import session

@app.route('/select')
def select_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('select.html')

@app.route('/image')
def image_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('image.html')

@app.route('/video')
def video_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('video.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# LOGIN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        from database import get_db
        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            return redirect(url_for('select_page'))
        else:
            return render_template('login.html', error="Invalid Credentials")

    return render_template('login.html')


#signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        hashed_password = generate_password_hash(password)

        from database import get_db
        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            return redirect(url_for('login'))

        except:
            return render_template('signup.html', error="Username already exists")

    return render_template('signup.html')


@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    rows = conn.execute(
        "SELECT filename, result, confidence, filetype, created_at FROM history WHERE username=? ORDER BY created_at DESC",
        (session['user'],)
    ).fetchall()

    conn.close()

    return render_template('history.html', rows=rows)



# IMAGE DETECTION
@app.route('/detect-image', methods=['POST'])
def detect_image():

    file = request.files.get('image')

    if not file or file.filename == "":
        return "❌ No image uploaded"

    if not allowed_file(file.filename, IMAGE_EXTENSIONS):
        return "❌ Only Image files (JPG, PNG) allowed!"

    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(image_path)

    label, confidence, metadata = analyze_image(image_path)
    
    username = session.get('user')

    if username:
        conn = get_db()
        conn.execute(
            "INSERT INTO history (username, filename, result, confidence, filetype) VALUES (?, ?, ?, ?, ?)",
            (username, filename, label, confidence, "image")
        )
        conn.commit()
        conn.close()


    return render_template(
        'result.html',
        result=label,
        prob=confidence,
        metadata=metadata,
        filename=filename,
        filetype="image"
    )
    


# VIDEO DETECTION
@app.route('/detect-video', methods=['POST'])
def detect_video():

    file = request.files.get('video')

    if not file or file.filename == "":
        return "❌ No video uploaded"

    if not allowed_file(file.filename, VIDEO_EXTENSIONS):
        return "❌ Only Video files (MP4, AVI, MOV) allowed!"

    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    file.save(video_path)

    label, confidence, metadata, converted_path = analyze_video(video_path)
    converted_filename = os.path.basename(converted_path)
    video_url = url_for('serve_uploaded_file', filename=converted_filename)

    username = session.get('user')

    if username:
        conn = get_db()
        conn.execute(
            "INSERT INTO history (username, filename, result, confidence, filetype) VALUES (?, ?, ?, ?, ?)",
            (username, filename, label, confidence, "video")
        )
        conn.commit()
        conn.close()

    return render_template(
        'result.html',
        result=label,
        prob=confidence,
        metadata=metadata,
        video_url=video_url,
        filetype="video"
    )


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True, port=3002)