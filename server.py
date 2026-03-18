from flask import Flask, request, render_template, send_from_directory
from secrets import token_hex
from time import time
from os import remove
import shelve

app = Flask(__name__)

DAY = 86400
WEEK = 604800
MONTH = 2628000
NEVER = -1.0
MAX_SIZE = 2147483648 #2gb

@app.route("/")
def index():
    return render_template("index.html")
    
def update_database(filename, expiry_seconds):
    file_id = token_hex(32)
    db = shelve.open("database.gnu", "c")
    if expiry_seconds > 0:
        db[file_id] = (filename, str(time()+expiry_seconds))
    else:
        db[file_id] = (filename, "-1.0")
    db.close()
    return file_id

@app.route("/upload", methods=["POST"])
def upload_file():
        
    expiry_secs = MONTH #month is default if user didnt select anything
    if "upload" not in request.files:
        return "No file part", 400
    file = request.files["upload"]
    expiry_choice = request.form.get('expiry')
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if file.filename == "":
        return "No selected file", 400
    if size > MAX_SIZE:
        return "Apparently, you can't read '<2gb'"
    file.save("uploads//"+file.filename)
    
    match expiry_choice:
        case "1d":
            expiry_secs = DAY
        case "7d":
            expiry_secs = WEEK
        case "30d":
            expiry_secs = MONTH
        case "never":
            expiry_secs = NEVER
    
    file_id = update_database(file.filename, expiry_secs)
    return f"http://127.0.0.1:5000/{file_id}"
    
@app.route('/<token>')
def download_file(token):
    filename = ""
    try:
        db = shelve.open("database.gnu", "c")
        filename = db[token][0]
        if float(db[token][1]) < time() and not db[token][1] == "-1.0":
            del db[token]
            return "Ewww... the link... it's all moldy and stale"
    except KeyError:
        return "404 file not found; the link may have expired, or may never have existed"
    finally:
        db.close()
  
    return send_from_directory("uploads", filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
