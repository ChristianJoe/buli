import requests
import bs4
from pprint import pprint
import json
import pandas as pd
import datetime
import logging

from ..fb import send_text
from pathlib import Path
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).absolute().parent.parent



# translation definition of
weapon = {"1" : "Luftgewehr",
          "2" : "Luftpistole",
         }
league = {"1" :  "2.BuLi Nord",
          "2" :  "2.BuLi Ost",
          "3" :  "2.BuLi West",
          "4" :  "2.BuLi Südwest",
          "5" :  "2.BuLi Süd",
          "6" :  "1.BuLi Nord",
          "7" :  "1.BuLi Süd"
        }
page_id = {"205" : "setlist",
           "231" : "date_result",
           "42" : "table 1.Nord Luftgewehr",
           "51" : "table 1.Süd Luftgewehr",
           "55" : "table 2.Nord Luftgewehr",
           "65" : "table 2.Süd Luftgewehr",
           "63" : "table 2.Südwest Luftgewehr",
           "61" : "table 2.West Luftgewehr",
           "57" : "table 2.Ost Luftgewehr",
           "42" : "table 1.Nord Luftpistole",
           "51" : "table 1.Süd Luftpistole",
           "55" : "table 2.Nord Luftpistole",
           "65" : "table 2.Süd Luftpistole",
           "63" : "table 2.Südwest Luftpistole",
           "61" : "table 2.West Luftpistole",
           "57" : "table 2.Ost Luftpistole",
          }
competitons = {"1.BuLi Nord": 11,
               "1.BuLi Süd": 11,
               "2.BuLi Süd": 6,
               "2.BuLi Nord": 4,
               "2.BuLi West": 4,
               "2.BuLi Ost":4,
               "2.BuLi Südwest":4
              }
inverted_weapon = dict([[v,k] for k,v in weapon.items()])
inverted_league = dict([[v,k] for k,v in league.items()])
inverted_page_id =  dict([[v,k] for k,v in page_id.items()])


# build html link
def build_html(kind, weapon, league, competition="1"):
    '''
    liga      1.2. nord/ost/sued/suedwest/west
    weapon    airrifle, airpistole
    competition 1-11
    '''
    # http://bundesliga.dsb.de/?page_id=55 table 1.Nord rifle
    if kind == "table":
        adding = "?page_id=" + inverted_page_id(kind + ' ' + league + ' ' + weapon)
    elif kind == "date" or kind == 'result':
        adding = "?page_id=231&waffe=" + inverted_weapon[weapon] + "&liga=" + inverted_league[
            league] + "&wettkampf=" + competition
    else:
        logger.info('wrong url')

    stemm = "http://bundesliga.dsb.de/"
    html = stemm + adding

    return html


# get results --- safe in csv
def get_results_pd():



    kind = "date"
    alphabet = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]
    data = []
    result_data = []
    first_name = []
    last_name = []
    clubs = []
    for weapon in inverted_weapon:
        for league in inverted_league:
            total_competitions = competitons[league]
            for competition in range(1, total_competitions + 1):

                site = build_html(kind, weapon, league, str(competition))
                response = requests.get(site)
                soup = bs4.BeautifulSoup(response.text, "lxml")

                tables = soup.find_all('table', {'class': 'ergebnisse-header'})
                tables2 = soup.find_all('table', {'class': 'ergebnisse', 'cellspacing': '0'})
                tables3 = soup.find_all('table', {'class': 'ergebnisse', 'style': 'width: 100%; cellspacing='})

                total_competitions = len(tables)
                total_stadiums = (len(tables3))
                comp_per_stadium = total_competitions / total_stadiums

                for i in range(0, total_competitions):
                    if weapon == "Luftgewehr":
                        weapon_short = "LG"
                    else:
                        weapon_short = "LP"

                    # ele for element
                    for index, ele in enumerate(tables):
                        tables3_index = int((index) / comp_per_stadium)
                        date = tables3[tables3_index].find_all('td')[0].text.replace('Begegnung am ', '')
                        host = tables3[tables3_index].find_all('td')[1].text.replace('Ausrichter: ', '').strip()
                        home_team = ele.find_all('td')[2].text.strip(),
                        guest_team = ele.find_all('td')[10].text.strip(),

                        for ending in ['II', 'I', '2', 'FSG']:
                            host = host.replace(ending, '').strip()
                            home_team_short = home_team[0].replace(ending, '').strip()
                            guest_team_short = guest_team[0].replace(ending, '').strip()
                        if home_team_short not in clubs:
                            clubs.append(home_team_short)

                        test = {
                            'home_team': home_team[0],
                            'home_team_short': home_team_short,
                            'home_result': int(ele.find_all('td')[4].text),
                            'home_points': int(ele.find_all('td')[5].text),
                            'guest_team': guest_team[0],
                            'guest_team_short': guest_team_short,
                            'guest_result': int(ele.find_all('td')[8].text),
                            'guest_points': int(ele.find_all('td')[7].text),
                            'time': ele.find_all('td')[1].text,
                            'date': date,
                            'host': host,
                            'site': site
                        }

                        test['winner'] = 'home' if test['home_points'] >= 3 else 'guest'
                        test['comp_id'] = weapon_short + league + str(competition) + (alphabet[i])
                        test['comp'] = index+1
                        test['league'] = league
                        test['weapon'] = weapon

                        if tables2:
                            subtables = tables2[index]
                            for pos in range(0, 5):
                                subtab = subtables.find_all('tr')[pos]
                                temp_home = {
                                    'comp_id': test['comp_id'],
                                    'team_full': test['home_team'],
                                    'home': True,
                                    'position': pos + 1,
                                    'first_name': subtab.find_all('td')[2].text.split(',')[1].strip(),
                                    'last_name': subtab.find_all('td')[2].text.split(',')[0].strip(),
                                    'result': int(subtab.find_all('td')[4].text),
                                    'point': int(subtab.find_all('td')[5].text),
                                    'shoot_off': subtab.find_all('td')[3].text

                                }
                                temp_guest = {
                                    'comp_id': test['comp_id'],
                                    'team_full': test['guest_team'],
                                    'home': False,
                                    'position': pos + 1,
                                    'first_name': subtab.find_all('td')[10].text.split(',')[1].strip(),
                                    'last_name': subtab.find_all('td')[10].text.split(',')[0].strip(),
                                    'result': int(subtab.find_all('td')[8].text),
                                    'point': int(subtab.find_all('td')[7].text),
                                    'shoot_off': subtab.find_all('td')[9].text

                                }
                                result_data.append(temp_home)
                                result_data.append(temp_guest)
                                if temp_home['first_name'] not in first_name:
                                    first_name.append(temp_home['first_name'])
                                if temp_guest['first_name'] not in first_name:
                                    first_name.append(temp_guest['first_name'])
                                if temp_home['last_name'] not in last_name:
                                    last_name.append(temp_home['last_name'])
                                if temp_guest['last_name'] not in last_name:
                                    last_name.append(temp_guest['last_name'])

                        data.append(test)

    result = pd.DataFrame(data)
    result_shooter = pd.DataFrame(result_data)

    result.to_csv(str(DATA_DIR/'data/team_results.csv'))
    result_shooter.to_csv(str(DATA_DIR/'data/shooter_results.csv'))

    # do the api.ai entities
    for list_names in [last_name, first_name, clubs]:
        add = 'last'
        if list_names == first_name:
            add = 'first'
        elif list_names == clubs:
            add = 'club'
        api = []
        for name in list_names:
            name2 = name.replace('-', ' ')
            name2 = name2.replace('/', ' ')
            name2 = name2.replace('van der', ' ')
            synonyms = [x for x in name2.split(' ')]
            synonyms.append(name)
            temp = {"value": name, "synonyms": synonyms}
            api.append(temp)

        with open(str(DATA_DIR/'data')+'/'+ add + 'names_apiai.json', "w", encoding="utf8") as output_file:
            json.dump(api, output_file, ensure_ascii=False)

    send_text('1642888035775604', 'Update done')

    return











