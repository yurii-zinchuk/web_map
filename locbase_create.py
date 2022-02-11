"""
Module to create a file with locations of addresses from IMDB file.
Not all addresses are accessed by geopy. Searching for coordinates is
much faster with a file. This module uses geopy to find and write
locations, than parse info into a beautiful form.
!!  DO NOT RUN. WAS USED DURING DEVELOPMENT !!
"""

from geopy.geocoders import Nominatim
from main import read_file, parse_lines


def write_base(path: str, clean_info: list):
    """Try to find and write to a file locations
    of all addresses from the input list. (lat, lon)
    If error occured, print to stdout the address
    and error itself, and the count of errors.
    In the end print number of different addresses.

    Args:
        path (str): Path to a location dataset (where to write).
        clean_info (list): List with information,
        especially with addresses.
    """
    geolocator = Nominatim(user_agent="my_request")

    cashed = set()
    num_of_errors, num_of_different_addresses = 0, 0

    for point in clean_info:
        address = ', '.join(point[2].split(', ')[-3:])
        if address not in cashed:

            cashed.add(address)
            num_of_different_addresses += 1

            try:
                location = geolocator.geocode(address)
                with open(path, 'a', encoding='utf-8', errors='ignore')\
                        as file:
                    file.write(address + '\t' + str(location.latitude) + ' ' +
                               str(location.longitude) + '\n')

            except Exception as err:
                num_of_errors += 1
                err_info = '<<{}>>!!!!!!!!{}!!!!!!!!!\n {}'
                print(err_info.format(num_of_errors, address, err))

    print(f">>>{num_of_different_addresses} different addresses<<<")


def create_file_with_unique_addresses(path: str):
    """Rewrite file leaving only unique lines.

    Args:
        path (srt): Path to file.
    """
    with open(path, 'r', encoding='utf-8', errors='ignore') as file:
        unique_addresses = set(file.readlines())

    with open(path, 'w', encoding='utf-8', errors='ignore') as file:
        file.writelines(unique_addresses)


def find_not_found_addresses(path_src: str, path_dst: str, clean_info: list):
    """Create file with addresses, which locations are not found.

    Args:
        path_src (str): Path to file with addresses with found locations.
        path_dst (str): Path to file with addresses with not found locations.
        clean_info (list): Info list with all possible addresses.
    """
    found_addresses = set()
    with open(path_src, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            found_addresses.add(line.split('\t')[0]+'\n')

    all_addresses = set()
    for point in clean_info:
        address = ', '.join(point[2].split(', ')[-3:])
        all_addresses.add(address+'\n')

    not_found_addresses = all_addresses.difference(found_addresses)
    with open(path_dst, 'w', encoding='utf-8', errors='ignore') as file:
        file.writelines(not_found_addresses)


def continuous_location_update(path_not_found: str, path_locbase: str):
    """Some locations weren't found the first time by geopy,
    but were the second. This function tries many times.

    Args:
        path_not_found (str): Path to file with not found addresses.
        path_locbase (str): Path to file with locations.
    """
    with open(path_not_found, 'r', encoding='utf-8', errors='ignore') as file:
        not_found = set(file.readlines())

    if not not_found:
        exit()

    geolocator = Nominatim(user_agent='abc')
    with open(path_locbase, 'a', encoding='utf-8', errors='ignore') as file:
        for address in not_found:
            try:
                location = geolocator.geocode(address)
                file.write(address[:-1] + '\t' + str(location.latitude) + ' ' +
                           str(location.longitude) + '\n')
            except Exception:
                pass


if __name__ == "__main__":
    lines = read_file('data/locations.list')
    clean_info = parse_lines(lines)

    # write_base('data/locbase.txt')
    # create_file_with_unique_addresses('data/locbase.txt')

    while True:
        find_not_found_addresses('data/locbase.txt',
                                 'data/notfound.txt', clean_info)
        continuous_location_update('data/notfound.txt', 'data/locbase.txt')

    pass
