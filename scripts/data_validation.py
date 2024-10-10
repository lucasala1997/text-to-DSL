import json
import logging
from jsonschema import validate, ValidationError

def validate_data():
    """Validates the JSON data for both simple and complex examples against a predefined schema.

    This function ensures that all data entries conform to the specified schema requirements.

    Raises:
        FileNotFoundError: If the data files are not found.
        JSONDecodeError: If there is an error in decoding the JSON data.
        ValidationError: If the JSON data does not conform to the specified schema.
    """
    try:
        # Define the JSON schema for validation
        schema = {
            "type": "object",
            "properties": {
                "example_id": {"type": "string"},
                "input_text": {"type": "string"},
                "expected_dsl_output": {"type": "string"},
                "complexity_level": {"type": "string"},
                "description": {"type": "string"},
                "synthetic_data": {"type": "boolean"}
            },
            "required": ["example_id", "input_text", "expected_dsl_output", "complexity_level", "description", "synthetic_data"]
        }

        # Load the simple examples
        with open('../data/simple_examples.json', 'r') as file:
            simple_examples = json.load(file)
        logging.info('Simple examples loaded successfully.')

        # Load the complex examples
        with open('../data/complex_examples.json', 'r') as file:
            complex_examples = json.load(file)
        logging.info('Complex examples loaded successfully.')

        # Validate each example against the schema
        for example in simple_examples:
            try:
                validate(instance=example, schema=schema)
            except ValidationError as schema_error:
                logging.error(f"Validation error in simple_examples.json: {schema_error.message}. Problematic data: {example}")

        for example in complex_examples:
            try:
                validate(instance=example, schema=schema)
            except ValidationError as schema_error:
                logging.error(f"Validation error in complex_examples.json: {schema_error.message}. Problematic data: {example}")

        logging.info('Data validation completed successfully. All entries conform to the schema.')

    except FileNotFoundError as fnf_error:
        logging.error(f"File not found: {fnf_error}")
    except json.JSONDecodeError as json_error:
        logging.error(f"Error decoding JSON: {json_error}")
    except ValidationError as schema_error:
        logging.error(f"Data does not conform to schema: {schema_error}")
    except Exception as e:
        logging.error(f"Unexpected error in data validation: {e}")


