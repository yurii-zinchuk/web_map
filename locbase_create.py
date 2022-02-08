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


if __name__ == "__main__":
    lines = read_file('locations.list')
    clean_info = parse_lines(lines)
    geolocator = Nominatim(user_agent="my_request")

    cashed = dict()

    for point in clean_info:
        if len(point[2]) >= 3:
            loc = ', '.join(point[2].split(', ')[-3:])
        else:
            loc = point[2]
        if loc not in cashed:
            try:
                location = geolocator.geocode(loc)
                cashed[loc] = (location.longitude, location.latitude)
                with open('locbase', 'a', encoding='utf-8',
                          errors='ignore') as file:
                    file.write(loc + '\t' + str(location.longitude) + ' ' +
                               str(location.latitude) + '\n')
                print(loc)
                print(location.longitude, location.latitude)
            except Exception as err:
                print(f'!!!!!!!!{loc}!!!!!!!!!', err)
                cashed[loc] = 'failed'
