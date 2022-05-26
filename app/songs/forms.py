from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError

class SongSearchForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    artist = StringField('Artist', validators=[])
    submit = SubmitField('Search')

class LyricsForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max = 1000)])
    artist = StringField('Artist', validators=[DataRequired(), Length(max = 1000)])
    release = StringField('Release', validators=[DataRequired(), Length(max = 1000)])
    year = StringField('Year', validators=[DataRequired()])

    def validate_year(self, year):        
        try:
            y = int(year.data)
        except:
            raise ValidationError('The year must be a number.')

    capo = StringField('Capo', validators=[Length(max = 30)])
    notes = TextAreaField('Notes', validators=[Length(max = 1000)])
    lyrics = TextAreaField('Lyrics', validators=[DataRequired(), Length(max = 100000)])

    submit = SubmitField('Build')
    apply = SubmitField('Apply changes')

class LyricsFormAddToDb(FlaskForm):
    submit = SubmitField('Add to collection')
