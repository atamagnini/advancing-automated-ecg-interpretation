#Data conversion to csv 

import os
import numpy as np
import pandas as pd
from scipy.io import loadmat

def convert_to_csv(data_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Walk through all directories and files in the data folder
    for subdir, dirs, files in os.walk(data_folder):
        for filename in files:
            if filename.endswith(".mat"):
                mat_filepath = os.path.join(subdir, filename)
                hea_filepath = mat_filepath.replace('.mat', '.hea')
                
                # Check if the corresponding header file also exists
                if os.path.exists(hea_filepath):
                    # Load .mat file
                    mat_data = loadmat(mat_filepath)
                    data = np.asarray(mat_data['val'], dtype=np.float64)
                    df_data = pd.DataFrame(data)
                    
                    # Load .hea file
                    with open(hea_filepath, 'r') as file:
                        header_data = file.readlines()
                    df_header = pd.DataFrame(header_data, columns=['Header_Info'])
                    
                    # Save to CSV in the output folder
                    csv_data_path = os.path.join(output_folder, filename.replace('.mat', '_data.csv'))
                    csv_header_path = os.path.join(output_folder, filename.replace('.mat', '_header.csv'))
                    
                    df_data.to_csv(csv_data_path, index=False)
                    df_header.to_csv(csv_header_path, index=False)
                    
    print("Conversion complete. CSV files saved to:", output_folder)

data_folder = 'data/single_folder_data'
output_folder = 'data/single_files_csv'
convert_to_csv(data_folder, output_folder)