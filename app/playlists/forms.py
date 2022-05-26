from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

class NewPlaylistForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max = 100)])
    submit = SubmitField("Create")

class AddSongToPlaylistForm(FlaskForm):
    title = StringField('Title', validators=[Length(max = 100)])
    artist = StringField('Artist', validators=[Length(max = 100)])
    submit = SubmitField("Add selected songs")