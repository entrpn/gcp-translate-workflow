import os
import uuid

from package.translate import batch_translate_document

from google.cloud import storage

from flask import Flask, request, jsonify
from dotenv import load_dotenv
load_dotenv()

def create_gcs_dir(bucket_name, job_dir):
    print("bucket_name:",bucket_name[5:-1])
    print("new dir:",job_dir)
    gcs_client = storage.Client()
    bucket = gcs_client.get_bucket(bucket_name[5:-1])
    blob = bucket.blob(job_dir)
    blob.upload_from_string('')


app = Flask(__name__)

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)

@app.route("/translate", methods=['POST'])
def translate_docs():
    data = request.json
    print(data)
    input_path = data["input_path"]
    output_path = data["output_path"]
    
    from_language_code = data["from_language_code"]
    to_language_code = data["to_language_code"]

    unique_id = str(uuid.uuid4())
    print(unique_id)
    job_dir=unique_id + "/"
    print(job_dir)
    create_gcs_dir(output_path,job_dir)
    
    operation_name = batch_translate_document(input_path, output_path+job_dir, from_language_code, to_language_code)

    response = {}
    response["status"] = "OK"
    response["operation_name"] = operation_name
    response["output_bucket_uri"] = output_path+unique_id

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))