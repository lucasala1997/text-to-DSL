import pandas as pd
import json
import sys

def clean_model_name(name):
    name = name.replace("overall_metrics_", "")  # Remove prefix
    name = name.replace("_", " ")  # Replace underscores with spaces
    name = name.replace("quantized", "").strip()  # Remove "quantized"
    name = name.replace("full precision", "fp")  # Replace "full precision" with "fp"
    return name

def format_parameters(param_str, model_name):
    try:
        params = json.loads(param_str.replace("'", "\""))  # Ensure valid JSON format
        if "OpenAI" in model_name:
            formatted = f"top_p: {params.get('top_p', 'N/A')}, t: {params.get('temperature', 'N/A')}"
        else:
            formatted = f"top_k: {params.get('top_k', 'N/A')}, top_p: {params.get('top_p', 'N/A')}, t: {params.get('temperature', 'N/A')}"
        return formatted
    except json.JSONDecodeError:
        return "Invalid Params"

def process_csv(file_path, output_path):
    # Load the CSV file
    df = pd.read_csv(file_path)
    
    # Apply transformations
    df.rename(columns={
        "model_name": "Models",
        "overall_accuracy": "Acc_avg",
        "complex_accuracy": "Acc_com",
        "simple_accuracy": "Acc_sim",
        "average_bleu_score": "Bleu_avg",
        "complex_bleu_score": "Bleu_com",
        "simple_bleu_score": "Bleu_sim"
    }, inplace=True)
    
    df["Models"] = df["Models"].apply(clean_model_name)
    df["parameters"] = df.apply(lambda row: format_parameters(row["parameters"], row["Models"]), axis=1)
    
    # Drop unnecessary columns
    df.drop(columns=["average_time", "average_complex_time", "average_simple_time", "system_prompt_version", "total_examples"], inplace=True)
    
    # Limit all other numerical columns to at most 3 decimal places, keeping leading digits
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].apply(lambda x: round(x, 3))
    
    # Save the processed CSV
    df.to_csv(output_path, index=False)
    print(f"Processed file saved at: {output_path}")

if __name__ == "__main__":
    input_path = "/home/lucasala/text_to_dsl/text-to-DSL/logs/best_model_results.csv"
    output_path = "/home/lucasala/text_to_dsl/text-to-DSL/logs/best_model_results_cleaned.csv"
    process_csv(input_path, output_path)