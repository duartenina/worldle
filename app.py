import io
from random import choice
from flask import Flask, render_template, Response, request
from matplotlib.backends.backend_agg import FigureCanvasAgg
from core_funcs import ALL_COUNTRIES, draw_country_border, calculate_distance_direction


app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True


COUNTRY_LIST = list(ALL_COUNTRIES.keys())
UNKNOWN_COUNTRY = 'albania'
CURRENT_INPUT = ''
PREVIOUS_GUESSES = []


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
            guess, f'{guess:>30s} | {dist:>5.0f} km | {direc}'
        ))
    else:
        CURRENT_INPUT = guess

    return worldle()


# @app.route('/new', methods=['POST'])
def new_random_country():
    global UNKNOWN_COUNTRY, PREVIOUS_GUESSES, CURRENT_INPUT
    CURRENT_INPUT = ''
    PREVIOUS_GUESSES = []

    UNKNOWN_COUNTRY = choice(COUNTRY_LIST)

    return worldle()


# @app.route("/")
def worldle():
    is_correct = (
        (len(PREVIOUS_GUESSES) > 0)
        and
        (UNKNOWN_COUNTRY == PREVIOUS_GUESSES[-1][0])
    )
    print(PREVIOUS_GUESSES)
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
        return worldle()
    elif request.method == 'POST':
        if request.form.get('guess') == 'guess':
            print('guess')
            return guess()
        elif request.form.get('reset') == 'reset':
            print('reset')
            return new_random_country()