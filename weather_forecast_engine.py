import os
from os import path

import cv2
import cairosvg

import requests
from bs4 import BeautifulSoup

from pony.orm import db_session
from models import WeatherForecasts

import datetime as dt
from datetime import datetime

from collections import OrderedDict

SEASONS = {"января": 1, "февраля": 2, "марта": 3, "апреля": 4,
           "мая": 5, "июля": 6, "июня": 7, "августа": 8,
           "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12}

URL = "https://yandex.ru/pogoda/ufa/details?via=ms"
TEMPLATE_PATH = os.path.abspath('template.jpg')
TEMPLATE = cv2.imread(TEMPLATE_PATH)

GRADIENT_DICT = {"пасмурно дождь": (0, 77, 255),
                 "солнечно": (255, 255, 92),
                 "облачно малооблачно": (180, 184, 176),
                 "снег": (74, 204, 247)}


class DataBaseUpdater:
    """
    Класс делает запрос на сервер.
    Получает прогноз погоды на следующие десять дней
    и подходящие иконки, если их нет в папке icons
    """

    def __init__(self):
        self.list_of_days = list()
        self.list_class_of_day = ['forecast-details__day-number',
                                  'forecast-details__day-month']
        self.list_class_of_weather = ['weather-table__daypart',
                                      'weather-table__temp',
                                      'weather-table__body-cell_type_condition',
                                      'weather-table__body-cell_type_humidity']

    def parse(self):
        """
        Функция парсит страницу на карточки прогноза погоды
        :return:
        """
        weather = requests.get(URL)
        html_doc = BeautifulSoup(weather.text, features='html.parser')
        self.list_of_days = html_doc.find_all('div', {'class': 'card'})

    @db_session
    def update_db(self):
        """
        Функция парсит информацию о погоде в и записывает в базу данных
        :return:
        """
        self.parse()
        for day_info in self.list_of_days:
            if day_info.find("div", {"class": "adv"}):
                continue

            day, month = self.get_info(day_info, self.list_class_of_day)
            date = self.get_date(int(day), SEASONS[month])

            weather_forecast = {}
            weather_forecast['дата'] = date
            weather_forecast['погода'] = OrderedDict()
            weather_row = day_info.find_all(attrs={"class": "weather-table__row"})

            for weather in weather_row:
                times_of_day, temperature, condition, wind = self.get_info(weather, self.list_class_of_weather)
                weather_forecast['погода'][times_of_day] = (temperature.replace('−', '-'), condition, wind)

                if not path.exists(path.abspath(path.join('icons', f'{condition}.png'))):
                    self.get_icon(condition, weather)
            if WeatherForecasts.get(date=date):
                continue
            WeatherForecasts(date=weather_forecast['дата'], weather=weather_forecast['погода'])

    @db_session
    def get_data(self, of=None, to=None):
        of, to = self.get_section(of, to)
        for i in range(of, to + 1):
            forecast = WeatherForecasts.get(id=i)
            date = forecast.date.strftime('%A, %d %B, %Y')
            print(f"{date}:")
            for time_to_day, weather in forecast.weather.items():
                print(f'\t{time_to_day.title()}:')
                print(f"\t\t{' | '.join(p for p in weather)}")

    def get_section(self, of, to):
        list_forecasts = list(WeatherForecasts.select(lambda p: p.id).order_by(WeatherForecasts.id))
        if of:
            of = datetime.strptime(of, '%d.%m.%Y')
            of = WeatherForecasts.get(date=of).id
        else:
            of = list_forecasts[0].id
        if to:
            to = datetime.strptime(to, '%d.%m.%Y')
            to = WeatherForecasts.get(date=to).id
        else:
            to = list_forecasts[-1].id
        return of, to

    def get_info(self, day_info, list_of_class):
        """
        Вспомогатеьная функция для извлечения информации о погоде
        :param day_info:
        :param list_of_class:
        :return:
        """
        info_list = []
        for _class in list_of_class:
            info_list.append(day_info.find(attrs={"class": _class}).text)
        return info_list

    def get_date(self, day, month):
        """
        Функция ковертирования даты
        :param day:
        :param month:
        :return:
        """
        current_year = datetime.now().year
        date = dt.datetime(current_year, month, day)
        return date

    def get_icon(self, condition, day_info):
        img = day_info.find('img')
        url = f"https:{img.get('src')}"
        icon_png_path = path.abspath(path.join('icons', f'{condition}.png'))
        cairosvg.svg2png(url=url, write_to=icon_png_path)
        icon = cv2.imread(path.abspath(icon_png_path))
        icon = self.get_white_background(icon)
        cv2.imwrite(icon_png_path, icon)

    def get_white_background(self, icon):
        """
        Вспомогательная функция, делает фон белым
        :param icon:
        :return:
        """
        height, width, channels = icon.shape
        for x in range(0, width):
            for q in range(0, height):
                if icon[x, q, 0] == icon[x, q, 1] == icon[x, q, 2] == 0:
                    icon[x, q, 0] = icon[x, q, 1] = icon[x, q, 2] = 255
        return icon


class ImageMaker(DataBaseUpdater):
    """
    Класс получение карточек погоды
    """

    @db_session
    def create_card(self, of=None, to=None):

        of, to = self.get_section(of, to)

        for i in range(of, to + 1):
            image = TEMPLATE.copy()
            forecast = WeatherForecasts.get(id=i)
            date = forecast.date.strftime('%A, %d %B, %Y')
            weather = forecast.weather

            if path.exists(path.abspath(path.join('cards', f'{date}.png'))):
                continue

            self.write_icons(weather, image)
            self.gradient(weather['днём'][1], image)
            cv2.putText(img=image, text=date, org=(10, 30), fontFace=cv2.FONT_HERSHEY_COMPLEX,
                        fontScale=0.7, color=(133, 133, 133), thickness=2, lineType=cv2.LINE_AA)

            self.write_weather_info(weather, image)
            cv2.imwrite(path.join('cards', f'{date}.png'), image)

    def write_icons(self, weather, image):
        for weather_info, y in zip(weather.values(), range(70, 500, 40)):
            weather_type = weather_info[1]

            if not path.exists(path.abspath(path.join('icons', f'{weather_type}.png'))):
                DataBaseUpdater().update_db()

            icon = cv2.imread(path.abspath(path.join('icons', f'{weather_type}.png')))
            image[y - 20:y + 4, 390:414] = icon

    def write_weather_info(self, weather, image):
        for weather_tuple, y in zip(weather.items(), range(70, 500, 40)):
            weather_time, weather_info = weather_tuple
            data = f"{weather_time}: {weather_info[0].replace('…', '...').replace('°', '')}  {weather_info[1]}"
            cv2.putText(img=image, text=data, org=(10, y), fontFace=cv2.FONT_HERSHEY_COMPLEX,
                        fontScale=0.5, color=(255, 0, 0), thickness=1, lineType=cv2.LINE_AA)

    def gradient(self, type_weather, image):
        r, g, b = self.get_color(type_weather)
        width, high, _ = image.shape
        step_r, step_g, step_b = (255 - r) / width, (255 - g) / width, (255 - b) / width

        for px_w in range(width):
            for px_h in range(high):
                if image[px_w, px_h, 0] == image[px_w, px_h, 0] == image[px_w, px_h, 0] == 255:
                    image[px_w, px_h, 0] = b
                    image[px_w, px_h, 1] = g
                    image[px_w, px_h, 2] = r
            r, g, b = r + step_r, g + step_g, b + step_b

    def get_color(self, type_weather):
        for key, value in GRADIENT_DICT.items():
            if any(word.lower() in key for word in type_weather.split()):
                return value
