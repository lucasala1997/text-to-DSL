import requests
import json

# Define the base URL and API endpoint
base_url = 'http://localhost:11434/v1/chat/completions'

# Headers and payload for the request
headers = {
    'Authorization': 'Bearer ollama',  # required, but unused
    'Content-Type': 'application/json'
}

 # Load few-shot examples
few_shot_examples_file = f"data/sensors/few_shot_examples.json"
few_shot_examples = []
with open(few_shot_examples_file, 'r') as file:
    few_shot_examples = json.load(file)


message = []
message.append({"role": "system", "content": "You are a helpful assistant. You are tasked with generating Domain Specific Language (DSL) code for a given input. Respond only with the DSL code."})
message.append({"role": "user", "content": "Rules that need to be followed to write the code:"})
message.append({"role": "user", "content": "prova"})

if few_shot_examples:
    for idx, example in enumerate(few_shot_examples, 1):
        message.append({"role": "user", "content": example['input_text']})
        message.append({"role": "assistant", "content": example['expected_dsl_output']})

message.append({"role": "user", "content": "write Anything"})

# Data for the chat completion request
data = {
    "model": "codellama:7b-instruct-q4_K_M",
    "messages": message,
    "seed": 7,
    "num_predict": -1,
    "num_ctx": 16384,
    "top_k": 40,
    "top_p": 0.7,
    "temperature": 0.7
}

# Send the request to the API
response = requests.post(base_url, headers=headers, json=data)

# Check if the request was successful and print the result
if response.status_code == 200:
    result = response.json()
    print(result['choices'][0]['message']['content'])
else:
    print(f"Error: {response.status_code} - {response.text}")
