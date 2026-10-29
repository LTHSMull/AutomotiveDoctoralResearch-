import streamlit as st
import pandas as pd

# Set the title of the web page
st.title("My Doctoral Research Dashboard")

# Add some text
st.write("Welcome to my educational technology data explorer!")

# Create and display a simple data table
data = {
    'Student Group': ['Control', 'Experimental'],
    'Average Score': [75, 88]
}
df = pd.DataFrame(data)

st.dataframe(df)
