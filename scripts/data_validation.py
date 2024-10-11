import json
import logging
from jsonschema import validate, ValidationError
import os

def validate_data(dataset_name=None):
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
                "DSL_type": {"type": "string"},
                "input_text": {"type": "string"},
                "expected_dsl_output": {"type": "string"},
                "complexity_level": {"type": "string"},
                "description": {"type": "string"},
                "synthetic_data": {"type": "boolean"}
            },
            "required": ["example_id", "DSL_type", "input_text", "expected_dsl_output", "complexity_level", "description", "synthetic_data"]
        }

        # If no dataset is provided, prompt the user to select a dataset
        if not dataset_name:
            # Read the directory data and create a list with the name of the first level folders in it
            data_directory = 'data'
            available_dataset = [name for name in os.listdir(data_directory) if os.path.isdir(os.path.join(data_directory, name))]
            print("Available datasets:")
            for i, model in enumerate(available_dataset, 1):
                print(f"{i}. {model}")

            # Keep prompting the user until a valid choice is made
            while True:
                try:
                    dataset_choice = int(input("Enter the dataset you wish to test: "))
                    if 1 <= dataset_choice <= len(available_dataset):
                        dataset_name = available_dataset[dataset_choice - 1]
                        print(f"\nUsing Dataset: {dataset_name}")
                        break  # Exit the loop once a valid choice is made
                    else:
                        print("Invalid choice. Please enter a number corresponding to the available datasets.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")


        # Load the simple examples
        with open(f'data/{dataset_name}/simple_examples.json', 'r') as file:
            simple_examples = json.load(file)
        logging.info('Simple examples loaded successfully.')

        # Load the complex examples
        with open(f'data/{dataset_name}/complex_examples.json', 'r') as file:
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
        return dataset_name

    except FileNotFoundError as fnf_error:
        logging.error(f"File not found: {fnf_error}")
    except json.JSONDecodeError as json_error:
        logging.error(f"Error decoding JSON: {json_error}")
    except ValidationError as schema_error:
        logging.error(f"Data does not conform to schema: {schema_error}")
    except Exception as e:
        logging.error(f"Unexpected error in data validation: {e}")


