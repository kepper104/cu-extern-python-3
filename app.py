import dash
import requests
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go

from geocoder import get_coordinates_of_city

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Погодо-Проверятель-9000"

# Это не библиотека, а издевательство

COLUMN_WIDTH = 1500

origin_coords = None
destination_coords = None
intermediate_coords = []

min_comfortable_temperature = 8
max_comfortable_temperature = 30
min_comfortable_humidity = 30
max_comfortable_humidity = 8
max_wind_speed = 40
max_precipitation_probability = 50


def get_weather_forecast(lat, lon, city_name, days=7):
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    query = f"?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"

    if days != 7:
        query += '&forecast_days=' + str(days)

    response = requests.get(BASE_URL + query)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Failed to retrieve weather data for ({lat}, {lon}): Status {response.status_code}")
        return None


def get_weather_quality(lat, lon):
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    request_query = (f'?latitude={lat}&longitude={lon}'
                     f'&current=temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m')

    try:
        response = requests.get(BASE_URL + request_query)

        if response.status_code != 200:
            return
        weather_data = response.json()

        current_temperature = weather_data['current']['temperature_2m']
        current_humidity = weather_data['current']['relative_humidity_2m']
        current_wind_speed = weather_data['current']['wind_speed_10m']
        current_precipitation_probability = weather_data['current']['precipitation_probability']
        if (current_temperature < min_comfortable_temperature or
                current_temperature > max_comfortable_temperature or
                current_humidity < min_comfortable_humidity or
                current_humidity > max_comfortable_humidity or
                current_wind_speed > max_wind_speed or
                current_precipitation_probability > max_precipitation_probability):
            return "Погода сомнительная!"
        return "Погода идеальная!"
    except Exception as e:
        return "Ошибка!" + str(e)


app.layout = html.Div([
    html.H2("Погодо-Проверятель-9000",
            style={'margin-left': 'auto', 'margin-right': 'auto', 'text-align': 'center', 'margin-top': '40px'}),

    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col(html.Label("Город отправления:")),
                dbc.Col(dbc.Input(id='origin-input', type='text', placeholder='Название города'))
            ], className="mb-3", style={'height': '50px'}),

            html.Div(id='intermediate-points', children=[]),

            dbc.Row([
                dbc.Col(html.Label("Город назначения:")),
                dbc.Col(dbc.Input(id='destination-input', type='text', placeholder='Название города'))
            ], className="mb-3", style={'height': '50px'}),

            dbc.Button("Добавить промежуточный город", id='add-point-btn', color="primary", className="me-2",
                       style={'margin-left': '50%', 'width': '50%'}),

            dbc.Row([
                dbc.Col(html.Label("Интервал просмотра")),
                dbc.Col(dcc.Dropdown(
                    id="plot-interval-dropdown",
                    options=[
                        {"label": "3 Дня", "value": "3"},
                        {"label": "7 Дней", "value": "7"},
                    ],
                    value="7",
                    clearable=False,
                ))
            ], className="mb-3", style={'height': '50px', 'margin-top': '20px'}),

            dbc.Button("Получить прогноз", id='get-weather-btn', color="success",
                       style={'margin-left': '50%', 'width': '50%'}),

            html.H4("Выберите данные для просмотра", style={'margin-top': '20px'}),
            dcc.Dropdown(
                id="plot-type-dropdown",
                options=[
                    {"label": "Температура", "value": "temperature"},
                    {"label": "Влажность", "value": "humidity"},
                    {"label": "Скорость ветра", "value": "wind_speed"},
                ],
                value="temperature",
                clearable=False,
                style={'margin-bottom': '10px'},
            ),

        ], style={'max-width': '1000px'}),

        dbc.Col([
            html.Div(id='data-selection', children=[
                dbc.Checkbox(
                    id='origin-checkbox', label=f'PLACEHOLDER YOU SHOULD NOT SEE', value=True, style={'display': 'none'}
                ),
                dbc.Checkbox(
                    id='destination-checkbox', label=f'PLACEHOLDER YOU SHOULD NOT SEE', value=True,
                    style={'display': 'none'}
                )
            ])
        ], style={'max-width': '100px'}),
        dbc.Col([
            dcc.Graph(id='map')
        ], style={'flex': '1'})

    ], style={'width': '100%', 'padding-left': '100px', 'padding-top': '20px', 'display': 'flex',
              'flex-direction': 'row'}),

    dcc.Store(id="session-data", data=None),
    dcc.Graph(id='selected-graph', style={'display': 'none'}),
])


@app.callback(
    Output('intermediate-points', 'children'),
    Input('add-point-btn', 'n_clicks'),
    Input({'type': 'delete-point-btn', 'index': dash.ALL}, 'n_clicks'),
    State('intermediate-points', 'children')
)
def manage_intermediate_points(add_click, delete_clicks, children):
    ctx = dash.callback_context

    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'add-point-btn.n_clicks' and add_click:
        point_number = len(children) + 1
        new_point = dbc.Row([
            dbc.Col(html.Label(f"Промежуточный город {point_number}:")),
            html.Div([
                # The delete button caused to many problems e.g. reordering the intermediate points numeration,
                # deleting two points at once, deleting the checkbox, etc.

                # dbc.Button("X", id={'type': 'delete-point-btn', 'index': point_number}, color="danger",
                #            size="sm", style={'width': '50px', "height": '50px'}
                #            ),

                dbc.Input(type='text', id={'type': 'intermediate-input', 'index': point_number},
                          placeholder=f'Название города {point_number}',
                          style={'width': '351px', 'margin-top': '6px', 'margin-bottom': '6px'}
                          )

            ], style={'display': 'flex', 'flex-direction': 'row', 'justify-content': 'space-between', 'width': 'unset',
                      'gap': '10px'}),

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


@app.callback(
    Output('data-selection', 'children'),
    Output('get-weather-btn', 'n_clicks'),
    Output('session-data', 'data'),
    Input('get-weather-btn', 'n_clicks'),
    Input('session-data', 'data'),
    State('plot-interval-dropdown', 'value'),
    State('origin-input', 'value'),
    State('destination-input', 'value'),
    State('intermediate-points', 'children'),
    prevent_initial_call=True
)
def fetch_weather_data(n_clicks, session_data, plot_interval, origin_city, destination_city, children):
    global origin_coords, destination_coords, intermediate_coords
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate

    if n_clicks:
        weather_data = {"data": {}}

        origin_coords = get_coordinates_of_city(origin_city)
        destination_coords = get_coordinates_of_city(destination_city)

        try:

            weather_data['data']['origin'] = get_weather_forecast(origin_coords["latitude"], origin_coords["longitude"],
                                                                  origin_city, days=int(plot_interval))
        except Exception as e:
            print("Ошибка!")

        try:
            weather_data['data']['destination'] = get_weather_forecast(destination_coords["latitude"],
                                                                       destination_coords["longitude"],
                                                                       destination_city,
                                                                       days=int(plot_interval))
        except Exception as e:
            print("Ошибка!")

        intermediate_coords = []
        for i, point in enumerate(children, start=1):
            try:
                city_name = point['props']['children'][1]['props']['value']
            except KeyError:
                city_name = point['props']['children'][1]['props']['children'][0]['props']['value']
            try:
                coords = get_coordinates_of_city(city_name)
                intermediate_coords.append(coords)
                weather_data['data'][f'intermediate_{i}'] = get_weather_forecast(coords["latitude"],
                                                                                 coords["longitude"],
                                                                                 city_name, days=int(plot_interval))
            except Exception as e:
                print("Ошибка!")

        checkboxes = []
        checkboxes.append(dbc.Checkbox(id='origin-checkbox', label=f'Показать', value=True,
                                       style={'height': '50px'}, className="mb-3"))

        for i in range(1, len(intermediate_coords) + 1):
            city_name = children[i - 1]['props']['children'][1]['props']['children'][0]['props']['value']

            checkboxes.append(dbc.Checkbox(id={'type': f'intermediate-checkbox', 'index': i},
                                           label=f'Показать', value=True,
                                           style={'height': '50px'}, className="mb-3"))
        checkboxes.append(
            dbc.Checkbox(id='destination-checkbox', label=f'Показать', value=True,
                         style={'height': '50px'}, className="mb-3"))
        return checkboxes, 0, weather_data

    return [], 0, {'data': None}


@app.callback(
    Output('selected-graph', 'figure'),
    Output('selected-graph', 'style'),
    Input('get-weather-btn', 'n_clicks'),
    Input('origin-checkbox', 'value'),
    Input('destination-checkbox', 'value'),
    Input('plot-type-dropdown', 'value'),
    Input({'type': 'intermediate-checkbox', 'index': dash.ALL}, 'value'),
    State("origin-input", "value"),
    State("destination-input", "value"),
    State({'type': 'intermediate-input', 'index': dash.ALL}, 'value'),
    State("session-data", "data"),
)
def update_graphs(n_clicks, origin_selected, destination_selected, plot_type, intermediate_selected, origin_name,
                  destination_name,
                  intermediate_names, session_data):
    if not session_data:
        return go.Figure(data=[]), {'display': 'none'}

    weather_data = session_data['data']
    traces_temp = []
    traces_hum = []
    traces_wind = []

    if origin_selected and 'origin' in weather_data:
        origin_data = weather_data['origin']['hourly']
        traces_temp.append(
            go.Scatter(x=origin_data['time'], y=origin_data['temperature_2m'], mode='lines', name=origin_name))
        traces_hum.append(
            go.Scatter(x=origin_data['time'], y=origin_data['relative_humidity_2m'], mode='lines', name=origin_name))
        traces_wind.append(
            go.Scatter(x=origin_data['time'], y=origin_data['wind_speed_10m'], mode='lines', name=origin_name))

    if destination_selected and 'destination' in weather_data:
        destination_data = weather_data['destination']['hourly']
        traces_temp.append(go.Scatter(x=destination_data['time'], y=destination_data['temperature_2m'], mode='lines',
                                      name=destination_name))
        traces_hum.append(
            go.Scatter(x=destination_data['time'], y=destination_data['relative_humidity_2m'], mode='lines',
                       name=destination_name))
        traces_wind.append(go.Scatter(x=destination_data['time'], y=destination_data['wind_speed_10m'], mode='lines',
                                      name=destination_name))

    for i, selected in enumerate(intermediate_selected, start=1):
        if selected and f'intermediate_{i}' in weather_data:
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

    if plot_type == "temperature":
        fig = go.Figure(data=traces_temp)
        fig.update_layout(title='Прогноз температуры', xaxis_title='Время', yaxis_title='Температура (°C)')
    elif plot_type == "humidity":
        fig = go.Figure(data=traces_hum)
        fig.update_layout(title='Прогноз влажности', xaxis_title='Время', yaxis_title='Влажность (%)')
    elif plot_type == "wind_speed":
        fig = go.Figure(data=traces_wind)
        fig.update_layout(title='Прогноз скорости ветра', xaxis_title='Время',
                          yaxis_title='Скорость ветра (км/ч)')

    if traces_temp or traces_hum or traces_wind:
        return fig, {'display': 'block'}
    else:
        return fig, {'display': 'none'}


@app.callback(
    Output('map', 'figure'),
    Input('map', 'id'),
    Input('get-weather-btn', 'n_clicks'),
)
def update_map(_, n_clicks):
    global origin_coords, destination_coords, intermediate_coords

    if not origin_coords or not destination_coords:
        return go.Figure(data=[], layout=go.Layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}))

    all_coords = [origin_coords] + intermediate_coords + [destination_coords]

    all_coords = [(i['latitude'], i['longitude']) for i in all_coords]

    icons = [get_weather_quality(*coord) for coord in all_coords]

    latitudes, longitudes = zip(*all_coords)
    line_trace = go.Scattermapbox(
        lat=latitudes,
        lon=longitudes,
        mode='lines+markers+text',
        text=icons,
        textposition="top right",
        marker=dict(size=10, color="blue"),
        line=dict(width=2, color="blue"),
    )

    fig = go.Figure(line_trace)
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            zoom=1,
            center=dict(lat=(origin_coords['latitude'] + destination_coords['latitude']) / 2,
                        lon=(origin_coords['longitude'] + destination_coords['longitude']) / 2)
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
