import os
from google.cloud import translate_v3beta1 as translate

PROJECT_ID=os.getenv('PROJECT_ID')

def batch_translate_document(
    input_uri: str,
    output_uri: str,
    from_language_code: str,
    to_language_code: str
):

    client = translate.TranslationServiceClient()

    # The ``global`` location is not supported for batch translation
    location = "us-central1"

    # Google Cloud Storage location for the source input. This can be a single file
    # (for example, ``gs://translation-test/input.docx``) or a wildcard
    # (for example, ``gs://translation-test/*``).
    # Supported file types: https://cloud.google.com/translate/docs/supported-formats
    gcs_source = {"input_uri": input_uri}

    batch_document_input_configs = {
        "gcs_source": gcs_source,
    }
    gcs_destination = {"output_uri_prefix": output_uri}
    batch_document_output_config = {"gcs_destination": gcs_destination}
    parent = f"projects/{PROJECT_ID}/locations/{location}"

    # Supported language codes: https://cloud.google.com/translate/docs/language
    operation = client.batch_translate_document(
        request={
            "parent": parent,
            "source_language_code": from_language_code,
            "target_language_codes": [to_language_code],
            "input_configs": [batch_document_input_configs],
            "output_config": batch_document_output_config,
        }
    )
    return operation._operation.name