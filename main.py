"""
Module to create a web-map of films locations
using the IMDB database.
"""

import argparse
import folium as fl
from typing import List
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
        paren_index = line.split('\t')[0].index('(')
        film_name = str(line.split('\t')[0][:paren_index-1])
        release_year = str(line.split('\t')[0][paren_index+1:paren_index+5])

        if line.split('\t')[-1].endswith(')\n'):
            shooting_location = str(line.split('\t')[-2])
        else:
            shooting_location = str(line.split('\t')[-1][:-1])

        clean_info.append([film_name, release_year, shooting_location])

    return clean_info


def create_dict(clean_info: list) -> dict:
    """Create dict with release years as keys and list of
    tuples of films' names and shooting addresses as values.
    Ignore bad years.

    Args:
        clean_info (list): Nested list containing lists with
            name, year and address.

    Returns:
        dict: Films grouped by realease year.
    """
    films_by_years = dict()
    for film_name, release_year, shooting_address in clean_info:
        key_year = release_year
        if key_year.isnumeric() and len(key_year) == 4:
            if key_year not in films_by_years.keys():
                films_by_years[key_year] = [(film_name, shooting_address)]
            else:
                films_by_years[key_year].append((film_name, shooting_address))

    return films_by_years


def get_coordinates(address: str, path: str) -> tuple:
    """Return a tuple of latitude and longitude of
    a place, using it's address.

    Args:
        address (str): Place address e.g. "City, District, Country".
        path (str): Path to a file where to look for coordinates.

    Returns:
        tuple: Coordinates. (lat, lon)
    """
    with open(path, 'r', encoding='utf-8', errors='ignore') as file:
        baseaddresses_and_coordinates = set(file.readlines())

    cut_address = ', '.join(address.split(', ')[-3:])
    for baseaddress_and_coordinate in baseaddresses_and_coordinates:
        if cut_address in baseaddress_and_coordinate:
            coordinates = (float(baseaddress_and_coordinate.split(
                '\t')[1].split(' ')[0]),
                float(baseaddress_and_coordinate.split(
                    '\t')[1].split(' ')[1][:-1]))

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


def create_stat(names_and_addresses: list, lat: float,
                lon: float, coord_base: str) -> list:
    """Return a nested list with lists that contain all info about
    all films of a given year. Each sublist contains film name, shooting
    address, distance from the given point, and a tuple (lat, lon) of
    coordinates.

    Args:
        names_and_addresses (list): List that contains tuples that contain
            film name and shooting address.
        lat (float): Latitude of our given point.
        lon (float): Longitude of our given point.
        coord_base (str): Path to file with addresses and locations.

    Returns:
        list: Nested list with all info about films of our given year.
    """
    stat = list()
    for film, address in names_and_addresses:
        address_coordinates = get_coordinates(address, coord_base)
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
    different_locations = set()
    index = 0
    while len(different_locations) != 10:
        markers_info.append(stat[index])
        different_locations.add(stat[index][-1])
        index += 1

    return markers_info


def create_nearby_marks_layer(markers_info: list) -> fl.FeatureGroup:
    """Create a map layer object with markers of films that were shot
    nearby the given year.

    Args:
        markers_info (list): List with lists that contain name, address,
            distance, and tuple of coordinates of every film that will be
            on the markers.

    Returns:
        fl.FeatureGroup: A map object with markers of nearby shot films.
    """
    fg_m = fl.FeatureGroup(name='Nearby Films')

    fg_m.add_child(fl.Marker(
        location=[lat, lon],
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
            popup='\\n'.join(films[coordinates]),
            tooltip=str(round(distance, 3))+' km',
            icon=fl.Icon(color='darkred')
        ))

    return fg_m


def create_best_films_markers() -> fl.FeatureGroup:
    """Create a map layer object with markers
    of the 8 best films of all times.

    Returns:
        fl.FeatureGroup: A map object with markers of the best films.
    """
    data = [['The Shawshank Redemption',
             'Frederiksted, Virgin Islands',
             (17.7125, -64.8815)],
            ['The Godfather',
             'Messina, Sicily, Italy',
             (38.1937, 15.5542)],
            ['The Godfather: Part II',
             'Lake Tahoe, California, USA',
             (39.0968, -120.0324)],
            ['The Dark Knight ',
            'Chicago, Illinois, USA',
             (41.8781, -87.6298)],
            ['12 Angry Men',
            'New York City, New York, USA',
             (40.7128, -74.0060)],
            ["Schindler's List",
            'Oswiecim, Malopolskie, Poland',
             (50.0344, 19.2098)],
            ['The Lord of the Rings: The Return of the King',
            'Matamata, Waikato, New Zealand',
             (-37.8085, 175.7710)],
            ['Pulp Fiction',
            'Glendale, California, USA',
             (34.1425, -118.2551)]]

    html = """
    <h4>Film here:</h4>
    <a href='"https://www.google.com/search?q=%22{}%22'
    target='_blank'>{}</a>
    """

    fg_best = fl.FeatureGroup(name='Best Films Of All Times')
    for film, address, coordinate in data:
        iframe = fl.IFrame(
            html=html.format(film, film),
            width=150,
            height=100
        )
        fg_best.add_child(fl.Marker(
            location=coordinate,
            popup=fl.Popup(iframe),
            tooltip=address,
            icon=fl.Icon(color='green', icon_color='lightred')
        ))

    return fg_best


def create_population_layer() -> fl.FeatureGroup:
    """Create layer with population.

    Returns:
        fl.FeatureGroup: A map object with population info.
    """
    fg_pop = fl.FeatureGroup(name='Population')
    fg_pop.add_child(fl.GeoJson(
        data=open('data/world.json', 'r', encoding='utf-8-sig').read(),
        style_function=lambda x: {
            'fillColor': 'green' if x['properties']['POP2005'] < 10000000
            else 'orange' if 1000000 <= x['properties']['POP2005'] < 50000000
            else 'red'
        }
    ))

    return fg_pop


def create_map(lat: float, lon: float, markers_info: list, map_name: str):
    """Create the base of the map and add all the layers on it.

    Args:
        lat (float): Latitude of our given point.
        lon (float): Longitude of our given point.
        markers_info (list): List with lists with info about
            nearby shot films the given year.
        map_name (str): Name of the map html file.
    """
    my_map = fl.Map(
        location=[lat, lon],
        zoom_start=6,
        control_scale=True,
        min_zoom=2
    )

    fg_list = list()
    fg_list.append(create_nearby_marks_layer(markers_info))
    fg_list.append(create_best_films_markers())
    fg_list.append(create_population_layer())

    for fg in fg_list:
        my_map.add_child(fg)

    my_map.add_child(fl.LayerControl())

    my_map.save(map_name)


def main(year: int, lat: float, lon: float,
         coord_base: str, map_name: str, imdb_base: str):
    """Main function. Calls other functions, runs the flow
    of the program.

    Args:
        year (int): Our given year.
        lat (float): Latitude of our given point.
        lon (float): Longitude of our given point.
        coord_base (str): Path to a file with addresses
            and their coordinates.
        map_name (str): Name of the html map file.
        imdb_base (str): Path to the file with IMDB film info.
    """
    lines = read_file(imdb_base)
    clean_info = parse_lines(lines)
    films_by_year = create_dict(clean_info)
    names_and_addresses = films_by_year[year]
    stat = create_stat(names_and_addresses, lat, lon, coord_base)

    markers_info = filter_stat(stat)

    create_map(lat, lon, markers_info, map_name)


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

    coordinates_base = 'data/locbase.txt'
    map_name = 'MyMap.html'
    imdb_file = 'data/locations_small.list'

    main(year, lat, lon, coordinates_base, map_name, imdb_file)
