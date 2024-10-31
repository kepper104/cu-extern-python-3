import json
import dash
import requests
from dash import dcc, html, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from geocoder import get_coordinates_of_city

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Store weather data globally
weather_data = {}


# Function to retrieve weather data from Open-Meteo API
def get_weather_forecast(lat, lon, city_name):
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    query = f"?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"

    response = requests.get(BASE_URL + query)
    if response.status_code == 200:
        data = response.json()
        print("got data for ", city_name)
        # print(f"Weather data for ({lat}, {lon}):\n", json.dumps(data, indent=2))
        return data  # Return the data for processing
    else:
        print(f"Failed to retrieve weather data for ({lat}, {lon}): Status {response.status_code}")
        return None


# Define the layout of the app
app.layout = html.Div([
    html.H2("Weather Route Planner"),

    # Two-column layout: Left for inputs, Right for checkboxes
    dbc.Row([

        # Left Column: Input fields
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Label("Origin City:")),
                dbc.Col(dbc.Input(id='origin-input', type='text', placeholder='Enter origin city'))
            ], className="mb-3", style={'height': '50px'}),

            dbc.Row([
                dbc.Col(html.Label("Destination City:")),
                dbc.Col(dbc.Input(id='destination-input', type='text', placeholder='Enter destination city'))
            ], className="mb-3", style={'height': '50px'}),

            # Placeholder for dynamically added intermediate points
            html.Div(id='intermediate-points', children=[],
                     ),

            # Buttons to add intermediate points and request weather
            dbc.Row([
                dbc.Col(dbc.Button("Add Intermediate Point", id='add-point-btn', color="primary", className="me-2"),
                        width="auto"),
                dbc.Col(dbc.Button("Get Weather Data", id='get-weather-btn', color="success"), width="auto")
            ], className="mb-3"),
        ]),

        # Right Column: Checkboxes
        dbc.Col([
            # Checkboxes for selecting data for plotting
            html.Div(id='data-selection', children=[
                dbc.Checkbox(
                    id='origin-checkbox', label=f'Origin City', value=True, style={'display': 'none'}
                ),
                dbc.Checkbox(
                    id='destination-checkbox', label=f'Destination City', value=True, style={'display': 'none'}
                )
            ])
        ])
    ], style={'width': '1000px'}),

    # Graphs for temperature, humidity, and wind speed
    dcc.Graph(id='temperature-graph'),
    dcc.Graph(id='humidity-graph'),
    dcc.Graph(id='wind-speed-graph'),
])


@app.callback(
    Output('intermediate-points', 'children'),
    Input('add-point-btn', 'n_clicks'),
    Input({'type': 'delete-point-btn', 'index': dash.ALL}, 'n_clicks'),
    State('intermediate-points', 'children')
)
def manage_intermediate_points(add_click, delete_clicks, children):
    ctx = dash.callback_context

    # Add a new intermediate point if the add button was clicked
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'add-point-btn.n_clicks' and add_click:
        point_number = len(children) + 1
        new_point = dbc.Row([
            dbc.Col(html.Label(f"Intermediate Point {point_number}:"), width=2),
            html.Div([
                dbc.Col(
                    dbc.Button("Delete", id={'type': 'delete-point-btn', 'index': point_number}, color="danger",
                               size="sm"),
                    width="auto"),
                dbc.Col(dbc.Input(type='text', id={'type': 'intermediate-input', 'index': point_number},
                                  placeholder=f'Enter city name for point {point_number}', style={'width': '250px'}),
                        style={'flex': '0'}),
            ], style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'space-between', 'width': 'unset', 'gap': '10px'}),


        ], className="mb-3", id={'type': 'point-row', 'index': point_number},
            style={'height': '50px', 'display': 'flex', 'flex-direction': 'row',
                   'justify-content': 'space-between'})
        children.append(new_point)

    # Check if any delete button was clicked
    elif ctx.triggered and 'delete-point-btn' in ctx.triggered[0]['prop_id']:
        # Get the index of the point to delete
        delete_index = ctx.triggered[0]['prop_id'].split('.')[0]
        delete_index = eval(delete_index)['index']
        # Remove the specific point by filtering it out of the children list
        children = [child for child in children if child['props']['id']['index'] != delete_index]

    return children


# Callback to fetch weather data on button click
@app.callback(
    Output('data-selection', 'children'),
    Output('get-weather-btn', 'n_clicks'),  # Dummy output to satisfy Dash callback requirements
    Input('get-weather-btn', 'n_clicks'),
    State('origin-input', 'value'),
    State('destination-input', 'value'),
    State('intermediate-points', 'children'),
    prevent_initial_call=True  # Only triggers after button is clicked
)
def fetch_weather_data(n_clicks, origin_city, destination_city, children):
    global weather_data  # Use the global weather_data variable

    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    if n_clicks:
        # Get coordinates for origin and destination
        origin_coords = get_coordinates_of_city(origin_city)
        destination_coords = get_coordinates_of_city(destination_city)

        # Store weather data for origin and destination
        weather_data['origin'] = get_weather_forecast(origin_coords["latitude"], origin_coords["longitude"],
                                                      origin_city)
        weather_data['destination'] = get_weather_forecast(destination_coords["latitude"],
                                                           destination_coords["longitude"], destination_city)

        # Get coordinates for intermediate points
        intermediate_coords = []
        for i, point in enumerate(children, start=1):
            print(i, point)
            try:
                city_name = point['props']['children'][1]['props']['value']
            except KeyError:
                city_name = point['props']['children'][1]['props']['children'][1]['props']['children']['props']['value']

            coords = get_coordinates_of_city(city_name)
            intermediate_coords.append(coords)
            weather_data[f'intermediate_{i}'] = get_weather_forecast(coords["latitude"], coords["longitude"], city_name)

        # Create checkboxes for selecting data
        checkboxes = []
        checkboxes.append(dbc.Checkbox(id='origin-checkbox', label=f'Показать', value=True,
                                       style={'height': '50px'}, className="mb-3"))
        checkboxes.append(
            dbc.Checkbox(id='destination-checkbox', label=f'Показать', value=True,
                         style={'height': '50px'}, className="mb-3"))
        for i in range(1, len(intermediate_coords) + 1):
            city_name = children[i - 1]['props']['children'][1]['props']['children'][1]['props']['children']['props']['value']

            checkboxes.append(dbc.Checkbox(id={'type': f'intermediate-checkbox', 'index': i},
                                           label=f'Показать', value=True,
                                           style={'height': '50px'}, className="mb-3"))

        return checkboxes, 0  # Reset the button click count

    return [], 0


# Callback to update the graphs based on selected data
@app.callback(
    Output('temperature-graph', 'figure'),
    Output('humidity-graph', 'figure'),
    Output('wind-speed-graph', 'figure'),
    # Input('data-selection', 'children'),
    Input('get-weather-btn', 'n_clicks'),
    Input('origin-checkbox', 'value'),
    Input('destination-checkbox', 'value'),
    Input({'type': 'intermediate-checkbox', 'index': dash.ALL}, 'value'),
    State("origin-input", "value"),
    State("destination-input", "value"),
    State({'type': 'intermediate-input', 'index': dash.ALL}, 'value'),

)
def update_graphs(n_clicks, origin_selected, destination_selected, intermediate_selected, origin_name, destination_name,
                  intermediate_names):
    # if n_clicks is None:
    #     raise dash.exceptions.PreventUpdate
    print(weather_data)
    traces_temp = []
    traces_hum = []
    traces_wind = []

    # Origin data
    if origin_selected and 'origin' in weather_data:
        origin_data = weather_data['origin']['hourly']
        traces_temp.append(
            go.Scatter(x=origin_data['time'], y=origin_data['temperature_2m'], mode='lines', name=origin_name))
        traces_hum.append(
            go.Scatter(x=origin_data['time'], y=origin_data['relative_humidity_2m'], mode='lines', name=origin_name))
        traces_wind.append(
            go.Scatter(x=origin_data['time'], y=origin_data['wind_speed_10m'], mode='lines', name=origin_name))

    # Destination data
    if destination_selected and 'destination' in weather_data:
        destination_data = weather_data['destination']['hourly']
        traces_temp.append(go.Scatter(x=destination_data['time'], y=destination_data['temperature_2m'], mode='lines',
                                      name=destination_name))
        traces_hum.append(
            go.Scatter(x=destination_data['time'], y=destination_data['relative_humidity_2m'], mode='lines',
                       name=destination_name))
        traces_wind.append(go.Scatter(x=destination_data['time'], y=destination_data['wind_speed_10m'], mode='lines',
                                      name=destination_name))

    print("INTER SELECTED:", intermediate_selected)
    print("INTERNAMES:", intermediate_names)
    # Intermediate data
    for i, selected in enumerate(intermediate_selected, start=1):
        print("DEBUG 1:", i, selected)
        if selected and f'intermediate_{i}' in weather_data:
            print("nice!", i)
            intermediate_data = weather_data[f'intermediate_{i}']['hourly']
            traces_temp.append(
                go.Scatter(x=intermediate_data['time'], y=intermediate_data['temperature_2m'], mode='lines',
                           name=intermediate_names[i - 1]))
            traces_hum.append(
                go.Scatter(x=intermediate_data['time'], y=intermediate_data['relative_humidity_2m'], mode='lines',
                           name=intermediate_names[i - 1]))
            traces_wind.append(
                go.Scatter(x=intermediate_data['time'], y=intermediate_data['wind_speed_10m'], mode='lines',
                           name=intermediate_names[i - 1]))
        else:
            print("EPIC FAIL", i, selected)
    # Create figures
    temperature_fig = go.Figure(data=traces_temp)
    temperature_fig.update_layout(title='Temperature over Time', xaxis_title='Time', yaxis_title='Temperature (°C)')

    humidity_fig = go.Figure(data=traces_hum)
    humidity_fig.update_layout(title='Humidity over Time', xaxis_title='Time', yaxis_title='Humidity (%)')

    wind_speed_fig = go.Figure(data=traces_wind)
    wind_speed_fig.update_layout(title='Wind Speed over Time', xaxis_title='Time', yaxis_title='Wind Speed (km/h)')

    return temperature_fig, humidity_fig, wind_speed_fig


# @app.callback(
#     Output("output-component-id", "children"),
#     Input({'type': 'intermediate-checkbox', 'index': ALL}, 'value'),
#     Input("origin-checkbox", "value")
# )
# def update_output(values, values2):
#     # values will be a list of the 'value' property for each component that matches the pattern
#     print(values, values2)
#     return f"Checkbox values: {values} {values2}"


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
