from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os

url = "https://api.themoviedb.org/3/search/movie"
url_id = "https://api.themoviedb.org/3/movie/"
image_url = "https://image.tmdb.org/t/p/w500"

key = os.environ.get('M_KEY')

headers = {
    "accept": "application/json",
    "Authorization": key,
}

all_movies = []

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('F_KEY')
Bootstrap5(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
db = SQLAlchemy()
db.init_app(app)


class MovieForm(FlaskForm):
    rating = StringField('Your Rating Out of 10 e.g. 7.5')
    review = StringField('Your Review')
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", description='Enter the title of the movie e.g. The Matrix',
                        validators=[DataRequired()])
    submit = SubmitField("Add Movie")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    records = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_the_movies = records.scalars().all()
    for i in range(len(all_the_movies)):
        all_the_movies[i].ranking = len(all_the_movies) - i
    all_the_movies_sorted = sorted(all_the_movies, key=lambda x: x.ranking)
    return render_template("index.html", movies=all_the_movies_sorted)


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    form = MovieForm()
    the_movie = Movie.query.get(id)
    if form.validate_on_submit():
        the_movie.rating = float(form.rating.data)
        the_movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=the_movie, form=form)


@app.route('/<int:id>')
def delete(id):
    the_movie = Movie.query.get(id)
    db.session.delete(the_movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_search = form.title.data
        response = requests.get(url, headers=headers, params={'query': movie_search})
        results = response.json()['results']
        return render_template('select.html', options=results)
    return render_template('add.html', form=form)


@app.route('/save/<int:id>')
def save(id):
    response = requests.get(f'{url_id}{id}', headers=headers)
    the_movie = response.json()
    new_movie = Movie(
        title=the_movie['original_title'],
        year=the_movie['release_date'].split('-')[0],
        description=the_movie['overview'],
        img_url=f'{image_url}{the_movie["poster_path"]}'
    )
    db.session.add(new_movie)
    db.session.commit()
    movie_id = new_movie.id
    return redirect(url_for("edit", id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
