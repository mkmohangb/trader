from flask_wtf import FlaskForm
from wtforms import IntegerField, RadioField
from wtforms.validators import InputRequired


class TradeForm(FlaskForm):

    instrument = RadioField('Instrument', choices=['NIFTY', 'BANKNIFTY'],
                            validators=[InputRequired()])
    stoploss = RadioField('StopLoss', choices=['FSL', 'CSL'],
                          validators=[InputRequired()])
    product = RadioField('Product', choices=['MIS', 'NRML'],
                         validators=[InputRequired()])
    expiry = RadioField('Expiry', choices=['Current Weekly', 'Next Weekly'],
                        validators=[InputRequired()])
    lots = IntegerField('Lots', validators=[InputRequired()])
