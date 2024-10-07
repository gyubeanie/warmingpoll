import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# Initialize session state
if 'responses' not in st.session_state:
    st.session_state.responses = []

st.title("Global Warming Trajectory Poll")

# User input
st.write("Draw your expected global warming trajectory from 2020 to 2100.")
st.write("Click and drag on the chart below to draw your trajectory.")

# Create a Plotly figure for user input
fig = go.Figure()

# Add IPCC RCP scenarios
years = list(range(2020, 2101))
rcp26 = [1 + 0.01*i for i in range(81)]  # Simplified RCP 2.6 scenario
rcp45 = [1 + 0.02*i for i in range(81)]  # Simplified RCP 4.5 scenario
rcp85 = [1 + 0.04*i for i in range(81)]  # Simplified RCP 8.5 scenario

fig.add_trace(go.Scatter(x=years, y=rcp26, mode='lines', name='RCP 2.6', line=dict(color='green')))
fig.add_trace(go.Scatter(x=years, y=rcp45, mode='lines', name='RCP 4.5', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=years, y=rcp85, mode='lines', name='RCP 8.5', line=dict(color='red')))

# Add user input trace
fig.add_trace(go.Scatter(x=years, y=[1]*len(years), mode='lines', name='Your input',
                         line=dict(color='blue'), hoverinfo='none'))

fig.update_layout(
    title='Global Temperature Increase (°C)',
    xaxis_title='Year',
    yaxis_title='Temperature Increase (°C)',
    yaxis_range=[0, 5],
    showlegend=True
)

# Display the plot
user_input = st.plotly_chart(fig, use_container_width=True)

# Submit button
if st.button('Submit your trajectory'):
    # Extract the y-values of the user's input
    user_data = user_input['data'][-1]['y']
    st.session_state.responses.append(user_data)
    st.write("Thank you for your submission!")

# Display results
if st.session_state.responses:
    st.subheader("Results")
    
    result_fig = go.Figure()

    # Add IPCC RCP scenarios
    result_fig.add_trace(go.Scatter(x=years, y=rcp26, mode='lines', name='RCP 2.6', line=dict(color='green')))
    result_fig.add_trace(go.Scatter(x=years, y=rcp45, mode='lines', name='RCP 4.5', line=dict(color='orange')))
    result_fig.add_trace(go.Scatter(x=years, y=rcp85, mode='lines', name='RCP 8.5', line=dict(color='red')))

    # Add individual responses
    for response in st.session_state.responses:
        result_fig.add_trace(go.Scatter(x=years, y=response, mode='lines', 
                                        line=dict(color='rgba(100,100,100,0.2)'), showlegend=False))

    # Add average response
    avg_response = np.mean(st.session_state.responses, axis=0)
    result_fig.add_trace(go.Scatter(x=years, y=avg_response, mode='lines', name='Average response',
                                    line=dict(color='blue', width=4)))

    result_fig.update_layout(
        title='Global Temperature Increase Projections',
        xaxis_title='Year',
        yaxis_title='Temperature Increase (°C)',
        yaxis_range=[0, 5],
        showlegend=True
    )

    st.plotly_chart(result_fig, use_container_width=True)

    st.write(f"Number of responses: {len(st.session_state.responses)}")

st.write("Note: This is a simplified model for educational purposes. For accurate climate projections, please refer to peer-reviewed scientific sources such as the IPCC reports.")
