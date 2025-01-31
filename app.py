from flask import Flask, render_template, request, jsonify
from io import BytesIO
from processing import get_data

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        try:
            file_stream = BytesIO(file.read())
            row_count = get_data(file_stream, file.filename)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
        return jsonify({'rows': row_count})
    
    return jsonify({'error': 'File upload failed'}), 400

if __name__ == '__main__':
    app.run(debug=True)
