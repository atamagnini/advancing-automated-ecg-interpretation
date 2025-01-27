import pandas as pd
import os
import random
from tqdm import tqdm

def extract_patient_info(header_content):
    patient_info = {}
    for line in header_content:
        if "Age" in line:
            patient_info['Age'] = line.split(':')[-1].strip()
        elif "Sex" in line:
            patient_info['Sex'] = line.split(':')[-1].strip()
        elif "Dx" in line:
            dx_full = line.split(':')[-1].strip()
            # Keep only the first value if multiple Dx values are separated by commas
            patient_info['Dx'] = dx_full.split(',')[0].strip()
    return patient_info

def process_files(header_file_path, data_file_path):
    with open(header_file_path, 'r') as file:
        header_content = file.readlines()

    patient_info = extract_patient_info(header_content)
    header_df = pd.read_csv(header_file_path, header=None, sep=" ", engine='python')
    data_df = pd.read_csv(data_file_path, header=None)
    
    leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
    lead_mapping = {}
    for _, row in header_df.iterrows():
        entries = list(filter(None, row[0].strip().split(' ')))
        if entries[-1] in leads:
            lead_mapping[entries[-1]] = int(entries[-4])
    
    used_indices = set()
    merged_data = {lead: [] for lead in leads}
    for lead in leads:
        match_value = lead_mapping.get(lead)
        if match_value is not None:
            matched_rows = data_df[data_df.iloc[:, 0] == match_value]
            for idx, row in matched_rows.iterrows():
                if idx not in used_indices:
                    merged_data[lead] = row[1:].values
                    used_indices.add(idx)
                    break
        if len(merged_data[lead]) == 0:
            merged_data[lead] = [0] * (data_df.shape[1] - 1)

    merged_df = pd.DataFrame(merged_data).fillna(0)
    merged_df['Age'] = patient_info.get('Age', 'Unknown')
    merged_df['Sex'] = patient_info.get('Sex', 'Unknown')
    merged_df['Dx'] = patient_info.get('Dx', 'Unknown')
    merged_df.insert(0, 'ID', os.path.basename(header_file_path).replace('_header.csv', ''))

    return merged_df

# Directory and file processing
directory = 'data/single_files_csv'
dfs = []
count = 0

# Load SNOMED mappings file
snomed_df = pd.read_csv('data/other_utilities/Physionet Challenge 2020 - SNOMED mappings/SNOMED_mappings_unscored.csv', delimiter=';')
snomed_df['SNOMED CT Code'] = snomed_df['SNOMED CT Code'].astype(str)

pbar = tqdm(total=1000, desc="Processing Files")

while True:
    # Get list of files
    file_list = [filename for filename in os.listdir(directory) if filename.endswith("_header.csv")]

    # Shuffle the list of filenames
    random.shuffle(file_list)

    for filename in file_list:
        header_file_path = os.path.join(directory, filename)
        data_file_path = os.path.join(directory, filename.replace("_header.csv", "_data.csv"))
        merged_df = process_files(header_file_path, data_file_path)

        # Merge SNOMED mappings with final_df to retrieve 'Diagnosis Name' and 'Diagnosis Abbreviation'
        merged_df = pd.merge(merged_df, snomed_df[['SNOMED CT Code', 'Dx', 'Abbreviation']], how='left', left_on='Dx', right_on='SNOMED CT Code')
        merged_df.rename(columns={'Dx_x': 'Dx', 'Dx_y': 'Diagnosis Name', 'Abbreviation': 'Diagnosis Abbreviation'}, inplace=True)
        merged_df.drop('SNOMED CT Code', axis=1, inplace=True)

        # Check for missing values in 'Diagnosis Name' column
        if merged_df['Diagnosis Name'].isnull().any():
            continue  # Continue to next iteration if any 'Diagnosis Name' is missing

        dfs.append(merged_df)
        count += 1
        pbar.update(1)  # Update progress bar
        if count >= 1000:
            break
    else:
        continue  # Continue to next iteration if loop completes without breaking
    break  # Break the outer loop if count reaches 1000

final_df = pd.concat(dfs, ignore_index=True)
print(final_df)

# Saving the df
final_df.to_csv('data/merged_data_1000(test).csv', index=False)

pbar.close()  # Close progress bar