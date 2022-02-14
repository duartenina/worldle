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
class Worldle_Cookies:
    unknown_country: str
    current_input: str
    previous_guesses: list
    # selected_regions: list = ALL_REGIONS


# @app.route("/<country_name>.png")
def plot_country(country_name):
    fig = draw_country_border(country_name)

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)

    return Response(output.getvalue(), mimetype='image/png')


def guess(cookies: Worldle_Cookies, response):
    guess = request.form['guess_input']

    if guess in ALL_COUNTRIES:
        dist, direc = calculate_distance_direction(
            cookies.unknown_country, guess
        )

        cookies.current_input = ''
        cookies.previous_guesses.append((
            guess.upper(), f'{dist:.0f}', direc
        ))
    else:
        cookies.current_input = guess

    response.set_cookie('current_input', cookies.current_input)

    print(cookies.previous_guesses)
    previous_guesses_str = json.dumps(cookies.previous_guesses)
    response.set_cookie('previous_guesses', previous_guesses_str)

    return cookies


def new_random_country(cookies: Worldle_Cookies, response):
    current_input = ''
    response.set_cookie('current_input', current_input)

    previous_guesses = []
    previous_guesses_str = json.dumps(previous_guesses)
    response.set_cookie('previous_guesses', previous_guesses_str)

    possible_countries = filter_countries(
        only_geojson=True,
        # regions=SELECTED_REGIONS,
        # min_population=0,
        # min_area=0,
    )

    unknown_country = choice(possible_countries)
    response.set_cookie('unknown_country', unknown_country)

    if cookies is None:
        cookies = Worldle_Cookies(unknown_country, current_input, previous_guesses)
    else:
        cookies.unknown_country = unknown_country
        cookies.current_input = current_input
        cookies.previous_guesses = previous_guesses

    return cookies


def initialize_cookies(response):
    # Same initial country, changes daily
    d0 = datetime(2000, 1, 1)
    d1 = datetime.now()
    delta = d1 - d0
    seed(delta.days)

    cookies = new_random_country(None, response)

    # next countries will be random
    seed()

    response.set_cookie('is_initialized', 'True')

    return cookies


def get_cookies(request, response):
    is_initialized = request.cookies.get('is_initialized')
    if is_initialized is None:
        vars = initialize_cookies(response)
        cookies = vars
    else:
        unknown_country = request.cookies.get('unknown_country')
        current_input = request.cookies.get('current_input')
        previous_guesses_str = request.cookies.get('previous_guesses')
        previous_guesses = json.loads(previous_guesses_str)

        cookies = Worldle_Cookies(unknown_country, current_input, previous_guesses)

    return cookies


# def save_cookies(cookies, response):
#     pass


def create_html(cookies: Worldle_Cookies):
    is_correct = (
        (len(cookies.previous_guesses) > 0)
        and
        (cookies.unknown_country == cookies.previous_guesses[-1][0].lower())
    )

    return render_template(
        'worldle.html',
        correct=is_correct,
        unknown_country=cookies.unknown_country,
        country_list=COUNTRY_LIST,
        current_input=cookies.current_input,
        previous_guesses=cookies.previous_guesses
    )


@app.route("/", methods=['GET', 'POST'])
def main():
    response = make_response()
    cookies = get_cookies(request, response)

    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        if request.form.get('guess') == 'guess':
            cookies = guess(cookies, response)
        elif request.form.get('reset') == 'reset':
            cookies = new_random_country(cookies, response)

    # save_cookies(cookies, response)

    html = create_html(cookies)
    response.set_data(html)

    return response


