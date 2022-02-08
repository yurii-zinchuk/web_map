"""
Module to create a web-map of films locations
using the IMDB database.
"""


import argparse
from typing import List
import folium as fl
from haversine import haversine


def read_file(path: str) -> List[str]:
    """Read file. Return list of file's lines. Raw, without
    any parsing, slicing or cleanup. Lines contain:
    film name, release year, shooting address.
    And other trash among it.

    Args:
        path (str): Path to dataset.

    Returns:
        List[str]: List of raw lines.
    """
    with open(path, 'r', encoding='utf-8',
              errors='ignore') as file:
        raw_lines = file.readlines()[14:-1]

    return raw_lines


def parse_lines(lines: list) -> List[List[str]]:
    """Clean up lines with film info, delete trash.
    Leave only film name, release year, shooting address.

    Args:
        lines (list): Raw lines from func which reads the file.

    Returns:
        List[List[str]]: Nested list. Each list contains name, year, adderss.
    """
    clean_info = list()
    for line in lines:
        if line.split('\t')[-1].endswith(')\n'):

            film_name = line.split('\t')[0][:line.split('\t')[0].index('(')-1]
            release_year = line.split('\t')[0][line.split(
                '\t')[0].index('('):line.split('\t')[0].index(')')+1]
            shooting_location = line.split('\t')[-2]

            clean_info.append(str(film_name + '\t' + release_year + '\t' +
                                  shooting_location).split('\t'))
        else:

            film_name = line.split('\t')[0][:line.split('\t')[0].index('(')-1]
            release_year = line.split('\t')[0][line.split(
                '\t')[0].index('('):line.split('\t')[0].index(')')+1]
            shooting_location = line.split('\t')[-1][:-1]

            clean_info.append(str(film_name + '\t' + release_year + '\t' +
                                  shooting_location).split('\t'))

    return clean_info


def create_dict(clean_info: list) -> dict:
    """Create dict with release years as keys and list of
    tuples of films' names and shooting addresses as values.
    Ignore bad years (the reason is poor cleanup scheme, fix!!!),
    don't include in keys.

    Args:
        clean_info (list): Nested list containing lists with
        name, year and address.

    Returns:
        dict: Films grouped by realease year.
    """
    films_by_years = dict()
    for film_name, release_year, shooting_address in clean_info:
        key_year = release_year[1:-1]
        if key_year.isnumeric() and len(key_year) == 4:
            if key_year not in films_by_years.keys():
                films_by_years[key_year] = [(film_name, shooting_address)]
            else:
                films_by_years[key_year].append((film_name, shooting_address))

    return films_by_years


def get_coordinates(address: str) -> tuple:
    """Return a tuple of latitude and longitude of
    a place, using it's address.

    Args:
        place (str): Place address e.g. "City, District, Country".

    Returns:
        tuple: Coordinates. (lat, lon)
    """
    with open('locbase', 'r', encoding='utf-8', errors='ignore') as file:
        baseaddresses_and_coordinates = set(file.readlines())

    cut_address = ', '.join(address.split(', ')[-3:])
    found = False
    for baseaddress_and_coordinate in baseaddresses_and_coordinates:
        if cut_address in baseaddress_and_coordinate:
            found = True
            coordinates = (float(baseaddress_and_coordinate.split(
                '\t')[1].split(' ')[1][:-1]),
                float(baseaddress_and_coordinate.split('\t')[1].split(' ')[0]))

    if not found:
        # try:
        #     geolocator = Nominatim(user_agent='my_request')
        #     location = geolocator.geocode(cut_address)
        #     coordinates = (str(location.longitude), str(location.latitude))
        # except Exception:
        #     coordinates = None
        coordinates = None

    return coordinates


def calculate_distance(la1: float, la2: float,
                       lo1: float, lo2: float) -> float:
    """Return distance between two points on Earth's surface.
    Units are kilometers.

    Args:
        la1 (float): Latitude of first point.
        la2 (float): Latitude of second point.
        lo1 (float): Longitude of first point.
        lo2 (float): Longitude of second point.

    Returns:
        float: Distance in kilometers.
    """
    distance = haversine((la1, lo1), (la2, lo2))
    return distance


def create_stat(names_and_addresses: list, lat: float, lon: float) -> list:
    """Return a nested list with lists that contain all info about
    all films of a given year. Each sublist contains film name, shooting
    address, distance from the given point, and a tuple (lat, lon) of
    coordinates.

    Args:
        names_and_addresses (list): List that contains tuples that contain
        film name and shooting address.
        lat (float): Latitude of our given point.
        lon (float): Longitude of our given point.

    Returns:
        list: Nested list with all info about films of our given year.
    """
    stat = list()
    for film, address in names_and_addresses:
        address_coordinates = get_coordinates(address)
        if address_coordinates:
            address_lat = address_coordinates[0]
            address_lon = address_coordinates[1]

            distance = calculate_distance(lat, address_lat, lon, address_lon)

            stat.append([film, address, distance, address_coordinates])
    stat.sort(key=lambda x: x[2])

    return stat


def filter_stat(stat: list) -> list:
    """Return only what's useful for creationg marks on the map.
    Based on the content of stat list. Choose 10 nearest films.

    Args:
        stat (list): Stat list from the create_stat() function.

    Returns:
        list: The same list as stat, but only useful info for markers.
    """
    markers_info = list()
    different_films = set()
    index = 0
    while len(different_films) != 10:
        markers_info.append(stat[index])
        different_films.add(stat[index][0])
        index += 1

    return markers_info


def create_nearby_marks_layer(markers_info: list) -> fl.FeatureGroup:
    """Create a map layer object with markers of films that were shoot
    nearby the given year.

    Args:
        markers_info (list): List with lists that contain name, address,
        distance, and tuple of coordinates of every film that will be
        on the markers.

    Returns:
        fl.FeatureGroup: A map object with marks of nearby shot films.
    """
    fg_m = fl.FeatureGroup(name='Nearby Films')

    fg_m.add_child(fl.Marker(location=[lat, lon],
                             popup='You are here!',
                             icon=fl.Icon())
                   )

    films = dict()
    for film, _, distance, coordinates in markers_info:
        if coordinates in films:
            films[coordinates].add('>'+film)
        else:
            films[coordinates] = {'>'+film}

        fg_m.add_child(fl.Marker(
            location=coordinates,
            popup='\n'.join(films[coordinates]),
            tooltip=str(round(distance, 3))+' km',
            icon=fl.Icon(color='darkred')
        ))

    return fg_m


def create_map(lat: float, lon: float, markers_info: list):
    """Create the base of the map and add all the layers on it.

    Args:
        lat (float): Latitude of our given point.
        lon (float): Longitude of our given point.
        markers_info (list): List with lists with info about
        nearby shot films the given year.
    """
    my_map = fl.Map(
        location=[lat, lon],
        zoom_start=7,
        control_scale=True
    )

    fg_m = create_nearby_marks_layer(markers_info)
    my_map.add_child(fg_m)

    my_map.add_child(fl.LayerControl())

    my_map.save('MyMap.html')


def main(year: int, lat: float, lon: float):
    """Main function. Calls other functions, runs the flow
    of the program.

    Args:
        year (int): Our given year.
        lat (float): Latitude of our given point.
        lon (float): Longitude of our given point.
    """
    lines = read_file('newlocations.list')
    clean_info = parse_lines(lines)
    films_by_year = create_dict(clean_info)
    names_and_addresses = films_by_year[year]
    stat = create_stat(names_and_addresses, lat, lon)

    markers_info = filter_stat(stat)

    create_map(lat, lon, markers_info)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get arguments for map building.")
    parser.add_argument("year", type=int, metavar="",
                        help="Year of films")
    parser.add_argument("latitude", type=float, metavar="",
                        help="Latitude of location")
    parser.add_argument("longitude", type=float, metavar="",
                        help="Longitude of location")
    args = parser.parse_args()

    year = str(args.year)
    lon = args.longitude
    lat = args.latitude

    main(year, lat, lon)
