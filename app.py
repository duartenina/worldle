from audioop import maxpp
import io
import json
from dataclasses import dataclass
from datetime import datetime
from random import seed, choice
from flask import (
    Flask, render_template, Response, request, make_response
)
from matplotlib.backends.backend_agg import FigureCanvasAgg
from core_funcs import (
    ALL_COUNTRIES, ALL_REGIONS, COUNTRY_LIST,
    draw_country_border, calculate_distance_direction, filter_countries
)


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

@dataclass
class Worldle_Params:
    unknown_country: str = ''
    current_input: str = ''
    previous_guesses: list = ()
    num_countries: int = len(ALL_COUNTRIES)
    min_area_power: float = 0.
    max_area_power: float = 7.
    min_pop_power: float = 2.
    max_pop_power: float = 9.
    selected_regions: list = ALL_REGIONS


# @app.route("/<country_name>.png")
def plot_country(country_name):
    fig = draw_country_border(country_name)

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)

    return Response(output.getvalue(), mimetype='image/png')


def guess(params: Worldle_Params, response):
    guess = request.form['guess_input']

    if guess in ALL_COUNTRIES:
        dist, direc = calculate_distance_direction(
            params.unknown_country, guess
        )

        params.current_input = ''
        params.previous_guesses.append((
            guess.upper(), f'{dist:.0f}', direc
        ))
    else:
        params.current_input = guess

    response.set_cookie('current_input', params.current_input)

    previous_guesses_str = json.dumps(params.previous_guesses)
    response.set_cookie('previous_guesses', previous_guesses_str)

    return params


def new_random_country(params: Worldle_Params, response):
    current_input = ''
    response.set_cookie('current_input', current_input)

    previous_guesses = []
    previous_guesses_str = json.dumps(previous_guesses)
    response.set_cookie('previous_guesses', previous_guesses_str)

    if params.min_area_power > 0:
        min_area = 10**params.min_area_power
    else:
        min_area = None

    if params.max_area_power < 7:
        max_area = 10**params.max_area_power
    else:
        max_area = None

    if params.min_pop_power > 2:
        min_population = 10**params.min_pop_power
    else:
        min_population = None

    if params.max_pop_power < 9:
        max_population = 10**params.max_pop_power
    else:
        max_population = None

    possible_countries = filter_countries(
        only_geojson=True,
        regions=params.selected_regions,
        min_area=min_area,
        max_area=max_area,
        min_population=min_population,
        max_population=max_population
    )

    response.set_cookie('selected_regions', json.dumps(params.selected_regions))
    response.set_cookie('min_area_power', f'{params.min_area_power:.3f}')
    response.set_cookie('max_area_power', f'{params.max_area_power:.3f}')
    response.set_cookie('min_pop_power', f'{params.min_pop_power:.3f}')
    response.set_cookie('max_pop_power', f'{params.max_pop_power:.3f}')

    num_countries = len(possible_countries)
    response.set_cookie('num_countries', f'{num_countries}')

    if num_countries > 0:
        unknown_country = choice(possible_countries)
    else:
        unknown_country = 'error'
    response.set_cookie('unknown_country', unknown_country)

    params.unknown_country = unknown_country
    params.current_input = current_input
    params.previous_guesses = previous_guesses
    params.num_countries = num_countries

    return params


def initialize_params(response):
    # Same initial country, changes daily
    d0 = datetime(2000, 1, 1)
    d1 = datetime.now()
    delta = d1 - d0
    seed(delta.days)

    params = Worldle_Params()
    params = new_random_country(params, response)

    # next countries will be random
    seed()

    response.set_cookie('is_initialized', 'True')

    return params


def get_cookies(request, response, request_type=None):
    is_initialized = request.cookies.get('is_initialized')
    if is_initialized is None:
        vars = initialize_params(response)
        params = vars
    else:
        unknown_country = request.cookies.get('unknown_country')
        current_input = request.cookies.get('current_input')
        previous_guesses_str = request.cookies.get('previous_guesses')
        previous_guesses = json.loads(previous_guesses_str)
        num_countries = request.cookies.get('num_countries')

        if request_type == 'new_country':
            min_area_power = float(request.form.get('area_min'))
            max_area_power = float(request.form.get('area_max'))
            min_pop_power = float(request.form.get('population_min'))
            max_pop_power = float(request.form.get('population_max'))

            selected_regions = []
            for region in ALL_REGIONS:
                chk = request.form.get(region)
                if chk is not None:
                    selected_regions.append(region)

            if len(selected_regions) == 0:
                selected_regions = ALL_REGIONS

            selected_regions = selected_regions
        else:
            min_area_power = request.cookies.get('min_area_power')
            max_area_power = request.cookies.get('max_area_power')
            min_pop_power = request.cookies.get('min_pop_power')
            max_pop_power = request.cookies.get('max_pop_power')

            selected_regions_str = request.cookies.get('selected_regions')
            selected_regions = json.loads(selected_regions_str)

        params = Worldle_Params(
            unknown_country, current_input, previous_guesses,
            selected_regions=selected_regions, num_countries=num_countries,
            min_area_power=min_area_power, max_area_power=max_area_power,
            min_pop_power=min_pop_power, max_pop_power=max_pop_power
        )

    return params


def create_html(params: Worldle_Params):
    is_correct = (
        (len(params.previous_guesses) > 0)
        and
        (params.unknown_country == params.previous_guesses[-1][0].lower())
    )

    return render_template(
        'worldle.html',
        correct=is_correct,
        unknown_country=params.unknown_country,
        country_list=COUNTRY_LIST,
        current_input=params.current_input,
        previous_guesses=params.previous_guesses,
        num_countries=params.num_countries,
        all_regions=ALL_REGIONS,
        selected_regions=params.selected_regions,
        min_area_power=params.min_area_power,
        max_area_power=params.max_area_power,
        min_pop_power=params.min_pop_power,
        max_pop_power=params.max_pop_power,
    )


@app.route("/", methods=['GET', 'POST'])
def main():
    response = make_response()

    if request.method == 'GET':
        params = get_cookies(request, response, request_type=None)
    elif request.method == 'POST':
        if request.form.get('guess') == 'guess':
            params = get_cookies(request, response, request_type='guess')
            params = guess(params, response)
        elif request.form.get('reset') == 'reset':
            params = get_cookies(request, response, request_type='new_country')
            params = new_random_country(params, response)

    # save_params(params, response)

    html = create_html(params)
    response.set_data(html)

    return response


