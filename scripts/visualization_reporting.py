import logging
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from utils import load_config


config = load_config()
# Set up logging based on config.json
logging.basicConfig(
    filename=config['paths']['project_log_file'],
    level=getattr(logging, config['logging']['level'], logging.INFO),
    format=config['logging']['format']
)

def generate_complexity_scatter_plot(metrics_folder="logs/models_results", results_folder="results"):
    """Generates scatter plots with separate points for 'simple' and 'complex' examples based on model test results."""
    
    # Ensure the results folder exists
    os.makedirs(results_folder, exist_ok=True)
    
    # Loop through all model result files and process them
    for file_name in os.listdir(metrics_folder):
        if file_name.endswith(".json"):
            # Read the JSON dataå
            model_file_path = os.path.join(metrics_folder, file_name)
            #print(model_file_path + "\n")
            with open(model_file_path, 'r') as file:
                data = json.load(file)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Prepare model-specific results directory
            
            model_name = file_name.replace('.json', '').replace('_', ' ')   
            model_results_path = os.path.join(results_folder, model_name)
            os.makedirs(model_results_path, exist_ok=True)
            
            # Extract parameters and separate by complexity
            df['temperature'] = df['parameters'].apply(lambda x: x['temperature'])
            df['top_p'] = df['parameters'].apply(lambda x: x['top_p'])
            #TODO: check if complexity_level is correct
            df['overall_accuracy'] = df['success'].apply(lambda x: 1 if x else 0)

            # Generate scatter plot
            plt.figure(figsize=(10, 6))
            sns.scatterplot(data=df, x='temperature', y='overall_accuracy', hue='complexity_level', style='complexity_level', s=100, palette='viridis')
            plt.xlabel("Temperature")
            plt.ylabel("Overall Accuracy")
            plt.title(f"Scatter Plot of Temperature vs. Overall Accuracy by Complexity Level for {model_name}")
            plt.legend(title='Complexity Level')

            # Save the plot
            plot_path = os.path.join(model_results_path, f"{model_name}_complexity_accuracy_scatter.png")
            plt.savefig(plot_path)
            plt.close()
            
            logging.info(f"Scatter plot saved for {model_name} at {plot_path}")


# Helper function to create a bar plot for parameter combinations
def plot_parameter_combinations(df, model_name, model_results_path):
    """Generates a bar plot for different parameter combinations by overall accuracy."""
    
    # Create a readable string for each parameter combination
    df['parameters_str'] = df['parameters'].apply(lambda x: f"top_k={x['top_k']}, top_p={x['top_p']}, temperature={x['temperature']}, version={df['system_prompt_version']}")
    
    # Generate the bar plot
    plt.figure(figsize=(10, 6))
    plt.bar(df['parameters_str'], df['overall_accuracy'], color='skyblue')
    plt.xlabel("Parameter Combinations")
    plt.ylabel("Overall Accuracy")
    plt.title(f"Best Performing Parameter Combinations by Overall Accuracy for {model_name}")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    # Save the plot in the model-specific results folder
    plot_path = os.path.join(model_results_path, f"{model_name}_parameter_combinations.png")
    plt.savefig(plot_path)
    plt.close()
    
    logging.info(f"Parameter combinations plot saved for {model_name} at {plot_path}")
    
def generate_scatter_plot(metrics_folder="logs/models_results/overall_results", results_folder="results"):
    # Ensure the results folder exists
    os.makedirs(results_folder, exist_ok=True)
    
    # Loop through all metric files and process them
    os.makedirs(metrics_folder, exist_ok=True)
    for file_name in os.listdir(metrics_folder):
        if file_name.endswith(".json"):
            # Derive model name from file name
            model_name = file_name.replace("overall_metrics_", "").replace('.json', '').replace('_', ' ')
            
            # Read the JSON data
            with open(os.path.join(metrics_folder, file_name), 'r') as file:
                data = json.load(file)
            
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            
            # Extract parameters for scatter plotting
            df['temperature'] = df['parameters'].apply(lambda x: x['temperature'])
            df['top_p'] = df['parameters'].apply(lambda x: x['top_p'])
            df['overall_accuracy'] = df['overall_accuracy']
            
            # Prepare model-specific results directory
            model_results_path = os.path.join(results_folder, model_name)
            os.makedirs(model_results_path, exist_ok=True)
            
            # Generate scatter plot for temperature vs overall_accuracy
            plt.figure(figsize=(10, 6))
            sns.scatterplot(data=df, x='temperature', y='overall_accuracy', hue='top_p', palette='viridis', s=100)
            plt.xlabel("Temperature")
            plt.ylabel("Overall Accuracy")
            plt.title(f"Scatter Plot of Temperature vs. Overall Accuracy for {model_name} (Hue: top_p)")
            plt.legend(title='Top_p')
            
            # Save the scatter plot
            scatter_plot_path = os.path.join(model_results_path, f"{model_name}_accuracy_scatter.png")
            plt.savefig(scatter_plot_path)
            plt.close()
            
            logging.info(f"Scatter plot saved for {model_name} at {scatter_plot_path}")
            
            # Call helper function to generate bar plot for parameter combinations
            plot_parameter_combinations(df, model_name, model_results_path)


# Main function to generate visualizations
def generate_visualizations(metrics_folder="logs/models_results/overall_results", results_folder="results"):
    """Generates visual reports to compare model performance based on metrics like accuracy and BLEU scores."""
    generate_scatter_plot(metrics_folder, results_folder)
    generate_complexity_scatter_plot()

