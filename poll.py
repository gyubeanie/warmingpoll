import streamlit as st
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

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

The **RCP pathways** are displayed on the canvas for reference.
""")

# Load RCP data
try:
    rcp_data = pd.read_csv('rcp_data.csv')
except Exception as e:
    # Create dummy RCP data if file not found
    rcp_years = list(range(years_min, years_max + 1))
    rcp_data = pd.DataFrame({
        'Year': rcp_years,
        'RCP2.6': [1 + 0.8 * ((i - 2020) / 80) ** 0.5 for i in rcp_years],
        'RCP4.5': [1 + 1.8 * ((i - 2020)/80) for i in rcp_years],
        'RCP8.5': [1 + 3.2 * ((i - 2020) / 80) ** 1.5 for i in rcp_years]
    })

# Function to map data coordinates to canvas coordinates
def data_to_canvas_coords(x, y):
    canvas_x = ((x - years_min) / (years_max - years_min)) * canvas_width
    canvas_y = canvas_height - ((y - temp_min) / (temp_max - temp_min)) * canvas_height
    return canvas_x, canvas_y

# Create initial drawing with RCP pathways
def create_initial_drawing(rcp_data):
    initial_drawing_objects = []
    colors = {'RCP2.6': 'green', 'RCP4.5': 'orange', 'RCP8.5': 'red'}

    # Add axes lines
    # X-axis
    x_axis = {
        'type': 'line',
        'x1': 0,
        'y1': canvas_height,
        'x2': canvas_width,
        'y2': canvas_height,
        'stroke': 'black',
        'strokeWidth': 2,
        'selectable': False
    }
    initial_drawing_objects.append(x_axis)

    # Y-axis
    y_axis = {
        'type': 'line',
        'x1': 0,
        'y1': 0,
        'x2': 0,
        'y2': canvas_height,
        'stroke': 'black',
        'strokeWidth': 2,
        'selectable': False
    }
    initial_drawing_objects.append(y_axis)

    # Add RCP pathways
    for scenario in ['RCP2.6', 'RCP4.5', 'RCP8.5']:
        data_x = rcp_data['Year'].values
        data_y = rcp_data[scenario].values

        # Map data x and y to canvas coordinates
        canvas_coords = [data_to_canvas_coords(x, y) for x, y in zip(data_x, data_y)]
        path_data = []
        for idx, (x, y) in enumerate(canvas_coords):
            cmd = 'M' if idx == 0 else 'L'
            path_data.append([cmd, x, y])

        path_object = {
            'type': 'path',
            'path': path_data,
            'fill': None,
            'stroke': colors[scenario],
            'strokeWidth': 2,
            'selectable': False,
        }

        initial_drawing_objects.append(path_object)

    # Return the initial drawing data
    initial_drawing = {'version': '4.6.0', 'objects': initial_drawing_objects}
    return initial_drawing

# Create the initial drawing
initial_drawing = create_initial_drawing(rcp_data)

# Create a canvas component with the initial drawing
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=2,
    stroke_color="#0000FF",
    background_color="#FFFFFF",
    initial_drawing=initial_drawing,
    update_streamlit=True,
    height=canvas_height,
    width=canvas_width,
    drawing_mode="freedraw",
    key="canvas",
)

if st.button('Submit'):
    if canvas_result.json_data is not None:
        # Extract strokes from the canvas
        objects = canvas_result.json_data["objects"]
        if objects:
            # Filter out the initial objects (axes and RCP pathways)
            user_objects = [obj for obj in objects if obj.get('stroke') == '#0000FF' or obj.get('stroke') == '#000']  # Assuming user's strokes are blue or black

            if user_objects:
                # Process each stroke
                all_points = []
                for obj in user_objects:
                    if obj["type"] == "path":
                        path = obj["path"]
                        x_coords = []
                        y_coords = []
                        for cmd in path:
                            if cmd[0] in ('M', 'L'):
                                x_coords.append(cmd[1])
                                y_coords.append(cmd[2])
                        all_points.append((x_coords, y_coords))

                if all_points:
                    # Map canvas coordinates to data coordinates
                    data_x = []
                    data_y = []
                    for x_list, y_list in all_points:
                        # Convert canvas x (pixels) to years
                        data_x.extend([years_min + (x / canvas_width) * (years_max - years_min) for x in x_list])
                        # Convert canvas y (pixels) to temperature increase (invert y-axis)
                        data_y.extend([temp_min + ((canvas_height - y) / canvas_height) * (temp_max - temp_min) for y in y_list])

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

                    # Plot the results
                    fig = go.Figure()

                    # Add RCP scenarios
                    for scenario in ['RCP2.6', 'RCP4.5', 'RCP8.5']:
                        fig.add_trace(go.Scatter(x=rcp_data['Year'], y=rcp_data[scenario], mode='lines', name=scenario))

                    # Add individual responses
                    for idx, row in responses_df.iterrows():
                        if idx == len(responses_df) - 1:
                            # Highlight the user's own response
                            fig.add_trace(go.Scatter(x=years, y=row.values, mode='lines',
                                                     line=dict(color='red', width=3), name='Your Response'))
                        else:
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
                        yaxis_range=[temp_min, temp_max],
                        showlegend=True,
                        width=800,
                        height=600
                    )

                    st.plotly_chart(fig)
                    st.write(f"Number of responses: {len(responses_df)}")

                    # Calculate the user's predicted warming in 2100
                    user_2100_temp = temps[-1]

                    # Get all users' 2100 temperatures
                    all_2100_temps = responses_df[str(2100)].values

                    # Calculate percentile
                    percentile = (np.sum(all_2100_temps < user_2100_temp) / len(all_2100_temps)) * 100

                    percentile = round(percentile, 1)
                    user_2100_temp = round(user_2100_temp, 2)

                    if percentile == 50:
                        comparison = 'equal to the median of'
                    elif percentile > 50:
                        comparison = f'higher than {percentile}% of'
                    else:
                        comparison = f'lower than {100 - percentile}% of'

                    st.write(f"Your predicted warming in 2100 is **{user_2100_temp}°C**, "
                             f"which is {comparison} other users.")

                else:
                    st.error("Please draw your expected temperature trajectory before submitting.")
            else:
                st.error("Please draw your expected temperature trajectory before submitting.")
        else:
            st.error("Please draw your expected temperature trajectory before submitting.")
