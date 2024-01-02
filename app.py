import openai
import pandas as pd
import os
import time
from dotenv import load_dotenv
from flask import Flask, request, send_file, render_template_string
import requests
import fastparquet

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
            # Create a thread with the file ID
            thread = client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": context,
                        "file_ids": [openai_file.id]
                    }
                ]
            )

            # Create a run within the thread
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )

            # Polling mechanism to wait for the run to complete
            max_retries = 100
            retries = 0
            run_status = None
            while run_status != "completed" and retries < max_retries:
                time.sleep(2)  # Sleep for 2 seconds before checking the status again
                updated_run = client.beta.threads.runs.retrieve(run_id=run.id, thread_id=thread.id)
                run_status = updated_run.status
                retries += 1

                if run_status in ["failed", "expired", "cancelled"]:
                    return f"Run did not complete successfully: Status {run_status}"

            if retries >= max_retries:
                return "Run polling reached maximum retries"

            # Retrieve the latest assistant message
            thread_messages = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_messages = [msg for msg in thread_messages if msg.role == "assistant"]
            latest_response = assistant_messages[-1].content if assistant_messages else ""

            # Here you need to process latest_response to get the output file
            # This depends on how your OpenAI model responds
            # Assuming it provides a direct link or data to create a file
            output_filename = 'processed_output.parquet'
            # Process the response to create or download the file
            
        except Exception as e:
            return f"Error in thread processing: {e}", 500

        return send_file(output_filename, as_attachment=True)

    # HTML form for file upload and context input
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <body>

        <h2>File and Context Submission</h2>
        <form method="post" enctype="multipart/form-data">
            <label for="context">Context:</label><br>
            <textarea name="context" rows="4" cols="50"></textarea><br><br>
            <label for="file">Upload file:</label><br>
            <input type="file" name="file"><br><br>
            <input type="submit" value="Submit">
        </form>

        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
