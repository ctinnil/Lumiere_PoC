import openai
import pandas as pd
import os
import time
import re
from dotenv import load_dotenv
from flask import Flask, request, send_file, render_template_string
import fastparquet
import json

"""Create a custom dataset fit for ML and DL form the provided web access log file, label the events based on your knowledge and know best practices or recommendations as malicious and legitimate, and encode and scale. Make assumptions and execute all the processing as needed."""

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
assistant_id = os.getenv("ASSISTANT_ID")

# Initialize the OpenAI client
client = openai.OpenAI(api_key=openai.api_key)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        context = request.form.get('context')
        file = request.files.get('file')
        context += " Limit your output to the resulting dataset into a single downloadable .parquet or .CSV file. Limit your output to conserve tokens to the bare minimum. Your asnwer should not be longer then 30 words! Don't provide any extra explanations, just the final file to download!"

        if not file:
            return 'No file uploaded', 400

        try:
            temp_filename = 'temp_uploaded_file'
            file.save(temp_filename)
            with open(temp_filename, 'rb') as f:
                openai_file = client.files.create(file=f, purpose='assistants')
            os.remove(temp_filename)
        except Exception as e:
            return f"Error uploading file to OpenAI: {e}", 500

        try:
            thread = client.beta.threads.create(messages=[{"role": "user", "content": context, "file_ids": [openai_file.id]}])
            run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

            run_status = None
            while run_status != "completed":
                time.sleep(2)
                updated_run = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)
                run_status = updated_run.status

                if run_status in ["failed", "expired", "cancelled"]:
                    return f"Run did not complete successfully: Status {run_status}"

            all_messages = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_messages = [msg for msg in all_messages if msg.role == "assistant"]
            latest_response = assistant_messages[-1].content if assistant_messages else ""

            print(assistant_messages)
            print()
            print(latest_response)

        except Exception as e:
            return f"Error in thread processing: {e}", 500

        try:
            file_id = extract_file_id(latest_response)
            print(file_id)
            if file_id:
                # Retrieve the file metadata
                file_metadata_response = client.files.retrieve(file_id)
                # Access the filename attribute directly
                filename = file_metadata_response.filename
                print(filename)
                file_content = client.files.retrieve_content(file_id)
                print(file_content)
                output_filename = os.path.basename(filename)
                print(output_filename)
                with open(output_filename, 'w') as file:
                    file.write(file_content)
                    # Check the file extension and read the file accordingly
                if output_filename.endswith('.csv'):
                    df = pd.read_csv(output_filename)
                elif output_filename.endswith('.parquet'):
                    df = pd.read_parquet(output_filename, engine='fastparquet')
                else:
                    return f"Unsupported file type for {output_filename}", 400
                print(df.head())
            else:
                return "No file ID found in the assistant's responses", 400
        except Exception as e:
            return f"Error processing file: {e}", 500

        return send_file(output_filename, as_attachment=True)

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Lumiere - Cyber Data Miner</title>
    <link rel="icon" type="image/png" href="/static/favicon.ico">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f4f4f4;
            text-align: center;
        }
        .container {
            margin-top: 50px;
        }
        .logo {
            width: 100px;
            margin-bottom: 20px;
        }
        h2 {
            color: #333;
        }
        form {
            background: #fff;
            padding: 20px;
            display: inline-block;
            border-radius: 5px;
            box-shadow: 0px 0px 10px 0px #0000001a;
        }
        label {
            display: block;
            margin: 15px 0 5px;
        }
        textarea, input[type="file"] {
            width: 95%;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        input[type="submit"] {
            background: #0275d8;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background: #025aa5;
        }
        .form-footer {
            text-align: right;
            margin-top: 20px;
        }

        .openai-badge {
            width: 100px; /* Adjust as needed */
        }
    </style>
</head>
<body>
    <div class="container">
        <img class="logo" src="/static/logo_t.png" alt="Lumiere Logo">
        <h2>Lumiere - Cyber Data Miner</h2>
        <form method="post" enctype="multipart/form-data">
            <label for="context">Context:</label>
            <textarea name="context" rows="4" cols="50"></textarea>
            <label for="file">Upload file:</label>
            <input type="file" name="file">
            <input type="submit" value="Submit">
            <div class="form-footer">
                <!-- Powered by OpenAI badge -->
                <img class="openai-badge" src="/static/powered-by-openai-badge-outlined-on-light.svg" alt="Powered by OpenAI">
            </div>
        </form>
    </div>
</body>
</html>
    ''')

def extract_file_id(messages):
    file_id_pattern = r"file-[a-zA-Z0-9]+"
    match = re.search(file_id_pattern, str(messages))
    if match:
        return match.group(0)
    return None

if __name__ == '__main__':
    app.run(debug=True)
