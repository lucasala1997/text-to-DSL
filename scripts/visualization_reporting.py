import logging
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from utils import load_config
import re


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
    df['parameters_str'] = df.apply(
        lambda row: f"top_k={row['parameters'].get('top_k', 'N/A')}, "
                    f"top_p={row['parameters'].get('top_p', 'N/A')}, "
                    f"temperature={row['parameters'].get('temperature', 'N/A')}, "
                    f"version={row['system_prompt_version']}",
        axis=1
    )
    
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
    """Generates scatter plots to compare model performance based on temperature and overall accuracy."""
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

def plot_best_performing_combinations(metrics_folder="logs/models_results/overall_results", results_folder="results", top_n=5):
    """Generates a bar plot for the best performing parameter combinations across models based on overall accuracy."""
    
    # Initialize a list to collect all parameter combinations
    all_combinations = []

    # Loop through each overall metrics file in the metrics folder
    for file_name in os.listdir(metrics_folder):
        if file_name.endswith(".json"):
            model_name = file_name.replace("overall_metrics_", "").replace('.json', '').replace('_', ' ')
            
            # Load the JSON data
            with open(os.path.join(metrics_folder, file_name), 'r') as file:
                data = json.load(file)

            # Add model name and combination data to the list
            for entry in data:
                all_combinations.append({
                    'model_name': model_name,
                    'parameters': entry['parameters'],
                    'overall_accuracy': entry['overall_accuracy']
                })

    # Convert the list to a DataFrame for easier handling
    df = pd.DataFrame(all_combinations)

    # Sort by overall_accuracy and select the top N combinations
    top_combinations = df.nlargest(top_n, 'overall_accuracy')

    # Create a readable string for each parameter combination
    top_combinations['parameters_str'] = top_combinations['parameters'].apply(
        lambda x: f"top_k={x.get('top_k', 'N/A')}, top_p={x['top_p']}, temperature={x['temperature']}"
    )

    # Generate the bar plot
    plt.figure(figsize=(12, 8))
    plt.barh(top_combinations['parameters_str'], top_combinations['overall_accuracy'], color='skyblue')
    plt.xlabel("Overall Accuracy")
    plt.title(f"Top {top_n} Best Performing Parameter Combinations Across Models")
    plt.gca().invert_yaxis()  # Invert y-axis to have the highest accuracy at the top
    plt.tight_layout()

    # Save the plot in the results folder
    plot_path = os.path.join(results_folder, f"top_{top_n}_best_performing_combinations.png")
    plt.savefig(plot_path)
    plt.close()
    
    logging.info(f"Best performing parameter combinations plot saved at {plot_path}")

# def plot_average_processing_times(metrics_folder="logs/models_results/overall_results", results_folder="results"):
#     """Generates a bar plot comparing average processing times for each model based on complexity level."""
    
#     # List to store average times for each model and complexity level
#     time_data = []

#     # Loop through each overall metrics file in the metrics folder
#     for file_name in os.listdir(metrics_folder):
#         if file_name.endswith(".json"):
#             model_name = file_name.replace("overall_metrics_", "").replace('.json', '').replace('_', ' ')
            
#             # Load the JSON data
#             with open(os.path.join(metrics_folder, file_name), 'r') as file:
#                 data = json.load(file)

#             # Extract average times for complex and simple examples
#             for entry in data:
#                 time_data.append({
#                     'model_name': model_name,
#                     'average_complex_time': entry['average_complex_time'],
#                     'average_simple_time': entry['average_simple_time']
#                 })

#     # Convert the list to a DataFrame for easier plotting
#     df = pd.DataFrame(time_data)

#     # Set up the bar plot
#     plt.figure(figsize=(12, 8))
#     bar_width = 0.35
#     x = range(len(df['model_name'].unique()))

#     # Plot complex and simple times side by side
#     plt.bar(x, df['average_complex_time'], width=bar_width, label='Complex Examples', color='salmon')
#     plt.bar([i + bar_width for i in x], df['average_simple_time'], width=bar_width, label='Simple Examples', color='skyblue')

#     # Set the x-tick labels and other plot details
#     plt.xlabel("Model Name")
#     plt.ylabel("Average Processing Time (seconds)")
#     plt.title("Average Processing Time by Model and Complexity Level")
#     plt.xticks([i + bar_width / 2 for i in x], df['model_name'].unique(), rotation=45, ha="right")
#     plt.legend(title="Complexity Level")
#     plt.tight_layout()

#     # Save the plot in the results folder
#     plot_path = os.path.join(results_folder, "average_processing_times_by_complexity.png")
#     plt.savefig(plot_path)
#     plt.close()

#     logging.info(f"Average processing times plot saved at {plot_path}")

def plot_performance_by_vram(metrics_folder="logs/models_results/overall_results", 
                             model_data_file="metadata/model_parameters.json", 
                             results_folder="results"):
    """Generates a bar plot showing model performance by VRAM size categories (<8GB, <24GB, <32GB, <64GB, <90GB, <128GB)."""
    
    # Ensure the results folder exists
    os.makedirs(results_folder, exist_ok=True)
    
    # Load the model data from model_data_file
    with open(model_data_file, 'r') as file:
        model_data = json.load(file)
    
    # Prepare a mapping from model_name to vram_requirement
    model_vram_mapping = {}
    for model_info in model_data.values():
        name = model_info.get('model_name')
        vram = model_info.get('vram_requirement', 'Unknown')
        if name:
            model_vram_mapping[name] = vram
    
    # Define VRAM categories
    def get_vram_category(vram):
        match = re.search(r'(\d+(\.\d+)?)GB', vram)
        if match:
            vram_value = float(match.group(1))
            if vram_value < 8:
                return "<8GB"
            elif vram_value < 24:
                return "<24GB"
            elif vram_value < 32:
                return "<32GB"
            elif vram_value < 64:
                return "<64GB"
            elif vram_value < 90:
                return "<90GB"
            elif vram_value < 128:
                return "<128GB"
            else:
                return ">=128GB"
        return "Unknown"
    
    # Prepare data for plotting
    performance_by_vram = []
    for file_name in os.listdir(metrics_folder):
        if file_name.endswith(".json"):
            # Read the JSON data
            model_file_path = os.path.join(metrics_folder, file_name)
            with open(model_file_path, 'r') as file:
                data = json.load(file)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Extract model name from the file name
            # Remove 'overall_metrics_' prefix and '.json' extension, then replace underscores with spaces
            model_name = file_name.replace('overall_metrics_', '').replace('.json', '').replace('_', ' ')
            
            # Try to find model_info in model_data using the exact model name
            vram_req = model_vram_mapping.get(model_name)
            if vram_req is None:
                logging.warning(f"VRAM data missing for model: {model_name}")
                continue
            
            vram_category = get_vram_category(vram_req)
            
            # Extract performance metric (e.g., 'average_bleu_score')
            if 'average_bleu_score' in df.columns:
                # Get the average of 'average_bleu_score' if there are multiple entries
                model_perf = df['average_bleu_score'].mean()
            else:
                model_perf = 0  # Handle appropriately if the key doesn't exist
            
            performance_by_vram.append({
                "model_name": model_name,
                "vram_category": vram_category,
                "performance": model_perf
            })
    
    # Check if performance_by_vram contains data
    if not performance_by_vram:
        logging.error("No data available for VRAM-based performance plot.")
        return
    
    # Convert to DataFrame for plotting
    df_plot = pd.DataFrame(performance_by_vram)
    
    # Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_plot, x="vram_category", y="performance", hue="vram_category", dodge=False)
    plt.xlabel("VRAM Requirement")
    plt.ylabel("Performance Metric (Average BLEU Score)")
    plt.title("Model Performance by VRAM Requirement")
    #plt.legend(title="VRAM Category")
    
    # Save plot
    plot_path = os.path.join(results_folder, "model_performance_by_vram.png")
    plt.savefig(plot_path)
    plt.close()
    logging.info(f"VRAM-based performance plot saved to {plot_path}")

def plot_performance_by_parameters(metrics_folder="logs/models_results/overall_results",
                                   results_folder="results"):
    """Generates a bar plot showing model performance by parameter categories (<8B, <32B, <70B, >70B)."""

    # Ensure the results folder exists
    os.makedirs(results_folder, exist_ok=True)
    
    # Categorize Parameters
    def get_parameter_category(model_name):
        match = re.search(r'(\d+)B', model_name)
        if match:
            params = int(match.group(1))
            if params < 8:
                return "<8B"
            elif params < 32:
                return "<32B"
            elif params < 70:
                return "<70B"
            else:
                return ">70B"
        return "Unknown"
    
    # Process data
    performance_by_params = []
    for file_name in os.listdir(metrics_folder):
        if file_name.endswith(".json"):
            # Read the JSON data
            model_file_path = os.path.join(metrics_folder, file_name)
            with open(model_file_path, 'r') as file:
                data = json.load(file)
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Extract model name from the file name
            model_name = file_name.replace('.json', '').replace('_', ' ')
            
            # Get parameter category from model name
            param_category = get_parameter_category(model_name)
            
            # Extract performance metric (e.g., 'average_bleu_score')
            if 'average_bleu_score' in df.columns:
                # Get the average of 'average_bleu_score' if there are multiple entries
                model_perf = df['average_bleu_score'].mean()
            else:
                model_perf = 0  # Handle appropriately if the key doesn't exist
            
            performance_by_params.append({
                "model_name": model_name,
                "param_category": param_category,
                "performance": model_perf
            })
    
    # Check if performance_by_params contains data
    if not performance_by_params:
        logging.error("No data available for parameter-based performance plot.")
        return
    
    # Convert to DataFrame and plot
    df_plot = pd.DataFrame(performance_by_params)
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_plot, x="param_category", y="performance", hue="param_category", dodge=False)
    plt.xlabel("Parameter Category")
    plt.ylabel("Performance Metric (Average BLEU Score)")
    plt.title("Model Performance by Parameter Category")
    # plt.legend(title="Parameter Category")

    # Save plot
    plot_path = os.path.join(results_folder, "model_performance_by_parameters.png")
    plt.savefig(plot_path)
    plt.close()
    logging.info(f"Parameter-based performance plot saved to {plot_path}")

# Main function to generate visualizations
def generate_visualizations(metrics_folder="logs/models_results/overall_results", results_folder="results"):
    """Generates visual reports to compare model performance based on metrics like accuracy and BLEU scores."""
    generate_scatter_plot(metrics_folder, results_folder)
    generate_complexity_scatter_plot()
    plot_best_performing_combinations()
    # plot_average_processing_times(metrics_folder, results_folder)  
    plot_performance_by_vram()
    plot_performance_by_parameters()


