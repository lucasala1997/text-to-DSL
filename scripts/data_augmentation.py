from dotenv import load_dotenv

import json
import logging
import random
import os
from nltk.corpus import wordnet
import spacy
import openai  # Import OpenAI library for GPT-4 paraphrasing

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Load environment variables from the .env file
load_dotenv()

def augment_data(method='nltk'):
    """Augments the JSON data by creating synthetic examples through specified augmentation techniques.

    This function generates synthetic data entries based on existing examples using one of three methods: 
    NLTK, SpaCy, or OpenAI GPT-4.

    Args:
        method (str): The augmentation method to use ('nltk', 'spacy', or 'openai'). Default is 'nltk'.

    Raises:
        FileNotFoundError: If the data files are not found.
        JSONDecodeError: If there is an error in decoding the JSON data.
    """
    try:
        # Load the examples
        with open('data/simple_examples.json', 'r') as file:
            simple_examples = json.load(file)
        logging.info('Simple examples loaded successfully for augmentation.')

        with open('data/complex_examples.json', 'r') as file:
            complex_examples = json.load(file)
        logging.info('Complex examples loaded successfully for augmentation.')

        # Perform data augmentation based on the chosen method
        augmented_examples = []
        for example in simple_examples + complex_examples:
            augmented_example = augment_example(example, method=method)
            augmented_examples.append(augmented_example)

        # Save augmented data to a new file
        with open('data/augmented_examples.json', 'w') as augmented_file:
            json.dump(augmented_examples, augmented_file, indent=4)
        logging.info(f'Data augmentation completed using {method} method and saved successfully.')

    except FileNotFoundError as fnf_error:
        logging.error(f"File not found: {fnf_error}")
    except json.JSONDecodeError as json_error:
        logging.error(f"Error decoding JSON: {json_error}")
    except Exception as e:
        logging.error(f"Unexpected error in data augmentation: {e}")

def augment_example(example, method='nltk'):
    """Augments a given example using the specified method.

    Args:
        example (dict): The original example containing fields like 'input_text', 'expected_dsl_output', etc.
        method (str): The augmentation method to use ('nltk', 'spacy', or 'openai').

    Returns:
        dict: A new dictionary representing the augmented example with 'synthetic_data' set to True.
    """
    if method == 'nltk':
        paraphrased_text = paraphrase_with_nltk(example['input_text'])
    elif method == 'spacy':
        paraphrased_text = paraphrase_with_spacy(example['input_text'])
    elif method == 'openai':
        paraphrased_text = paraphrase_with_openai(example['input_text'])
    else:
        raise ValueError("Invalid method specified. Choose from 'nltk', 'spacy', or 'openai'.")

    augmented_example = {
        "example_id": f"{example['example_id']}_augmented",
        "input_text": paraphrased_text,
        "expected_dsl_output": example['expected_dsl_output'],
        "complexity_level": example['complexity_level'],
        "description": example['description'],
        "synthetic_data": True
    }
    return augmented_example

def paraphrase_with_nltk(text):
    """Paraphrases the input text using NLTK by replacing words with synonyms.

    Args:
        text (str): The input text to be paraphrased.

    Returns:
        str: A paraphrased version of the input text.
    """
    words = text.split()
    paraphrased_words = []
    for word in words:
        synonyms = wordnet.synsets(word)
        if synonyms:
            paraphrased_words.append(random.choice(synonyms).lemmas()[0].name())
        else:
            paraphrased_words.append(word)
    return ' '.join(paraphrased_words)

def paraphrase_with_spacy(text):
    """Paraphrases the input text using SpaCy's NLP model.

    Args:
        text (str): The input text to be paraphrased.

    Returns:
        str: A paraphrased version of the input text using SpaCy.
    """
    # Process text with SpaCy model
    doc = nlp(text)
    paraphrased_text = ' '.join([token.text for token in doc])
    return paraphrased_text  # This is a placeholder; further enhancements can be made for true paraphrasing

def paraphrase_with_openai(text):
    """Paraphrases text using OpenAI GPT-4-turbo API.

    Args:
        text (str): The input text to be paraphrased.

    Returns:
        str: A paraphrased version of the text using GPT-4-turbo.
    """
    try:
        # Retrieve the OpenAI API key from environment variables
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OpenAI API key not found. Please set the API key in the .env file.")

        openai.api_key = openai_api_key

        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that specializes in paraphrasing text."},
                {"role": "user", "content": f"Paraphrase the following text: '{text}'"}
            ],
            max_tokens=100,
            temperature=0.7,
        )

        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Error using OpenAI GPT-4-turbo for paraphrasing: {e}")
        return text  # Return the original text if paraphrasing fails
