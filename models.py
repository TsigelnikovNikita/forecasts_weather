import datetime

from pony.orm import Database, Required, Json

db = Database()
db.bind(provider='postgres', user='postgres', host='localhost', password='postgres', database='weather_forecasts')


class WeatherForecasts(db.Entity):
    date = Required(datetime.datetime, unique=True)
    weather = Required(Json)


db.generate_mapping(create_tables=True)
