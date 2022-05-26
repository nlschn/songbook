from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
from app.models import User

class NewPlaylistForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max = 100)])
    submit = SubmitField("Create")

