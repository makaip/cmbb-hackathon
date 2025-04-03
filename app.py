import chardet
import pandas as pd
from flask import Flask, render_template, request, jsonify
from io import BytesIO
from abstracted.processing import process_data
from connection import relationships_to_edges, export_edges_to_dict
from genai import Gemini
import json
from r_types import Relationship

app = Flask(__name__)
llm = Gemini()
llm.set_output(list[Relationship])


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    llm.set_initial_prompt('''return any relationships between the genes below described by (1) "
                        their shared biological processes, molecular functions, and cellular components and (2) any relationship identified by recent research studies (Indicate RS for relation_type if criteria 2 is the case).  ''')
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
            df = process_data(df_input, max_rows=max_rows, gene_limit=100, max_workers=25)

            # Fill missing gene_id values
            df['ncbi_gene_id'] = df['ncbi_gene_id'].fillna("N/A").astype(str)
            df['Normalized_Read_Counts'] = df['Normalized_Read_Counts'].fillna(0).astype(int)


            try:
                relationships = llm.prompt(df.to_string())
                if not relationships:  # Check if result is empty
                    return jsonify({'error': 'LLM returned no relationships'}), 400
                if isinstance(relationships, str):
                    try:
                        # Clean up the relationships string by dropping first and last line
                        if isinstance(relationships, str):
                            relationships = json.loads(relationships)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, keep it as is
                        print("Invalid JSON")
                        return jsonify({'error': 'Gemini returned invalid JSON'}), 400
                
            except Exception as e:
                return jsonify({'error': f'LLM processing error: {str(e)}'}), 400
            edges, nodes_dict = relationships_to_edges(relationships)
            # Print or process node information
            for node_id, node_data in nodes_dict.items():
                # Get the matching row and access the symbol column if it exists
                matching_row = df[df['Geneid'] == node_id]
                if not matching_row.empty and 'symbol' in matching_row.columns:
                    
                    nodes_dict[node_id].label = matching_row['symbol'].iloc[0]

                    if 'summary' in matching_row.columns and not pd.isna(matching_row['summary'].iloc[0]) and matching_row['summary'].iloc[0] != '':
                        summary = matching_row['summary'].iloc[0]
                        if isinstance(summary, list) and len(summary) > 0 and 'description' in summary[0]:
                            nodes_dict[node_id].description = summary[0]['description']
                        else:
                            nodes_dict[node_id].description = str(summary) if summary else "No description available"
                    else:
                        # Prompt Gemini for a description
                        llm.set_initial_prompt("Generate a description for this gene")
                        nodes_dict[node_id].description = llm.prompt(str(matching_row.iloc[0].to_dict()))
                else:
                    print("Empty!")
                    nodes_dict[node_id].label = node_id  # Default to gene_id if symbol not found
                  # This will print the object's attributes as a dictionary
                
                # You can access specific node properties if available
                # For example: if 'name' in node_data: print(node_data['name'])
            
            data = export_edges_to_dict(nodes_dict,edges)
            return jsonify({'connections': data,
                            'top_rows':df[['Geneid', 'Normalized_Read_Counts']].to_dict(orient='records'),
                            'rows': len(df)})

        except Exception as e:
            print(f"ERROR: {e}")
            import traceback

            traceback.print_exc()  # Print full traceback for debugging
            return jsonify({'error': str(e)}), 400

        except Exception as e:
            print(f"ERROR: {e}")
            return jsonify({'error': str(e)}), 400

    return jsonify({'error': 'File upload failed'}), 400

if __name__ == '__main__':
    app.run(debug=True)
