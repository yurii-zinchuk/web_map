import argparse
import folium as fl
import pandas as pd
from geopy.geocoders import Nominatim


def read_file(path: str) -> list:
    """Read and create a list of strings
    with film lines.

    Args:
        path (str): path to IMDB film file.

    Returns:
        list: list of film info lines.
    """
    with open(path, 'r', encoding='utf-8',
              errors='ignore') as file:
        lines = file.readlines()[14:-1]

    return lines


def parse_lines(lines: list) -> list:
    """Clean up lines with film info, deleting trash.

    Args:
        lines (list): list of film info lines.

    Returns:
        list: clean film info lines.
    """
    clean_info = list()
    for line in lines:
        if line.split('\t')[-1].endswith(')\n'):
            clean_info.append(str(line.split('\t')[0][:line.split('\t')
                                                      [0].index('(')-1] + '\t'
                                  + line.split('\t')[0][line.split('\t')
                                  [0].index('('):line.split('\t')[0].index
                                  (')')+1] + '\t' + line.split('\t')[-2])
                              .split('\t'))
        else:
            clean_info.append(str(line.split('\t')[0][:line.split('\t')
                                                      [0].index('(')-1] + '\t'
                                  + line.split('\t')[0][line.split('\t')
                                  [0].index('('):line.split('\t')[0].index
                                  (')')+1] + '\t' + line.split('\t')[-1][:-1])
                              .split('\t'))

    return clean_info


def create_dict(clean_info: list) -> dict:
    """Create dict with years as keys and
    tuples of films and locations as values.

    Args:
        clean_info (list): list with clean film info.

    Returns:
        dict: dict with films info grouped by year.
    """
    years_dict = dict()
    for line in clean_info:
        key = line[1][1:-1]
        if key.isnumeric() and len(key) == 4:
            if key not in years_dict.keys():
                years_dict[key] = [(line[0], line[2])]
            else:
                years_dict[key].append((line[0], line[2]))

    return years_dict


def main():
    lines = read_file('locations.list')
    clean_info = parse_lines(lines)
    film_dict = create_dict(clean_info)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get arguments for map building.")
    parser.add_argument("year", type=int, metavar="",
                        help="Year of films")
    parser.add_argument("longitude", type=float, metavar="",
                        help="Longitude of location")
    parser.add_argument("latitude", type=float, metavar="",
                        help="Latitude of location")
    args = parser.parse_args()

    main()

    print(args.year)
