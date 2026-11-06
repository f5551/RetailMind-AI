import pandas as pd
import streamlit as st

# Let's inspect the Altair chart generated behind the scenes by Streamlit
df = pd.DataFrame({
    'product': ['Mechanical Keyboard', 'Gaming Headset', 'Monitor Light Bar', 'USB-C Hub', 'Wireless Mouse'],
    'line_revenue': [480.0, 480.0, 450.0, 640.0, 475.0]
})

print("Columns:", df.columns.tolist())
