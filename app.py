import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import numpy as np
import statsmodels.api as sm

# Read data from the Excel file
df = pd.read_excel('patient_data.xlsx')

# List of numeric columns to be used in dropdowns
numeric_columns = ['Hemoglobin (g/dL)', 'White Blood Cell Count (10^3/μL)', 'Platelet Count (10^3/μL)', 'Cholesterol (mg/dL)']

# Define a custom color palette for the bar chart
bar_color_palette = px.colors.qualitative.Pastel

# Define the healthy range for each parameter
healthy_ranges = {
    'Hemoglobin (g/dL)': (12.0, 16.5),
    'White Blood Cell Count (10^3/μL)': (4.5, 11.0),
    'Platelet Count (10^3/μL)': (150, 450),
    'Cholesterol (mg/dL)': (0, 200),
}

# Function to determine if a value is within the healthy range
def is_within_healthy_range(value, parameter):
    min_range, max_range = healthy_ranges[parameter]
    return min_range <= value <= max_range

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=['https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'])

# Define the app layout
app.layout = html.Div([
    # Header
    html.H1("PathoMetrics Dashboard", className="text-center mt-4 text-dark"),
    
    # Left Side: Patient Details and Desirable Ranges
    html.Div([
        # Patient Details Section
        html.Div([
            html.H3("Patient Details", className="mb-3 text-muted"),
            # Input for Patient ID
            dcc.Input(id='patient-id-input', type='text', placeholder='Enter Patient ID'),
            # Search button
            html.Button('Search', id='search-button', className='btn btn-primary ml-2'),
            # Patient details
            html.Div(id='patient-details-output', className="mt-3"),
        ], className="border rounded p-3 m-3 bg-light"),
        
        # Desirable Ranges Section
        html.Div([
            html.H3("Desirable Ranges", className="mb-3 text-muted"),
            # Display the desirable range for each parameter
            html.P(f"Hemoglobin: {healthy_ranges['Hemoglobin (g/dL)'][0]} - {healthy_ranges['Hemoglobin (g/dL)'][1]} g/dL"),
            html.P(f"White Blood Cell Count: {healthy_ranges['White Blood Cell Count (10^3/μL)'][0]} - {healthy_ranges['White Blood Cell Count (10^3/μL)'][1]} x 10^3/μL"),
            html.P(f"Platelet Count: {healthy_ranges['Platelet Count (10^3/μL)'][0]} - {healthy_ranges['Platelet Count (10^3/μL)'][1]} x 10^3/μL"),
            html.P(f"Cholesterol: Less than {healthy_ranges['Cholesterol (mg/dL)'][1]} mg/dL"),
        ], className="border rounded p-3 m-3 bg-light"),
    ], style={'float': 'left', 'width': '25%'}),
    
    # Right Side: Data Summary, Scatter Plot, and Bar Chart
    html.Div([
        # Data Summary Section
        html.Div([
            html.H3("Data Summary", className="mb-3 text-muted"),
            # Data summary statistics
            html.P(f"Number of unique patients: {df['Patient ID'].nunique()}"),
            html.P(f"Mean Age: {df['Age'].mean():.2f}"),
            html.P(f"Median Hemoglobin: {df['Hemoglobin (g/dL)'].median():.2f}"),
            html.P(f"Standard Deviation Platelet Count: {df['Platelet Count (10^3/μL)'].std():.2f}"),
        ], className="border rounded p-3 m-3 bg-light"),
        
        # Scatter Plot Section
        html.Div([
            html.H3("Scatter Plot", className="mb-3 text-muted"),
            # Scatter plot dropdowns
            dcc.Dropdown(
                id='scatter-x-variable',
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='Hemoglobin (g/dL)',  # Default X variable
                multi=False,
                placeholder='Select X variable (Scatter)',
                className="mb-2"
            ),
            dcc.Dropdown(
                id='scatter-y-variable',
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='White Blood Cell Count (10^3/μL)',  # Default Y variable
                multi=False,
                placeholder='Select Y variable (Scatter)',
                className="mb-2"
            ),
            # Scatter plot
            dcc.Graph(id='scatter-plot'),
        ], className="border rounded p-3 m-3 bg-light"),
        
        # Bar Graph Section
        html.Div([
            html.H3("Bar Chart", className="mb-3 text-muted"),
            # Dropdown for selecting Y variable for the bar chart
            dcc.Dropdown(
                id='bar-y-variable',
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='Hemoglobin (g/dL)',  # Default Y variable for bar chart
                multi=False,
                placeholder='Select Y variable (Bar)',
                className="mb-2"
            ),
            # Bar chart
            dcc.Graph(id='bar-chart'),
        ], className="border rounded p-3 m-3 bg-light"),
    ], style={'float': 'left', 'width': '75%'}),
])

# Callback to display patient details and highlight values outside the healthy range
@app.callback(
    Output('patient-details-output', 'children'),
    [Input('search-button', 'n_clicks')],
    [State('patient-id-input', 'value')]
)
def display_patient_details(n_clicks, patient_id):
    if not n_clicks:
        return html.P("Enter a Patient ID and click 'Search' to view details")
    
    if not patient_id:
        return html.P("Enter a valid Patient ID to view details")
    
    patient_details = df[df['Patient ID'] == patient_id]
    
    if patient_details.empty:
        return html.P("Patient ID not found")
    
    details = []
    for index, row in patient_details.iterrows():
        details.append(html.P(f"Patient ID: {row['Patient ID']}"))
        details.append(html.P(f"Age: {row['Age']}"))
        details.append(html.P(f"Gender: {row['Gender']}"))
        
        # Display parameter values and highlight values outside the healthy range in red
        for param in numeric_columns:
            value = row[param]
            if is_within_healthy_range(value, param):
                details.append(html.P(f"{param}: {value}"))
            else:
                details.append(html.P(f"{param}: {value}", style={'color': 'red'}))
    
    return details

# Callback to update the scatter plot based on user's selection
@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('scatter-x-variable', 'value'),
     Input('scatter-y-variable', 'value')]
)
def update_scatter_plot(x_variable, y_variable):
    scatter_plot = px.scatter(
        df, x=x_variable, y=y_variable, title=f'{x_variable} vs. {y_variable}'
    )
    
    # Fit linear regression model
    X = sm.add_constant(df[x_variable])
    model = sm.OLS(df[y_variable], X).fit()
    
    # Generate points for the trendline
    x_range = np.linspace(df[x_variable].min(), df[x_variable].max(), 100)
    y_range = model.params['const'] + model.params[x_variable] * x_range
    
    # Create a trace for the trendline
    trendline_trace = {
        'x': x_range,
        'y': y_range,
        'mode': 'lines',
        'name': 'Trendline',
    }
    
    # Add trendline to the scatter plot
    scatter_plot.add_trace(trendline_trace)
    
    return scatter_plot

# Callback to update the bar graph based on user's selection
@app.callback(
    Output('bar-chart', 'figure'),
    [Input('bar-y-variable', 'value')]
)
def update_bar_chart(y_variable):
    bar_chart = px.bar(
        df, x='Age', y=y_variable, title=f'{y_variable} vs. Age',
        color_discrete_sequence=bar_color_palette
    )
    return bar_chart

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
