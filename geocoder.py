import requests


def get_coordinates_of_city(city_name):
    """
    Get coordinates of a city by its name.
    :param city_name: name of the city
    :return: coordinates of the city
    """

    base_url = "https://geocoding-api.open-meteo.com/v1/search"
    request_query = f'?name={city_name}&count=5&language=ru&format=json'

    try:
        response = requests.get(base_url + request_query)
        if response.status_code != 200:
            return None
        else:
            response_json = response.json()
            if 'results' in response_json and len(response_json['results']) != 0:
                lat, lon = response_json['results'][0]['latitude'], response_json['results'][0]['longitude']
                coordinates = {"latitude": lat, "longitude": lon}
                return coordinates
            else:
                return None
    except Exception as e:
        print("Exception! Error: " + str(e))
        return None
