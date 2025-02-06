import json
import os
import re

def process_json(json_path):
    # Load the JSON file
    with open(json_path, 'r') as file:
        data = json.load(file)
    
    # Process each entry in the JSON
    for entry in data:
        if 'generated_dsl_output' in entry:
            # Extract the generated_dsl_output field
            dsl_output = entry['generated_dsl_output']
            
            # Remove everything between <think> tags (including the tags)
            dsl_output = re.sub(r'<think>.*?</think>', '', dsl_output, flags=re.DOTALL)
            
            # Find the index of "CREATE"
            create_index = dsl_output.find("CREATE")
            if create_index == -1:
                continue  # Skip if "CREATE" is not found
            
            # Remove everything before "CREATE"
            dsl_output = dsl_output[create_index:]
            
            # Find the last semicolon
            last_semicolon_index = dsl_output.rfind(';')
            if last_semicolon_index == -1:
                continue  # Skip if no semicolon is found
            
            # Remove everything after the last semicolon
            dsl_output = dsl_output[:last_semicolon_index + 1]
            
            # Update the entry with the processed DSL output
            entry['generated_dsl_output'] = dsl_output
    
    # Create a new filename for the processed JSON
    base_name, ext = os.path.splitext(json_path)
    new_json_path = f"{base_name}_processed{ext}"
    
    # Save the modified JSON to the new file
    with open(new_json_path, 'w') as file:
        json.dump(data, file, indent=4)
    
    print(f"Processed JSON saved to: {new_json_path}")

# Example usage
json_path = "/home/lucasala/text_to_dsl/text-to-DSL/logs/models_results/Deepseek_r1_(70B)_fp.json"
process_json(json_path)