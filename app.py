from flask import Flask, render_template, request, jsonify
from io import BytesIO
import pandas as pd
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
            df = get_data(file_stream, file.filename)  # Get the DataFrame
            
            # Rename first two columns
            if df.shape[1] < 2:
                return jsonify({'error': 'File must contain at least two columns'}), 400
            
            df.columns = ['gene_id', 'count'] + list(df.columns[2:])  # Rename first two columns
            
            if 'count' in df.columns:
                df = df.sort_values(by='count', ascending=False)  # Sort by "count" column
                top_20 = df[['gene_id', 'count']].head(20).to_dict(orient='records')  # Get top 20 rows
            else:
                return jsonify({'error': 'No "count" column found in the data'}), 400
            
            return jsonify({'rows': len(df), 'top_data': top_20})
        
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return jsonify({'error': 'File upload failed'}), 400

if __name__ == '__main__':
    app.run(debug=True)
