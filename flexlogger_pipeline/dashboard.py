import pandas as pd
import os
import streamlit as st
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st_autorefresh(interval=5000)  # Refresh every 5 seconds

folder_path = "g:/Shared drives/Sharing - General/Technical/Data Analysis/Current Cycling/Logs/"
#folder_path = "/Users/oliverhigbee/Library/CloudStorage/GoogleDrive-oliver.higbee@assetcool.com/Shared drives/Sharing - General/Technical/Data Analysis/Current Cycling/Logs/"
designated_folder = "test_2005"
full_path = os.path.join(folder_path, designated_folder)

master_file = os.path.join(full_path, "master_logs.csv")

if not os.path.exists(master_file):
    st.warning("master_logs.csv does not exist yet")
    st.stop()

try:
    df = pd.read_csv(master_file)
except PermissionError:
    st.warning("master_logs.csv is currently being written to. Please wait a moment and refresh.")
    st.stop()
except pd.errors.EmptyDataError:
    st.warning("master_logs.csv is empty. Please wait for data to be processed and refresh.")
    st.stop()

df = df.sort_values("index")    
df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
fig = px.line(
    df,
    x='time', #time
    y=["SE02_temp", "AA03_temp", "uncoated_temp", "uncoated_2_temp"], #temperature columns
    color_discrete_sequence=["#23b7cf", "#0f314d", "#9d9d9c", "#5a5a5a"],
    labels={"value": "Temperature (°C)", "time": "Time"},
    title='Dashboard Trial'
)

#st.write(df.columns.tolist())

# st.write("Stable segment true count:")
# st.write(df["stable_segment"].sum())

# st.write(df[["time", "AA03_temp", "AA03_temp_stable_start_marker", "stable_segment"]].tail(20))

#max_temp = df[["SE02_temp", "AA03_temp", "uncoated_temp", "uncoated_2_temp"]].max().max()

#add stable segment annotations
start_col = "AA03_temp_stable_start_marker"
if start_col in df.columns:
    stable_start_df = df[df[start_col].notna()]

    st.write("Stable start markers:", len(stable_start_df))

    for _, row in stable_start_df.iterrows():
        x_val = row["time"]

        fig.add_shape(
            type="line",
            x0=x_val,
            x1=x_val,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(
                color="green",
                width=2,
                dash="dash"
            )
        )
        fig.add_annotation(
            x=x_val,
            y=1,
            xref="x",
            yref="paper",
            text="Stable Start",
            showarrow=False,
            yanchor="bottom",
            font=dict(color="green")
        )

#2nd part: end markers
end_col = "AA03_temp_stable_end_marker"
if end_col in df.columns:
    stable_end_df = df[df[end_col].notna()]

    st.write("Stable end markers:", len(stable_end_df))

    for _, row in stable_end_df.iterrows():
        x_val = row["time"]

        fig.add_shape(
            type="line",
            x0=x_val,
            x1=x_val,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(
                color="red",
                width=2,
                dash="dash"
            )
        )
        fig.add_annotation(
            x=x_val,
            y=1,
            xref="x",
            yref="paper",
            text="Stable End",
            showarrow=False,
            yanchor="bottom",
            font=dict(color="red")
        )


# if "AA03_stable_segment" in df.columns:
#     stable = df["AA03_stable_segment"].astype(str).str.lower().isin(["true", "1"])
#     segment_id = (stable != stable.shift()).cumsum()

#     for _, segment in df[stable].groupby(segment_id[stable]):
#         fig.add_vrect(
#             x0=segment["time"].iloc[0],
#             x1=segment["time"].iloc[-1],
#             fillcolor="green",
#             opacity=0.08,
#             line_width=0,
#         )

#for the table of metrics
# spike_indexes = spike_df['index'].srot_values().tolist()
# results = []
# for i in range(len(spike_indexes)-1):
#     start_idx = spike_indexes[i]
#     end_idx = spike_indexes[i+1]

#     segment = df[(df["index"]>=start_idx) & (df["index"]<end_idx)].copy()

#     if segment.empty:
#         continue

#     segment["SE02_diff"] = segment["SE02_temp"] - segment["uncoated_temp"]
#     segment["abs_temp_diff"] = segment["SE02_minus_uncoated"].abs()

#     max_row = segment.loc[segment["abs_temp_diff"].idxmax()]

#     results.append({
#         "Segment": i+1,
#         "start_idx": start_idx,
#         "end_idx": end_idx,
#         "start_time": segment["time"].iloc[0],
#         "end_time": segment["time"].iloc[-1],
#         "max_temp_diff": max_row["abs_temp_diff"],
#     })

#diff_table = pd.DataFrame(results)

fig.update_xaxes(
    dtick = 2*60*1000, #2 minute intervals 
    tickformat="%H:%M:%S"
)    
fig.update_layout(
    height=600,
    width=2000,
)
st.plotly_chart(fig, use_container_width=True)
