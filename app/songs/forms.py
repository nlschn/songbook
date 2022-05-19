from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User

class SongSearchForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    artist = StringField('Artist', validators=[DataRequired()])
    submit = SubmitField('Search')

class LyricsForm(FlaskForm):
    lyrics = TextAreaField('Lyrics', validators=[DataRequired(), Length(max = 100000)])
    submit = SubmitField('Build')