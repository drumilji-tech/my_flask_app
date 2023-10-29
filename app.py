# app.py

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import boto3
from botocore.exceptions import NoCredentialsError

app = Flask(__name__)

# S3 configuration
S3_BUCKET_NAME = 'my-dtjoshi-bucket'
AWS_ACCESS_KEY_ID = 'AKIA4DBCY2MVCOJPNV4K'
AWS_SECRET_ACCESS_KEY = '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'
S3_REGION = 'us-east-1'

# MySQL configuration (uses Amazon RDS)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Local directory for file uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<User {self.name}>'

def upload_to_s3(file, bucket_name, object_name=None):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=S3_REGION)
    try:
        s3.upload_file(file, bucket_name, object_name or os.path.basename(file))
        return True
    except NoCredentialsError:
        print("AWS credentials not available.")
        return False

@app.route('/')
def index():
    # Fetch the list of uploaded files from S3 bucket
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=S3_REGION)
    response = s3.list_objects(Bucket=S3_BUCKET_NAME)
    uploaded_files = [obj['Key'] for obj in response.get('Contents', [])]

    return render_template('index.html', notes=User.query.all(), uploaded_files=uploaded_files)
    
    
@app.route('/add_note', methods=['POST'])
def add_note():
    note_content = request.form.get('note_content')
    notes.append(note_content)
    return redirect(url_for('index'))

@app.route('/edit_note/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if request.method == 'POST':
        if 0 <= note_id < len(notes):
            notes[note_id] = request.form.get('updated_note_content')
            return redirect(url_for('index'))
    elif 0 <= note_id < len(notes):
        return render_template('edit_note.html', note_id=note_id, note=notes[note_id])
    else:
        return redirect(url_for('index'))

@app.route('/delete_note/<int:note_id>')
def delete_note(note_id):
    if 0 <= note_id < len(notes):
        del notes[note_id]
    return redirect(url_for('index'))

# Other routes (add_note, edit_note, delete_note, user_details) remain unchanged

@app.route('/upload_file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # Upload the file to S3
        upload_to_s3(filename, S3_BUCKET_NAME)

        # Optionally, you can remove the local file after uploading to S3
        os.remove(filename)

    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
