# Lumiere - Cyber Data Miner PoC

<img src="img/image.png" alt="Banner" style="width: 100%; height: auto;">

In this project, we demonstrate the capabilities of Lumiere, a tool Powered by OpenAI, using a simple Flask web application.
The Python app connects to the custom OpenAI Assistants API to process the provided data files, generate a dataset based on specific guidelines and deliver the output in a parquet or CSV file.
Users may upload files and input context via an intuitive interface. 

For demonstration purposes we used an web `access.log` file and obtain the `preoccesd_dataset.csv`. 

The results have shown better labeling of potential malicious requests, compared to Apache Scalp. 

The functionality is also available through the intuitive Custom GPT, also named Lumiere, available in OpenAI's store.