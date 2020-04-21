#!/usr/bin/env python3

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
