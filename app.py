import openai
import pandas as pd
import os
import time
from dotenv import load_dotenv
from flask import Flask, request, send_file, render_template_string
import requests
import fastparquet
import openai.error

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
        context += " Output the resulting dataset into a single downloadable parquet file."

        if not file:
            return 'No file uploaded', 400

        try:
            # Save the uploaded file temporarily
            temp_filename = 'temp_uploaded_file'
            file.save(temp_filename)

            # Upload the file to OpenAI
            with open(temp_filename, 'rb') as f:
                openai_file = client.files.create(
                    file=f,
                    purpose='assistants'
                )
            os.remove(temp_filename)  # Remove the temporary file
        except Exception as e:
            return f"Error uploading file to OpenAI: {e}", 500

        try:
            # Create and process the thread
            response = process_thread(context, openai_file.id)
            if isinstance(response, str):
                # If response is string, it's an error message
                return response
        except openai.error.RateLimitError:
            # Handle rate limit error by retrying after a pause
            time.sleep(10)
            # Retry the request here
            try:
                response = process_thread(context, openai_file.id)
                if isinstance(response, str):
                    return response
            except Exception as e:
                return f"Error after retrying: {e}", 500
        except Exception as e:
            return f"Error processing thread: {e}", 500

        # Assuming response is the output filename
        return send_file(response, as_attachment=True)

    # HTML form for file upload and context input
    return render_template_string('''... [Your HTML form] ...''')

def process_thread(context, file_id):
    try:
        # Create a thread with the file ID
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": context,
                    "file_ids": [file_id]
                }
            ]
        )
        # ... [Rest of your run code remains the same] ...
        # Assuming the final output is a file name
        return 'output_filename'
    except Exception as e:
        return f"Error in thread processing: {e}"

if __name__ == '__main__':
    app.run(debug=True)
