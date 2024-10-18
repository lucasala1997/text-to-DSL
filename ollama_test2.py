import requests

# Define the base URL and API endpoint
base_url = 'http://localhost:11434/v1/chat/completions'

# Headers and payload for the request
headers = {
    'Authorization': 'Bearer ollama',  # required, but unused
    'Content-Type': 'application/json'
}

# Data for the chat completion request
data = {
    "model": "llama3.1:8b",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"}
    ]
}

# Send the request to the API
response = requests.post(base_url, headers=headers, json=data)

# Check if the request was successful and print the result
if response.status_code == 200:
    result = response.json()
    print(result['choices'][0]['message']['content'])
else:
    print(f"Error: {response.status_code} - {response.text}")
