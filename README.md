## Intro

This demo shows how users can create a Flask server in Cloud Run to run document translation jobs. A Cloud Function is triggered when the job is completed.

## Setup

### Setting up credentials

The Cloud Run server takes requests to create Document translation jobs.

1. You'll need a service account with the following roles:

    - roles/artifactregistry.admin
    - roles/automl.admin <<-- Used if running AutoML translate
    - roles/cloudbuild.serviceAgent
    - roles/run.admin
    - roles/cloudtranslate.user
    - roles/storage.admin
    - roles/cloudfunctions.admin

    From Cloud Shell you can create it with the following commands.

    ```bash
    gcloud projects describe $GOOGLE_CLOUD_PROJECT > project-info.txt
    PROJECT_ID=$(cat project-info.txt | sed -nre 's:.*projectId\: (.*):\1:p')
    gcloud iam service-accounts create translate-demo \
        --description="My demo account" \
        --display-name="translate-demo"
    ```

    And assign roles:

    ```bash
    SVC_ACCOUNT=translate-demo@${PROJECT_ID}.iam.gserviceaccount.com
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$SVC_ACCOUNT --role roles/storage.objectAdmin
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$SVC_ACCOUNT --role roles/cloudtranslate.user
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$SVC_ACCOUNT --role roles/run.admin
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$SVC_ACCOUNT --role  roles/cloudbuild.serviceAgent
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$SVC_ACCOUNT --role  roles/iam.serviceAccountUser
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$SVC_ACCOUNT --role  roles/automl.admin
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$SVC_ACCOUNT --role roles/artifactregistry.admin
    gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT --member serviceAccount:$SVC_ACCOUNT --role roles/cloudfunctions.admin
    ```

1. You'll also need to enable the following APIs:

    - artifactregistry.googleapis.com
    - cloudbuild.googleapis.com
    - translate.googleapis.com
    - run.googleapis.com
    - containerregistry.googleapis.com
    - automl.googleapis.com <<-- Used if running AutoML Translate

    You can do so as follows:

    ```
    gcloud services enable artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    translate.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudfunctions.googleapis.com \
    automl.googleapis.com
    ```

### Deploy The Cloud Run server

1. From the `cloud_run` directory where the `Dockerfile` is located, deploy to Cloud Run. You'll use the service account created so that the Cloud Run instance. Press enter for default values and choose the zone when you are prompted.

    ```bash
    gcloud run deploy --update-env-vars PROJECT_ID=<YOUR_PROJECT_ID> --service-account translate-demo@<YOUR_PROJECT_ID>.iam.gserviceaccount.com
    ```
1. Once deployed, test the service is running. Don't forget to change the URL

    ```bash
    curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" https://your.url.app
    ```

    The response should be `Hello World!`

### Deploy Cloud Function Trigger

The cloud function Trigger is used to inform users when a job is completed. Although this cloud function simply logs when a translated file is uploaded to a GCS bucket, it could be modified for alerting or pushing messages to another server or database to confirm job completion.

1. From inside the `cloud_function` folder, run the following command:

```bash
gcloud functions deploy translate_workflow --runtime python38 --trigger-resource jfa-automl-translate-outputs --trigger-event google.storage.object.finalize --ingress-settings internal-and-gclb --service-account translate-demo@<YOUR_PROJECT_ID>.iam.gserviceaccount.com
```

## Running a translation job.

1. Upload a file you want translated to a GCS bucket. 
1. Create an output bucket where files will land after the translation is finished. **Make a note of this bucket as it will be used later when we deploy a cloud function to monitor job completion.**
1. Modify the json message so that `input_path` points to the file you want translated and `output_path` to the bucket where the file will land after is finished. Also change the `from_language_code` and `to_language_code` to the languages you've like. Language codes can be found [here](https://cloud.google.com/translate/docs/languages).

    ```bash
    curl -X POST https://<cloud-run-instance-name>.app/translate -H "Authorization: Bearer $(gcloud auth print-identity-token)" -H 'Content-Type: application/json' -d "{\"input_path\" : \"gs://automl-translate-inputs/test_doc.docx\", \"output_path\" : \"gs://automl-translate-outputs/\", \"from_language_code\" : \"en-US\", \"to_language_code\" : \"es\"}"
    ```

    You'll receive a response with an operation name which can be queried for status. You'll also receive the `output_bucket_uri`. The `output_bucket_uri` is appended with a UUID so that different jobs do not conflict with each other. This data can potentially be stored in a database to match requests and responses in a system. Depending on how long the document is, it might take some time for the job to complete. To query the operation you can run the following:

    ```bash
    curl -H "Authorization: Bearer $(gcloud auth print-access-token)" https://translation.googleapis.com/v3/projects/<PROJECT_ID>/locations/us-central1/operations/20220503-<SOME_ID>-<ANOTHER_ID>-<MORE_IDS>
    ```

