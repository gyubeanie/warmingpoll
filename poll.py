import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, PickleType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database setup
Base = declarative_base()

class Response(Base):
    __tablename__ = 'responses'
    id = Column(Integer, primary_key=True)
    data = Column(PickleType)

engine = create_engine('sqlite:///responses.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Load RCP data
rcp_data = pd.read_csv('rcp_data.csv')
years = rcp_data['Year'].tolist()

st.title("Global Warming Trajectory Poll")

st.write("Use the sliders below to input your expected global warming trajectory from 2020 to 2100.")

# User input using sliders
user_input = [1.0]  # Starting from 1.0°C in 2020
input_years = [2020, 2040, 2060, 2080, 2100]
for year in input_years[1:]:
    temp = st.slider(f"Temperature increase in {year} (°C)", 0.0, 5.0, 1.0, 0.1)
    user_input.append(temp)

# Interpolate user input to match all years
full_user_input = np.interp(years, input_years, user_input)

# Create a Plotly figure
fig = go.Figure()

# Add IPCC RCP scenarios
for scenario in ['RCP2.6', 'RCP4.5', 'RCP8.5']:
    fig.add_trace(go.Scatter(x=years, y=rcp_data[scenario], mode='lines', name=scenario))

# Add user input trace
fig.add_trace(go.Scatter(x=years, y=full_user_input, mode='lines+markers', name='Your input',
                         line=dict(color='blue'), marker=dict(size=10)))

fig.update_layout(
    title='Global Temperature Increase (°C)',
    xaxis_title='Year',
    yaxis_title='Temperature Increase (°C)',
    yaxis_range=[0, 5],
    showlegend=True
)

# Display the plot
st.plotly_chart(fig, use_container_width=True)

# Submit button
if st.button('Submit your trajectory'):
    # Store in database
    session = Session()
    new_response = Response(data=full_user_input.tolist())
    session.add(new_response)
    session.commit()
    session.close()
    
    st.write("Thank you for your submission!")

# Display results
if st.button("Show Results"):
    st.subheader("Results")
    
    result_fig = go.Figure()

    # Add IPCC RCP scenarios
    for scenario in ['RCP2.6', 'RCP4.5', 'RCP8.5']:
        result_fig.add_trace(go.Scatter(x=years, y=rcp_data[scenario], mode='lines', name=scenario))

    # Fetch and add individual responses
    session = Session()
    responses = session.query(Response).all()
    
    all_responses = []
    for response in responses:
        result_fig.add_trace(go.Scatter(x=years, y=response.data, mode='lines', 
                                        line=dict(color='rgba(100,100,100,0.2)'), showlegend=False))
        all_responses.append(response.data)
    
    session.close()

    # Add average response
    if all_responses:
        avg_response = np.mean(all_responses, axis=0)
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

    st.write(f"Number of responses: {len(all_responses)}")

st.write("Note: This is a simplified model for educational purposes. For accurate climate projections, please refer to peer-reviewed scientific sources such as the IPCC reports.")
