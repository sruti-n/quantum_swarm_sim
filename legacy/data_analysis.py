# Credit to Gemini for helping me understand how to use the packages imported in this file 
# to help create graphs and analyze the data obtained from the quantum_robot.py file,
# as well as providing suggestions for improving the code and the data analysis. 

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Find the directory where this script is saved
script_dir = os.path.dirname(os.path.abspath(__file__))

# Find the full path to the CSV file in the same directory as this script
csv_path = os.path.join(script_dir, 'quantum_tests_data.csv')

# Load the data from the CSV file into a pandas DataFrame
data = pd.read_csv(csv_path)
print(data.head()) # Ensures that the header and data are loaded correctly

# Set the style for the graphs
sns.set_context("talk") # Sets the context to "talk" for better readability for the poster session of the research symposium
sns.set_style("whitegrid") # Sets the style to "whitegrid" for better visibility of the grid lines in the graphs
plt.rcParams.update({'font.size': 18}) # Sets the default font size to 18 for better readability in the graphs

"""
Create a line plot to show the effect of noise rate on the error rate for different quantum gates
The x-axis represents the noise rate, the y-axis represents the error rate, and different lines represent 
different quantum gates. The error bars are removed for better visibility of the data points.
"""
plt.figure(figsize=(12, 6)) # Sets the figure size to 12 inches by 6 inches for better visibility in the graphs
sns.lineplot(data=data, x='Noise Rate', y='Angle', hue='Gate Name', errorbar = None, marker='o')

plt.title('Effect of Noise Rate on Angle for Different Quantum Gates') # Sets the title of the graph
plt.xlabel('Noise Rate') # Sets the label for the x-axis
plt.ylabel('Angle (degrees)') # Sets the label for the y-axis
plt.legend(title='Gate Name') # Adds a legend with the title 'Gate Name'
plt.tight_layout() # Adjusts the layout to prevent overlap of elements in the graph
plt.ylim(-5,185) # Sets the limits for the y-axis to better visualize the data points

# Create the full path for the output file
output_path_angle = os.path.join(script_dir, 'quantum_gates_noise_effect.png')
plt.savefig(output_path_angle, format='png', dpi=300, bbox_inches='tight') # Saves the graph as a PNG file with 300 DPI resolution and tight bounding box to ensure all elements are included in the saved image
plt.show() # Displays the graph

"""
Calculate fidelity from error rate and add it as a new column to the DataFrame. Fidelity is calculated 
as 1 - Error Rate, which represents how closely the actual output of the quantum gate matches the 
ideal output. Then, create a line plot to show the effect of noise rate on the fidelity for different 
quantum gates. The x-axis represents the noise rate, the y-axis represents the fidelity, and different
lines represent different quantum gates. The error bars are removed for better visibility of the data 
points.
"""
data['Fidelity'] = 1 - data['Noise Rate'] # Calculate fidelity from error rate and add it as a new column to the DataFrame

# Create a line plot to show the effect of noise rate on the fidelity for different quantum gates
plt.figure(figsize=(12, 6)) # Sets the figure size to 12 inches by 6 inches for better visibility in the graphs
sns.lineplot(data=data, x='Noise Rate', y='Fidelity', hue='Gate Name', errorbar = None, marker='o')

plt.title('Effect of Noise Rate on Fidelity for Different Quantum Gates') # Sets the title of the graph
plt.xlabel('Noise Rate') # Sets the label for the x-axis
plt.ylabel('Fidelity') # Sets the label for the y-axis
plt.legend(title='Gate Name') # Adds a legend with the title 'Gate Name'
plt.tight_layout() # Adjusts the layout to prevent overlap of elements in the graph
plt.xlim(-0.05,1.05) # Sets the limits for the x-axis to better visualize the data points  

# Create the full path for the output file
output_path_fidelity = os.path.join(script_dir, 'quantum_gates_fidelity_effect.png')
plt.savefig(output_path_fidelity, format='png', dpi=300, bbox_inches='tight') # Saves the graph as a PNG file with 300 DPI resolution and tight bounding box to ensure all elements are included in the saved image
plt.show() # Displays the graph

"""
Create a scatterplot to compare the theoretical probabilities of the quantum gates with the experimental 
probabilities obtained from the measurements. The x-axis represents the theoretical probability, the 
y-axis represents the experimental probability, and different colors represent different noise rates. 
A dashed line is added to indicate perfect accuracy (where theoretical probability equals experimental 
probability).
"""
theoretical_prob = {
            'h': 0.5,
            'x': 1.0,
            'id': 0.0,
            'sx': 0.5,
            'y': 1.0,
            'z': 0.0
        }

data['Theoretical Probability'] = data['Gate Name'].map(theoretical_prob) # Map the theoretical probabilities to the DataFrame based on the gate names

plt.figure(figsize=(12, 6)) # Sets the figure size to 12 inches by 6 inches for better visibility in the graphs
sns.scatterplot(data=data, x='Theoretical Probability', y='Probability', hue='Noise Rate', palette = "flare", alpha=0.7)

# 4. Add the "Perfect Accuracy" line (the y=x line)
plt.plot([0, 1], [0, 1], color='black', linestyle='--', linewidth=2, label='Perfect Theory')

plt.title('Theoretical vs Experimental Probability for Different Noise Rates') # Sets the title of the graph
plt.xlabel('Theoretical Probability (Ideal)') # Sets the label for the x-axis
plt.ylabel('Experimental Probability (Measured)') # Sets the label for the y-axis
plt.legend(title='Noise Rate', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()

# Create the full path for the output file
output_path_theoretical_prob = os.path.join(script_dir, 'theoretical_vs_experimental.png')
plt.savefig(output_path_theoretical_prob, format='png', dpi=300, bbox_inches='tight')
plt.show()