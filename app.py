import chardet
import pandas as pd
from flask import Flask, render_template, request, jsonify
from io import BytesIO
from abstracted.processing import process_data

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
            file_extension = file.filename.split('.')[-1].lower()

            # Handle different file formats
            if file_extension in ['xls', 'xlsx']:
                df_input = pd.read_excel(file_stream)  # Read Excel file
            elif file_extension in ['csv', 'tsv']:
                file_stream.seek(0)  # Reset stream position
                
                # Auto-detect encoding
                raw_data = file_stream.read(10000)
                detected_encoding = chardet.detect(raw_data)['encoding']
                file_stream.seek(0)

                delimiter = ',' if file_extension == 'csv' else '\t'  # CSV or TSV handling
                df_input = pd.read_csv(file_stream, encoding=detected_encoding or 'utf-8', delimiter=delimiter)
            else:
                return jsonify({'error': 'Unsupported file format'}), 400

            # Get max_rows from form data (default to 20)
            max_rows = request.form.get('count', 20)
            max_rows = int(max_rows)
            if max_rows < 0:
                max_rows = 100000

            # Process the data
            df = process_data(df_input, max_rows=max_rows, gene_limit=100, max_workers=100)

            # Fill missing gene_id values
            df['gene_id'] = df['gene_id'].fillna("N/A").astype(str)
            df['Normalized_Read_Counts'] = df['Normalized_Read_Counts'].fillna(0).astype(int)

            return jsonify({
                'rows': len(df),
                'top_data': df[['gene_id', 'Normalized_Read_Counts']].to_dict(orient='records')
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 400

    return jsonify({'error': 'File upload failed'}), 400

if __name__ == '__main__':
    app.run(debug=True)
