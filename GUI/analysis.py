import copy

from django.db.models import Max
from django.core.files.base import ContentFile
from django.db import transaction

from gem_control_file import GEMDataFileReader

import numpy as np
import pandas as pd

import pdb

import os
import glob
import re

# Petr defined params in a separate file, but a lot of the parameters referred to pyensemble things. Let's see if we even need params.
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

    # extract metadata from filepath
    pattern = params['here'] + r"/[^/]+/[^_]+_[^_]+_([^_-]+)-\d+(\w+)_\d+(\w+)_\d+(\w+)_\d+(\w+)"
    match = re.search(pattern, filepath)
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
                run_data = pd.concat([run__data, new_df]).reset_index(drop=True)
			
    return run_data

# TODO create_run_per_trial_dataframe runs, but returns an empty DataFrame despite correctly initialized columns: 
# Columns: [condition, group_id, run_number, start_time, alpha, tempo, met_adjust_mean, met_adjust_std, mean_grp_asynch_per_window, std_grp_asynch_per_window, num_missed, mean_async_rel_met, std_async_rel_met, mean_async_rel_grp, std_async_rel_grp]
# Index: []