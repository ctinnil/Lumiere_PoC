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

        # Create a thread with the file ID
        try:
            thread = client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": context,
                        "file_ids": [openai_file.id]
                    }
                ]
            )
        except Exception as e:
            return f"Error creating thread: {e}", 500

        # Create a run within the thread
        try:
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
                    return f"Run did not complete successfully: Status {run_status}", 500

            if retries >= max_retries:
                return "Run polling reached maximum retries", 500

            # Retrieve the latest assistant message
            thread_messages = client.beta.threads.messages.list(thread_id=thread.id)
            assistant_messages = [msg for msg in thread_messages if msg.role == "assistant"]
            latest_response = assistant_messages[-1].id if assistant_messages else ""

        except Exception as e:
            return f"Error in calling OpenAI API: {e}", 500
        
        print(thread_messages.data)
        print(latest_response.data)
        
        # Process the response
        try:
            # Validate the latest_response before making a request
            if not latest_response.startswith("http"):
                return "Invalid response format", 500

            response = requests.get(latest_response.strip())
            output_filename = 'downloaded_file.parquet'
            with open(output_filename, 'wb') as file:
                file.write(response.content)

            # Read and process the Parquet file
            df = pd.read_parquet(output_filename, engine='fastparquet')
            # Example processing: Print the first few rows
            print(df.head())

        except Exception as e:
            return f"Error processing model output: {e}", 500

        # Return the file for download
        return send_file(output_filename, as_attachment=True)

    # HTML form for file upload and context input
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <body>

        <h2>Lumiere - Cyber Data Miner</h2>
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
