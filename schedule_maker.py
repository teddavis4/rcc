#!/usr/bin/python
"""Parse espn.com for game schedules and inputs them into the database."""

__author__ = "Ted Davis"

import datetime
import requests
from bs4 import BeautifulSoup

url = "http://www.espn.com/mens-college-basketball/team/schedule/_/id/2305/kansas-jayhawks"

req = requests.get(url)
soup = BeautifulSoup(req.text, 'html.parser')


class Game():
    """Game represents a basketball game."""

    def __init__(self, td_data):
        """Build Game object."""
        self.date = td_data[0].text.strip()
        opponent = td_data[1].text.strip()
        self.home_game = True if opponent.split(' ')[0] == 'vs' else False
        self.opponent = ' '.join(opponent.split(' ')[1:])
        self.game_time = td_data[2].text.strip()

    def get_game_string(self):
        """Return human readable string of game details."""
        home_symbol = "vs" if not self.home_game else "at"
        return "Kansas {} {} at {} on {}".format(home_symbol,
                                                 self.opponent,
                                                 self.game_time,
                                                 self.date,)

    def get_database_input_query(self):
        """Return the SQL necessary to input game into DB."""
        game_date = self.get_game_datetime_obj()
        year = "2018"
        if game_date.month < 10:
            year = "2019"
        game_date = game_date.strftime("{}-%m-%d %H:%M:00-06".format(year))
        return "INSERT INTO games values ('{}', '{}');".format(
            self.opponent,
            game_date)

    def get_game_datetime_obj(self):
        """Return the true datetime object."""
        date_time = datetime.datetime.strptime(self.game_time + " " +
                                               self.date, '%I:%M %p %a, %b %d')
        date_time += datetime.timedelta(hours=-1)
        return date_time


def main():
    """Parse espn.com for KU basketball schedule."""
    trs = soup.find_all('tbody')[0].find_all('tbody')[
        0].find_all('tbody')[0].find_all('tr')
    for row in trs:
        tds = row.find_all('td')
        try:
            game_info = Game(tds)
            print(game_info.get_game_string())
            print(game_info.get_database_input_query())
            print('-' * 80)
        except BaseException as exc:
            print(exc)


main()
