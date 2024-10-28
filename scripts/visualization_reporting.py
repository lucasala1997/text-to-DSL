import logging
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# TODO: check and adjust to the new files configuration
def generate_visualizations(metrics_folder="logs/models_results/overall_results", results_folder="results"):
    """Generates visual reports to compare model performance based on metrics like accuracy and BLEU scores.

    This function creates visual representations of model results to support data-driven decision-making.
    """
    
    # Ensure the results folder exists
    os.makedirs(results_folder, exist_ok=True)
    
    # Loop through all metric files and process them
    for file_name in os.listdir(metrics_folder):
        if file_name.endswith(".json"):
            # Derive model name from file name
            model_name = file_name.split("overall_metrics_")[-1].replace('.json', '').replace('_', ' ')
            
            # Read the JSON data
            with open(os.path.join(metrics_folder, file_name), 'r') as file:
                data = json.load(file)
            
            # Convert data to DataFrame
            df = pd.DataFrame(data)
            
            # Extract parameters for plotting
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
            
            # Save the plot
            plot_path = os.path.join(model_results_path, f"{model_name}_accuracy_scatter.png")
            plt.savefig(plot_path)
            plt.close()
            
            logging.info(f"Plot saved for {model_name} at {plot_path}")

# Call the function to generate visualizations
generate_visualizations()
