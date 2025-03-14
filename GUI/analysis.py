import numpy as np
import pandas as pd

import os
import glob
import re

os.chdir("GUI")

from gem_control_file import GEMDataFileReader


# Petr defined params in a separate file, but a lot of the parameters referred to pyensemble things. 
params = {
    'here': '/Users/beatlab/Desktop/GEM-prosociality_data/exp_data',
    'num_pacing_clicks': 3
}

'''
NOTE: The easiest way to call the functions that take **kwargs as an input argument is to pass in params, e.g. fetch_experiment_sessions(**params)
'''

def get_file_paths(**kwargs):
    """Search the data repo for runs per date of data collection."""
    # Data repo structure: .../DATE/FILE.gdf
    path = kwargs['here'] + "/**/*.gdf"
    filepaths = glob.glob(path, recursive = True)
    return filepaths

def create_run_per_trial_dataframe(filepath, params=params):
    """From a .gdf file of one run, compute the metrics of interest for each trial."""
    # Initialize output dataframe
    run_data = pd.DataFrame()

    # Open .gdf file with GEMDataReader
    gdf = GEMDataFileReader(filepath)
    gdf.read_file()

    # extract metadata from filename
    filename = os.path.basename(filepath) # extract only the filename (remove the directory path)
    pattern = r"GEM_pilot_([\w_]+)-\d+(\w+)_\d+(\w+)_\d+(\w+)_\d+(\w+)"
    match = re.search(pattern, filename)
    if match:
        metadata = {
            'condition': match.group(1),     
            'group_id': match.group(2) + match.group(3) + match.group(4) + match.group(5)
        }

    # Iterate over runs and match up the GEM tapping data with the PyEnsemble data. 
    for curr_run in gdf.run_info:
            # Skip this run if we have no header
            if not curr_run.hdr:
                print(f"No run header ... skipping ...")
                continue 

            # Get the run statistics for this run/trial
            curr_run.compute_stats(**params)

            # Create a dataframe of tapper stats with one row per participant
            ts_df = pd.DataFrame(curr_run.tapper_stats).T
            ts_df.reset_index(names = 'p_id', inplace = True) # JLS: reset index to merge with metadata_df

            # Get run metadata and metronome stats
            metadata.update(curr_run.hdr)
            metadata.update(curr_run.metronome_stats)
            metadata.update(curr_run.group_stats)
            
            # Create a dataframe. Have to create a "row" by passing the dictionary in as a list
            metadata_df = pd.DataFrame([metadata])

            # Replicate it across rows
            metadata_df = metadata_df.loc[np.repeat(metadata_df.index, ts_df.shape[0])].reset_index(drop=True)

            # Concatentate
            new_df = metadata_df.merge(ts_df, left_index=True, right_index=True)
            
            # Append to session data
            if run_data.empty:
                run_data = new_df 

            else:
                run_data = pd.concat([run_data, new_df]).reset_index(drop=True)
			
    return run_data

# iterate over files
df = pd.DataFrame() # initiate results dataframe
filepaths = get_file_paths(**params) # get all files in result directory
for file in filepaths:
    run_data = create_run_per_trial_dataframe(file, params=params)
    if df.empty:
        df =  run_data

    else:
        df = pd.concat([df, run_data]).reset_index(drop=True)

# remove time from p_id column, keep only two letters
df['p_id'] = df['p_id'].str.replace(r'\d+', '', regex=True)

# save to csv
out_path = params['here'] + '/df.csv'
df.to_csv(out_path, index=False) 