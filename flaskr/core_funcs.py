import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from countryinfo import CountryInfo

ALL_COUNTRIES = CountryInfo().all()
COUNTRY_LIST = list(ALL_COUNTRIES.keys())
ALL_REGIONS = ('Africa', 'Americas', 'Asia', 'Europe', 'Oceania')
EARTH_RADIUS = 6378.1       # km
DIRECTION_ARROWS = {
    0: '🢂',
    45: '🢅',
    90: '🢁',
    135: '🢄',
    180: '🢀',
    -45: '🢆',
    -90: '🢃',
    -135: '🢇',
    -180: '🢀',
    360: '✓',
}


def process_countries_into_dataframe():
    data_for_df = []
    for country_name in ALL_COUNTRIES:
        country = ALL_COUNTRIES[country_name]

        area = country.get('area', np.nan)
        pop = country.get('population', np.nan)
        region = country.get('region', '')
        has_geometry = (
            ('geoJSON' in country)
            and
            (country['geoJSON'] != {})
        )

        data_for_df.append(
            (country_name, region, area, pop, has_geometry)
        )

    return pd.DataFrame(
        data_for_df,
        columns=['name', 'region', 'area', 'population', 'has_geometry']
    )
COUNTRY_DF = process_countries_into_dataframe()


def draw_and_save_all_countries():
    for country in ALL_COUNTRIES:
        fig = draw_country_border(country)

        if fig is not None:
            fig.savefig(f'static/images/{country}.png', transparent=True)

        plt.close(fig)


def filter_countries(only_geojson=True, regions=ALL_REGIONS,
                     min_area=None, max_area=None,
                     min_population=None, max_population=None):

    inds = COUNTRY_DF['region'].isin(regions)

    if only_geojson:
        inds &= COUNTRY_DF['has_geometry']

    if min_area is not None:
        inds &= COUNTRY_DF['area'] >= min_area

    if max_area is not None:
        inds &= COUNTRY_DF['area'] <= max_area

    if min_population is not None:
        inds &= COUNTRY_DF['population'] >= min_population

    if max_population is not None:
        inds &= COUNTRY_DF['population'] <= max_population

    return list(COUNTRY_DF[inds]['name'])


def draw_country_border(country_name):
    country_info = ALL_COUNTRIES[country_name.lower()]

    fig = plt.figure()
    ax = fig.add_subplot(111)

    plt.axis('off')
    plt.axis('equal')

    try:
        country_geo = country_info['geoJSON']['features'][0]['geometry']
    except KeyError:
        return None

    if country_geo['type'] == 'Polygon':
        coords = np.array(country_geo['coordinates'][0])
        plt.fill(coords[..., 0], coords[..., 1], color='r')
    elif country_geo['type'] in ['Polygon', 'MultiPolygon']:
        for polygon in country_geo['coordinates']:
            coords = np.array(polygon[0])
            plt.fill(coords[..., 0], coords[..., 1], color='r')
    else:
        print(country_geo['type'])

    # plt.title(country_info.name().capitalize())

    plt.xticks([])
    plt.yticks([])

    return fig


def calculate_distance_direction(country_1, country_2):
    coords_1 = ALL_COUNTRIES[country_1]['latlng']
    coords_2 = ALL_COUNTRIES[country_2]['latlng']
    lat1, lng1 = np.radians(coords_1)
    lat2, lng2 = np.radians(coords_2)

    dlat = lat2 - lat1
    dlng = lng2 - lng1

    temp = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlng/2)**2
    dist = 2 * EARTH_RADIUS * np.arctan2(np.sqrt(temp), np.sqrt(1 - temp))

    angle = np.rad2deg(np.arctan2(-dlat, -dlng))
    direction = int(45 * np.round(angle / 45))

    if dist == 0:
        direction_str = DIRECTION_ARROWS[360]
    else:
        direction_str = DIRECTION_ARROWS[direction]

    # print((
    #     f'{coords_1} -> {coords_2} | '
    #     f'{np.rad2deg(dlat):.0f}, {np.rad2deg(dlng):.0f} | '
    #     f'd = {dist:.0f} | ang = {angle:.0f} | dir = {direction} | {direction_str}'
    # ))

    return dist, direction_str


if __name__ == '__main__':
    random_country = np.random.choice(list(ALL_COUNTRIES.keys()))
    random_country = 'albania'

    draw_country_border(random_country)

    # for country in ['iceland', 'spain', 'brazil', 'norway', 'guinea', 'india']:
    #     dist, dir = calculate_distance_direction('portugal', country)
    #     print(country, f'{dist:.0f}', dir)

    for country in ['serbia', 'romania']:
        dist, dir = calculate_distance_direction(random_country, country)
        print(country, f'{dist:.0f}', dir)
