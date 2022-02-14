import io
import os
from datetime import datetime
from random import seed, choice
from tkinter import SE
from flask import Flask, render_template, Response, request
from matplotlib.backends.backend_agg import FigureCanvasAgg
from core_funcs import (
    ALL_COUNTRIES, ALL_REGIONS, COUNTRY_LIST,
    draw_country_border, calculate_distance_direction, filter_countries
)


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True


UNKNOWN_COUNTRY = 'error'
CURRENT_INPUT = ''
PREVIOUS_GUESSES = []
SELECTED_REGIONS = ALL_REGIONS


# @app.route("/<country_name>.png")
def plot_country(country_name):
    fig = draw_country_border(country_name)

    output = io.BytesIO()
    FigureCanvasAgg(fig).print_png(output)

    return Response(output.getvalue(), mimetype='image/png')


def guess():
    global CURRENT_INPUT, PREVIOUS_GUESSES

    guess = request.form['guess_input']

    if guess in ALL_COUNTRIES:
        dist, direc = calculate_distance_direction(UNKNOWN_COUNTRY, guess)
        CURRENT_INPUT = ''
        PREVIOUS_GUESSES.append((
            guess.upper(), f'{dist:.0f}', direc
            #f'{guess:>30s} | {dist:>5.0f} km | {direc}'
        ))
    else:
        CURRENT_INPUT = guess


def check_country_ok(country):
    return os.path.exists(f'static/images/{country}.png')


# @app.route('/new', methods=['POST'])
def new_random_country():
    global UNKNOWN_COUNTRY, PREVIOUS_GUESSES, CURRENT_INPUT
    CURRENT_INPUT = ''
    PREVIOUS_GUESSES = []

    possible_countries = filter_countries(
        only_geojson=True,
        regions=SELECTED_REGIONS,
        min_population=0,
        min_area=0,
    )

    UNKNOWN_COUNTRY = choice(possible_countries)


# @app.route("/")
def worldle():
    is_correct = (
        (len(PREVIOUS_GUESSES) > 0)
        and
        (UNKNOWN_COUNTRY == PREVIOUS_GUESSES[-1][0].lower())
    )
    print(is_correct)

    return render_template(
        'worldle.html',
        correct=is_correct,
        country=UNKNOWN_COUNTRY,
        country_list=COUNTRY_LIST,
        current_input=CURRENT_INPUT,
        previous_guesses=PREVIOUS_GUESSES
    )


@app.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        pass
    elif request.method == 'POST':
        if request.form.get('guess') == 'guess':
            guess()
        elif request.form.get('reset') == 'reset':
            new_random_country()

    return worldle()


d0 = datetime(2000, 1, 1)
d1 = datetime.now()
delta = d1 - d0
seed(delta.days)

new_random_country()

seed()