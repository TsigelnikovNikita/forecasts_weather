#!/usr/bin/env python3

# В очередной спешке, проверив приложение с прогнозом погоды, вы выбежали
# навстречу ревью вашего кода, которое ожидало вас в офисе.
# И тут же день стал хуже - вместо обещанной облачности вас встретил ливень.

# Вы промокли, настроение было испорчено, и на ревью вы уже пришли не в духе.
# В итоге такого сокрушительного дня вы решили написать свою программу для прогноза погоды
# из источника, которому вы доверяете.

# Для этого вам нужно:

# Создать модуль-движок с классом WeatherMaker, необходимым для получения и формирования предсказаний.
# В нём должен быть метод, получающий прогноз с выбранного вами сайта (парсинг + re) за некоторый диапазон дат,
# а затем, получив данные, сформировать их в словарь {погода: Облачная, температура: 10, дата:datetime...}

# Добавить класс ImageMaker.
# Снабдить его методом рисования открытки
# (использовать OpenCV, в качестве заготовки брать lesson_016/python_snippets/external_data/probe.jpg):
#   С текстом, состоящим из полученных данных (пригодится cv2.putText)
#   С изображением, соответствующим типу погоды
# (хранятся в lesson_016/python_snippets/external_data/weather_img ,но можно нарисовать/добавить свои)
#   В качестве фона добавить градиент цвета, отражающего тип погоды
# Солнечно - от желтого к белому
# Дождь - от синего к белому
# Снег - от голубого к белому
# Облачно - от серого к белому

# Добавить класс DatabaseUpdater с методами:
#   Получающим данные из базы данных за указанный диапазон дат.
#   Сохраняющим прогнозы в базу данных (использовать peewee)

# Сделать программу с консольным интерфейсом, постаравшись все выполняемые действия вынести в отдельные функции.
# Среди действий, доступных пользователю, должны быть:
#   Добавление прогнозов за диапазон дат в базу данных
#   Получение прогнозов за диапазон дат из базы
#   Создание открыток из полученных прогнозов
#   Выведение полученных прогнозов на консоль
# При старте консольная утилита должна загружать прогнозы за прошедшую неделю.

# Рекомендации:
# Можно создать отдельный модуль для инициализирования базы данных.
# Как далее использовать эту базу данных в движке:
# Передавать DatabaseUpdater url-путь
# https://peewee.readthedocs.io/en/latest/peewee/playhouse.html#db-url
# Приконнектится по полученному url-пути к базе данных
# Инициализировать её через DatabaseProxy()
# https://peewee.readthedocs.io/en/latest/peewee/database.html#dynamically-defining-a-database

import argparse
from weather_forecast_engine import ImageMaker, DataBaseUpdater

FUNC_DICT = {"create_cards": getattr(ImageMaker(), 'create_card'),
             "get_fc": getattr(DataBaseUpdater(), 'get_data'),
             "update_db": getattr(DataBaseUpdater(), 'update_db')}


def get_argv():
    parser = argparse.ArgumentParser(description="Weather forecast")
    parser.add_argument('action',
                        help='Choose action. Possible action: update_db | get_forecasts | create_cards')
    parser.add_argument('--of',
                        help='from where get_forecasts/create_cards,'
                             'default this is the first element in database. Example: --of=17.04.2020',
                        default=None, type=str)
    parser.add_argument('--to',
                        help='to where get_forecasts/create card,'
                             'default this is the last element in database. Example: --to=21.04.2020',
                        default=None, type=str)
    return parser.parse_args()


if __name__ == '__main__':
    action = get_argv()
    if action.action == 'update_db':
        func = FUNC_DICT[action.action]
        func()
    else:
        to = action.to
        of = action.of
        func = FUNC_DICT[action.action]
        func(to=to, of=of)
