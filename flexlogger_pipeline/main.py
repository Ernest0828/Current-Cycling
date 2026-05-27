import sys
import pandas as pd
import os
import time

from flexlogger.automation import Application
from process import process_new_csvs

# def main():
#     """Connect to an already running instance of FlexLogger with an open project"""
#     app = Application()
#     project = app.get_active_project()
#     if project is None:
#         print("No project is open in FlexLogger!")
#         return 1
#     test_session_state = project.test_session.state
#     print(f"The test session state is : {test_session_state}")
#     print("Press Enter to disconnect from FlexLogger...")
#     input()
#     app.disconnect()
#     return 0


# if __name__ == "__main__":
#     sys.exit(main())
FILE_FOLDER = "G:/Shared drives/Sharing - General/Technical/Data Analysis/Current Cycling/Logs/"

def log_every_hour():
    seen_files = set()

    while True:
        files = [f for f in os.listdir(FILE_FOLDER) if f.endswith('.csv')]

        for filename in files:
            if filename not in seen_files:
                full_path = os.path.join(FILE_FOLDER, filename)
                print(f"New file detected: {filename}")
                
                process_new_csvs(FILE_FOLDER, col="21.174")  # Function to process new CSV files
                seen_files.add(filename)

        time.sleep(300) # Check every 5 minutes        

def process_csv(file_path):
    df = pd.read_csv(file_path)
    #processing starts here


def main(project_path):
    """Launch FlexLogger, open a project, start and stop the test session."""
    with Application.launch() as app:
        project = app.open_project(path=project_path)
        # test_session = project.test_session
        # test_session.start()
        try:
            channel_name = input("Enter the name of the channel to read: ")
            channel_specification = project.open_channel_specification_document()
            channel_value = channel_specification.get_channel_value(channel_name)
            print(f"The value of channel '{channel_name}' is: {channel_value}")

        except Exception as e:
            print(f"An error occurred: {e}")
            input("Press Enter to close FlexLogger...")
            project.close()
            return 1

        log_every_hour()

        project.close()
    return 0


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 2:
        print("Usage: %s <path of project to open>" % os.path.basename(__file__))
        sys.exit()
    project_path_arg = argv[1]
    sys.exit(main(project_path_arg))    