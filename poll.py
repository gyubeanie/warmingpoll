import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# Install streamlit-drawable-canvas if not already installed
# !pip install streamlit-drawable-canvas

# Set canvas dimensions and mapping parameters
canvas_width = 800
canvas_height = 400

years_min = 2020
years_max = 2100
temp_min = 0.0  # Temperature increase in °C
temp_max = 5.0

st.title('Draw Your Expected Global Temperature Trajectory')

st.write("""
Use the canvas below to draw your expected global temperature increase trajectory from **2020 to 2100**.
- **X-axis**: Year (2020 to 2100)
- **Y-axis**: Temperature Increase (0°C to 5°C)
""")

# Create a canvas component
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=2,
    stroke_color="#000",
    background_color="#fff",
    height=canvas_height,
    width=canvas_width,
    drawing_mode="freedraw",
    key="canvas",
)

data_x = []
data_y = []

if st.button('Submit'):
    if canvas_result.json_data is not None:
        # Extract strokes from the canvas
        objects = canvas_result.json_data["objects"]
        if objects:
            # Process each stroke
            all_points = []
            for obj in objects:
                if obj["type"] == "path":
                    path = obj["path"]
                    x_coords = []
                    y_coords = []
                    for cmd in path:
                        if cmd[0] in ('M', 'L'):
                            x_coords.append(cmd[1])
                            y_coords.append(cmd[2])
                    all_points.append((x_coords, y_coords))

            # Map canvas coordinates to data coordinates
            data_x = []
            data_y = []
            for x_list, y_list in all_points:
                # Convert canvas x (pixels) to years
                data_x.extend([years_min + (x / canvas_width) * (years_max - years_min) for x in x_list])
                # Convert canvas y (pixels) to temperature increase (invert y-axis)
                data_y.extend([temp_max - (y / canvas_height) * (temp_max - temp_min) for y in y_list])

            # Sort data by year
            data = sorted(zip(data_x, data_y))
            data_x, data_y = zip(*data)

            # Interpolate temperatures for each year from 2020 to 2100
            years = np.arange(years_min, years_max + 1)
            temps = np.interp(years, data_x, data_y)

            # Store the response
            responses_file = 'responses.csv'
            response_df = pd.DataFrame([temps], columns=years)
            if os.path.exists(responses_file):
                responses_df = pd.read_csv(responses_file)
                responses_df = pd.concat([responses_df, response_df], ignore_index=True)
            else:
                responses_df = response_df
            responses_df.to_csv(responses_file, index=False)

            st.success('Your response has been recorded.')

            # Load RCP data
            try:
                rcp_data = pd.read_csv('rcp_data.csv')
            except Exception as e:
                # Create dummy RCP data if file not found
                rcp_years = list(range(2020, 2101))
                rcp_data = pd.DataFrame({
                    'Year': rcp_years,
                    'RCP2.6': [1 + 0.8 * ((i - 2020) / 80) ** 0.5 for i in rcp_years],
                    'RCP4.5': [1 + 1.8 * ((i - 2020)/80) for i in rcp_years],
                    'RCP8.5': [1 + 3.2 * ((i - 2020) / 80) ** 1.5 for i in rcp_years]
                })

            # Plot the results
            fig = go.Figure()

            # Add RCP scenarios
            for scenario in ['RCP2.6', 'RCP4.5', 'RCP8.5']:
                fig.add_trace(go.Scatter(x=rcp_data['Year'], y=rcp_data[scenario], mode='lines', name=scenario))

            # Add individual responses
            for idx, row in responses_df.iterrows():
                fig.add_trace(go.Scatter(x=years, y=row.values, mode='lines',
                                         line=dict(color='rgba(100,100,100,0.2)'), showlegend=False))

            # Add average response
            avg_response = responses_df.mean()
            fig.add_trace(go.Scatter(x=years, y=avg_response, mode='lines', name='Average Response',
                                     line=dict(color='blue', width=4)))

            fig.update_layout(
                title='Global Temperature Increase Projections',
                xaxis_title='Year',
                yaxis_title='Temperature Increase (°C)',
                yaxis_range=[0, 5],
                showlegend=True,
                width=800,
                height=600
            )

            st.plotly_chart(fig)
            st.write(f"Number of responses: {len(responses_df)}")

        else:
            st.error("Please draw your expected temperature trajectory before submitting.")
    else:
        st.error("Please draw your expected temperature trajectory before submitting.")
