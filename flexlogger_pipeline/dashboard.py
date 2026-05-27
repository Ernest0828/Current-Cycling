import pandas as pd
import os
import streamlit as st
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from functions import detect_stable_segments, smoothen


st.set_page_config(layout="wide")
st_autorefresh(interval=5000)  # Refresh every 5 seconds

FILE_LINK = "https://drive.google.com/file/d/1tjzbtzE0oCvdu5gYZCwwuHM5bN_LbfLT/view"
ID = "1tjzbtzE0oCvdu5gYZCwwuHM5bN_LbfLT"
csv_url = f"https://drive.google.com/uc?export=download&id={ID}"

folder_path = "g:/Shared drives/Sharing - General/Technical/Data Analysis/Current Cycling/Logs/"
#folder_path = "/Users/oliverhigbee/Library/CloudStorage/GoogleDrive-oliver.higbee@assetcool.com/Shared drives/Sharing - General/Technical/Data Analysis/Current Cycling/Logs/"
designated_folder = "Quanta Project"
full_path = os.path.join(folder_path, designated_folder)

master_file = os.path.join(full_path, "master_logs.csv")
@st.cache_data(ttl=30)
def load_data():
    return pd.read_csv(csv_url)
# if not os.path.exists(master_file):
#     st.warning("master_logs.csv does not exist yet")
#     st.stop()

try:
    #df = pd.read_csv(master_file)
    df = load_data()

    temp_cols = ["AA03_temp", "SE02_temp", "uncoated_temp", "uncoated_2_temp"]
    for temp in temp_cols:
        df[temp] = pd.to_numeric(df[temp], errors="coerce")

    df = smoothen(df, temp_cols, window_size=120) #smooth over number of samples (1 sample/second)

    df = detect_stable_segments(
        df,
        col="SE02_temp",
        smooth_window=90, #smooth over 90s 
        gradient_window=120, #judge trend over 2 mins
        stable_threshold=0.02, #if average gradient is +- 0.02, considered stable (2.4F/2mins)
        min_stable_length=300, #must be stable for at least 5 mins
        rise_threshold=0.15, #must have a rise of at least 0.15F/s or 18F/2 mins to be considered a valid stable segment
        lookback_window=600 #look back 10 mins to find the rise before stable segment
    )
    df = detect_stable_segments(
        df,
        col="AA03_temp",
        smooth_window=90,
        gradient_window=120,
        stable_threshold=0.02,
        min_stable_length=300,
        rise_threshold=0.15,
        lookback_window=600
    )
except PermissionError:
    st.warning("master_logs.csv is currently being written to. Please wait a moment and refresh.")
    st.stop()
except pd.errors.EmptyDataError:
    st.warning("master_logs.csv is empty. Please wait for data to be processed and refresh.")
    st.stop()

df = df.sort_values("index_sample")  
 
df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S')
plot_df = df.rename(columns={
    "SE02_temp": "ACSR Drake/SE02",
    "uncoated_temp": "ACSR Drake",
    "AA03_temp": "TS Killdeer/AA03",
    "uncoated_2_temp": "TS Killdeer",
})

fig = px.line(
    plot_df,
    x='time', #time
    y=["ACSR Drake/SE02", "ACSR Drake"], #temperature columns
    color_discrete_sequence=["#23b7cf", "#9d9d9c"],
    labels={"value": "Temperature (°F)", "time": "Time"},
    title='SE02 Performance'
)


fig_2 = px.line(
    plot_df,
    x='time', #time
    y=["TS Killdeer/AA03", "TS Killdeer"], #temperature columns
    color_discrete_sequence=["#23b7cf", "#9d9d9c"], #0f314d
    labels={"value": "Temperature (°F)", "time": "Time"},
    title='AA03 Performance'
)
#for printing out col names
#st.write(df.columns.tolist())
# st.write("Stable segment true count:")
# st.write(df["stable_segment"].sum())

# st.write(df[["time", "AA03_temp", "AA03_temp_stable_start_marker", "stable_segment"]].tail(20))

#max_temp = df[["SE02_temp", "AA03_temp", "uncoated_temp", "uncoated_2_temp"]].max().max()

#add stable segment annotations
start_col = "SE02_temp_stable_start_marker"
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
end_col = "SE02_temp_stable_end_marker"
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

#start table
segment_col = "SE02_temp_segment_id"

if segment_col in df.columns:
    segment_df = df[df[segment_col].notna()].copy()

    if not segment_df.empty:
        segment_df["temp_difference"] = (
            segment_df["uncoated_temp"] - segment_df["SE02_temp"]
        ).abs()
        cooling = (segment_df["uncoated_temp"] - segment_df["SE02_temp"])/segment_df["uncoated_temp"] * 100
        segment_df["Cooling (%)"] = cooling
        summary_table = (
            segment_df
            .groupby(segment_col)
            .agg(
                uncoated_temp = ("uncoated_temp", "mean"),
                se02_temp = ("SE02_temp", "mean"),
                cooling = ("Cooling (%)", "mean"),
                avg_temp_difference=("temp_difference", "mean"),
                max_temp_difference=("temp_difference", "max"),
            )
            .reset_index()
            .rename(columns={
                segment_col: "Segment",
                
                "uncoated_temp": "ACSR Drake Mean Temp (°F)",
                "se02_temp": "ACSR Drake/SE02 Mean Temp (°F)",
                "cooling": "Cooling (%)",
                "avg_temp_difference": "Avg temp difference (°F)",
                "max_temp_difference": "Max temp difference (°F)",
            })
        )

        summary_table["Segment"] = summary_table["Segment"].astype(int)

        summary_table["Avg temp difference (°F)"] = summary_table["Avg temp difference (°F)"].round(2)
        summary_table["Max temp difference (°F)"] = summary_table["Max temp difference (°F)"].round(2)

        st.subheader("Stable Temperature Difference (SE02 vs Uncoated)")
        st.dataframe(summary_table, use_container_width=True, hide_index=True)

    else:
        st.info("No stable segments detected yet.")
else:
    st.info(f"{segment_col} column not found.")

#PLOTLY FOR AA03
fig.update_xaxes(
    dtick = 10*60*1000, #10 minute intervals 
    tickformat="%H:%M:%S"
)    
fig.update_layout(
    height=600,
    width=2000,
)
st.plotly_chart(fig, use_container_width=True)

start_col_2 = "AA03_temp_stable_start_marker"
if start_col_2 in df.columns:
    stable_start_df_2 = df[df[start_col_2].notna()]

    st.write("AA03 Stable start markers:", len(stable_start_df_2))

    for _, row in stable_start_df_2.iterrows():
        x_val = row["time"]

        fig_2.add_shape(
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
        fig_2.add_annotation(
            x=x_val,
            y=1,
            xref="x",
            yref="paper",
            text="Stable Start",
            showarrow=False,
            yanchor="bottom",
            font=dict(color="green")
        )

end_col_2 = "AA03_temp_stable_end_marker"
if end_col_2 in df.columns:
    stable_end_df_2 = df[df[end_col_2].notna()]

    st.write("AA03 Stable end markers:", len(stable_end_df_2))

    for _, row in stable_end_df_2.iterrows():
        x_val = row["time"]

        fig_2.add_shape(
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
        fig_2.add_annotation(
            x=x_val,
            y=1,
            xref="x",
            yref="paper",
            text="Stable End",
            showarrow=False,
            yanchor="bottom",
            font=dict(color="red")
        )

segment_col_2 = "AA03_temp_segment_id"

if segment_col_2 in df.columns:
    segment_df = df[df[segment_col_2].notna()].copy()
    if not segment_df.empty:
        segment_df["temp_difference"] = (
            segment_df["uncoated_2_temp"] - segment_df["AA03_temp"]
        ).abs()

        summary_table_2 = (
            segment_df
            .groupby(segment_col_2)
            .agg(
                
                uncoated_temp = ("uncoated_2_temp", "mean"),
                aa03_temp = ("AA03_temp", "mean"),
                avg_temp_difference=("temp_difference", "mean"),
                max_temp_difference=("temp_difference", "max"),
            )
            .reset_index()
            .rename(columns={
                segment_col_2: "Segment",
                
                "uncoated_temp": "TS Killdeer Mean Temp (°F)",
                "aa03_temp": "TS Killdeer/AA03 Mean Temp (°F)",
                "avg_temp_difference": "Avg temp difference (°F)",
                "max_temp_difference": "Max temp difference (°F)",
            })
        )

        summary_table_2["Segment"] = summary_table_2["Segment"].astype(int)

        summary_table_2["Avg temp difference (°F)"] = summary_table_2["Avg temp difference (°F)"].round(2)
        summary_table_2["Max temp difference (°F)"] = summary_table_2["Max temp difference (°F)"].round(2)
        

        st.subheader("Stable Temperature Difference (AA03 vs Uncoated)")
        st.dataframe(summary_table_2, use_container_width=True, hide_index=True)

    else:
        st.info("No stable segments detected yet.")



fig_2.update_xaxes(
    dtick = 10*60*1000, #10 minute intervals 
    tickformat="%H:%M:%S"
)    
fig_2.update_layout(
    height=600,
    width=2000,
)

st.plotly_chart(fig_2, use_container_width=True)
