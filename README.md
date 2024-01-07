# Lumiere - Cyber Data Miner PoC

<img src="static/image.png" alt="Banner" style="width: 100%; height: auto;">

In this project, we demonstrate the capabilities of Lumiere, a tool Powered by OpenAI, using a simple Flask web application.
The Python app connects to the custom OpenAI Assistants API to process the provided data files, generate a dataset based on specific guidelines, and deliver the output in a parquet or CSV file.
Users may upload files and input context via an intuitive interface.

![Lumiere](<static/lumiere poc.drawio.png>)

To access the full functionality please check the API documentation at [OpenAI](https://platform.openai.com/docs/overview).

*Example*

```bash
curl https://api.openai.com/v1/assistants/asst_QE9FSwuR2ZWTl7mzQZKBHzSy \                     
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "OpenAI-Beta: assistants=v1"
```

This Flask App will allow you to create a dataset in a couple of easy steps:

- add an explicit context describing the file used as a base;
- upload the file;
- press submit and wait for the result.

***As the LLM can generate different outputs, the cost of the API will depend on your context and how well the GPT understands the task. Sometimes, a file will not be delivered, so check the printouts and emphasize the context to limit the scope of the model.***

![Alt text](<static/Lumiere API PoC.png>)

For demonstration purposes, we used a web `access.log` file and obtained the `labeled_web_interaction_dataset.csv`.

+ [Original access.log](files/access.log)
+ [Apache Scalp results](files/access.log_scalp_Tue-19-Dec-2023.txt)
+ [Resulting dataset](files/labeled_web_interaction_dataset.csv)

The results have shown better labeling of potential malicious requests, compared to [Apache Scalp](https://code.google.com/archive/p/apache-scalp/).

	|Total Processed|Marked as Malicious|Marked as Legitimate
---|---|---|--- 
**Apache Scalp**|84.355|24.996|59.359
***Lumiere***|84.348|8.218|76.130

![Alt text](<static/chart scalp lumiere_white.001.png>)

The functionality is also available through the intuitive Custom GPT, also named [Lumiere](https://chat.openai.com/g/g-7GQEoVuPT-lumiere), available in OpenAI's store.

![Alt text](<static/Lumiere ChatGPT PoC.png>)