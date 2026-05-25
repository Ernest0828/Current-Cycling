import numpy as np
import pandas as pd
import re
import os
import time
from datetime import timedelta
import scipy
import scipy.stats as stats 
from scipy.signal import find_peaks

#1st step is to read the data
#2nd step are to apply the necessary smoothening
#3rd step is to contatenate the data into a master_df

#1st function is to read the data and return it as a dataframe
def read_data(file_path):
    #example format is in log-{DDMMYYYY}-{HH}_{MM}.csv, first MM is month, second is the minute
    #e.g. log-05052026-13-55.csv then log-05052026-15-55.csv
    #file_regex = r'LogFile_(\d{2})(\d{2})(\d{4})-(\d{2})-(\d{2}).csv.csv'
    file_regex = r'LogFile_(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2}).csv'
    #strip the .csv from the file name
    
    file_name = os.path.basename(file_path)
    
    match = re.fullmatch(file_regex, file_name)

    if not match:
        raise ValueError("File path does not match expected format, ignoring it...")
    
    df = pd.read_csv(file_path)
    return df #after calling this function, will call the outlier and smoothening functions
    
def remove_outliers_rolling(df, col, window, threshold):
    #2 step process, 1st is applying rolling median to remove outliers, then SMA for smoothing
    rolling_median = df[col].rolling(window, center=True, min_periods=1).median()
    diff = abs(df[col] - rolling_median)

    removed = df.loc[diff>=threshold]
    print(f"Removed {len(removed)} outliers from column {col} using rolling median with window {window} and threshold {threshold}.")

    return df[diff<threshold]

def smoothen(df, cols, window_size):
    df = df.copy()

    df[cols] = (df[cols].rolling(window=window_size, min_periods=1).mean())
    return df

#table_id = 'our-lamp-495415-f5.flexlogger_data.temperature'


def clean_cols(df):
    #concat all columns that start with "AA03" into one column, and all columns that start with "Uncoated" into another column, then return the dataframe with only these 2 columns
    aa03_cols = df.filter(regex=r'^AA03',axis=1) #example is AA03-1-1, AA03-1-2...
    uncoated_cols = df.filter(regex=r'^UN-1',axis=1) #example is UN-1-1, UN-1-2... there are also UN-2-1, UN-2-2 but we will keep those separate as uncoated_2
    se02_cols = df.filter(regex=r'^SE02',axis=1)
    uncoated_cols_2 = df.filter(regex=r'^UN-2',axis=1)
    
    return pd.DataFrame({
        #"Time": df["Time"],
        "AA03": aa03_cols.mean(axis=1), #take the mean of all columns that start with AA03
        "Uncoated": uncoated_cols.mean(axis=1), #take the mean of all columns that start with Uncoated
        "Uncoated_2": uncoated_cols_2.mean(axis=1), #take the mean of all columns that start with Uncoated_2
        "SE02": se02_cols.mean(axis=1) #take the mean of all columns that start with SE02
    })

def process_new_csvs(folder_path, col, col2, col3, col4):
    #folder_path = "G:/Shared drives/Sharing - General/Technical/Data Analysis/Current Cycling/Logs"
    master_file = os.path.join(folder_path, "master_logs.csv")

    processed_log = os.path.join(folder_path, "processed_logs.txt")

    if os.path.exists(master_file):
        master_df = pd.read_csv(master_file)
    else:
        master_df = pd.DataFrame()
    #master_df = pd.DataFrame()

    if os.path.exists(processed_log):
        with open(processed_log, 'r') as f:
            processed_files = set(line.strip() for line in f)
    else:
        processed_files = set()

    updated = False    

    for file in os.listdir(folder_path):
        if not file.endswith(".csv"):
            continue

        if file.endswith("_smoothed.csv") or file == "master_logs.csv":
            continue

        if file in processed_files:
            continue
        
        file_path = os.path.join(folder_path, file)
        print(file_path)

        try:
            print(f"Processing {file}...")
            df = read_data(file_path)
            df = clean_cols(df)

            df = remove_outliers_rolling(df, col, window=20, threshold=5)
            #df = smoothen(df[[col, col2, col3, col4]], window_size=10)

            #df.to_csv(file_path.replace(".csv", "_smoothed.csv"), index=False)

            df['source_file'] = file

            #big query gets called here
            
            #df = detect_stable_segments(df, col)
            

            # start_index = len(master_df)
            index_col = "index_sample"

            if master_df.empty:
                start_index = 0
            elif index_col in master_df.columns:
                start_index = master_df[index_col].max() + 1
            else:                
                start_index = len(master_df)

            df = df.reset_index(drop=True)
            df[index_col] = range(start_index, start_index + len(df))

            seconds = df[index_col]
            df['time'] = seconds.apply(
                lambda x: pd.Timestamp("00:00:00") + pd.Timedelta(seconds=int(x))
            ).dt.time
            
            COLUMN_MAPPING = {
                col: "AA03_temp",
                col2: "SE02_temp",
                col3: "uncoated_temp",
                col4: "uncoated_2_temp",
            }
            df = df.rename(columns=COLUMN_MAPPING)


            #upload_to_bigquery(df, table_id) # IMPORTANT PART FOR BIGQUERY

            master_df = pd.concat([master_df, df], ignore_index=True)

            #smoothen all 4 cols in the entire dataset iteratively
            # temp_cols = ["AA03_temp", "SE02_temp", "uncoated_temp", "uncoated_2_temp"]
            # master_df = smoothen(master_df, temp_cols, window_size=10)
            #rint(master_df.columns.tolist())

            stable_cols = [
                "stable_marker",
                "stable_segment",
                "AA03_temp_stable_marker",
                "AA03_temp_stable_segment",
            ]
            master_df = master_df.drop(
                columns=[c for c in stable_cols if c in master_df.columns]
            )
            #master_df = detect_stable_segments(master_df, "AA03_temp")
            #master_df = detect_stable_segments(master_df, "SE02_temp")
            master_df = master_df.rename(columns={
                "AA03_temp_stable_marker": "stable_marker",
                "AA03_temp_stable_segment": "stable_segment",
            })
            updated = True 

            processed_files.add(file)

            with open(processed_log, 'a') as f:
                f.write(file + '\n')

            updated = True    

        except ValueError as e:
            print(f"Error processing {file}: {e}")

    if updated:
        master_df.to_csv(master_file, index=False)
        print("master_logs.csv updated")
       # upload_to_bigquery(master_df, "current_cycling.logs.master_logs") #configure this
    else:
        print("No new files detected.")    


def main():
    FILE_FOLDER = "G:/Shared drives/Sharing - General/Technical/Data Analysis/Current Cycling/Logs/test_2005"
    #FILE_FOLDER = "/Users/oliverhigbee/Library/CloudStorage/GoogleDrive-oliver.higbee@assetcool.com/Shared drives/Sharing - General/Technical/Data Analysis/Current Cycling/Logs/test_2005"
    #no need to connetc to session anymore, just loop through folder and check new files with timer of 300s
    while True:
        print("Starting loop, checking new files...")
        processed_count = process_new_csvs(FILE_FOLDER, col="AA03", col2="SE02", col3="Uncoated", col4="Uncoated_2")  # Function to process new CSV files
        #if no new files, will print "No new files detected." and sleep for 300s before checking again
        if processed_count == 0:
            print("No new files detected.")
        time.sleep(30)

if __name__ == "__main__":    
    main()


