import requests
import bs4
import json
import pandas as pd
import datetime
import logging
from selenium import webdriver
browser = webdriver.PhantomJS()
import os
import pathlib

from ..data import reopen_data
from ..fb import send_text
from pathlib import Path
logger = logging.getLogger(__name__)
from backend.models import FacebookUser, CompetitionStatus



DATA_DIR = Path(__file__).absolute().parent.parent



# translation
weapon = {"1" : "Luftgewehr",
          "2" : "Luftpistole",
         }
league = {"6" :  "1.BuLi Nord",
          "7" :  "1.BuLi Süd",
          "1" :  "2.BuLi Nord",
          "2" :  "2.BuLi Ost",
          "3" :  "2.BuLi West",
          "4" :  "2.BuLi Südwest",
          "5" :  "2.BuLi Süd"

        }
page_id = {"205" : "setlist",
           "231" : "date_result",
           "42" : "table 1.BuLi Nord Luftgewehr",
           "51" : "table 1.BuLi Süd Luftgewehr",
           "55" : "table 2.BuLi Nord Luftgewehr",
           "65" : "table 2.BuLi Süd Luftgewehr",
           "63" : "table 2.BuLi Südwest Luftgewehr",
           "61" : "table 2.BuLi West Luftgewehr",
           "57" : "table 2.BuLi Ost Luftgewehr",
           "46" : "table 1.BuLi Nord Luftpistole",
           "123" : "table 1.BuLi Süd Luftpistole",
           "128" : "table 2.BuLi Nord Luftpistole",
           "142" : "table 2.BuLi Süd Luftpistole",
           "140" : "table 2.BuLi Südwest Luftpistole",
           "136" : "table 2.BuLi West Luftpistole",
           "134" : "table 2.BuLi Ost Luftpistole",
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
        adding = "?page_id=" + inverted_page_id[kind + ' ' + league + ' ' + weapon]
    elif kind == "date" or kind == 'result':
        adding = "?page_id=231&waffe=" + inverted_weapon[weapon] + "&liga=" + inverted_league[
            league] + "&wettkampf=" + competition
    elif kind == "setlist":
        adding = "?page_id=205&waffe=" + inverted_weapon[weapon] + inverted_league[league] + "&kompl=1"

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
    counter = 1
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

                    home_team_short = home_team[0]
                    guest_team_short = guest_team[0]
                    home_team1 = home_team[0]
                    guest_team1 = guest_team[0]

                    for ending in [' II', ' I', ' 2', 'FSG']:
                        if host.endswith(ending) or ending == 'FSG':
                            host = host.replace(ending, '').strip()
                        if home_team_short.endswith(ending) or ending == 'FSG':
                            home_team_short = home_team_short.replace(ending, '').strip()
                        if guest_team_short.endswith(ending) or ending == 'FSG':
                            guest_team_short = guest_team_short.replace(ending, '').strip()
                    if home_team1 == 'ST Hubertus Elsen':
                        home_team1 = 'ST Hubertus Elsen I'
                    if guest_team1 == 'ST Hubertus Elsen':
                        guest_team1 = 'ST Hubertus Elsen I'

                    if home_team1 == 'PSV Olympia Berlin':
                        if weapon_short == 'LG':
                            home_team1 = 'PSV Olympia Berlin LG'
                        elif '1.BuLi' in league:
                            home_team1 = 'PSV Olympia Berlin I'
                    if guest_team1 == 'PSV Olympia Berlin':
                        if weapon_short == 'LG':
                            guest_team1 = 'PSV Olympia Berlin LG'
                        elif '1.BuLi' in league:
                            guest_team1 = 'PSV Olympia Berlin I'
                    if home_team1 == 'SG Hamm I':
                        home_team1 = 'SG Hamm'
                    if guest_team1 == 'SG Hamm I':
                        guest_team1 = 'SG Hamm'


                    if home_team_short not in clubs:
                        clubs.append(home_team_short)

                    test = {
                        'home_team': home_team1,
                        'home_team_short': home_team_short,
                        'home_result': int(ele.find_all('td')[4].text),
                        'home_points': int(ele.find_all('td')[5].text),
                        'guest_team': guest_team1,
                        'guest_team_short': guest_team_short,
                        'guest_result': int(ele.find_all('td')[8].text),
                        'guest_points': int(ele.find_all('td')[7].text),
                        'time': ele.find_all('td')[1].text,
                        'date': date,
                        'host': host,
                        'site': site,
                    }

                    test['winner'] = 'home' if test['home_points'] >= 3 else 'guest'
                    test['comp_id'] = weapon_short + league + str(competition) + (alphabet[index])
                    test['comp'] = index+1
                    test['league'] = league
                    test['weapon'] = weapon

                    if tables2:
                        try:
                            subtables = tables2[index]
                            for pos in range(0, 5):
                                posstr_id = test['comp_id']+str(pos+1)
                                subtab = subtables.find_all('tr')[pos]
                                temp_home = {
                                    'comp_id': test['comp_id'],
                                    'team_full': test['home_team'],
                                    'team_short': test['home_team_short'],
                                    'home': True,
                                    'position': pos + 1,
                                    'first_name': subtab.find_all('td')[2].text.split(',')[1].strip(),
                                    'last_name': subtab.find_all('td')[2].text.split(',')[0].strip(),
                                    'result': int(subtab.find_all('td')[4].text),
                                    'point': int(subtab.find_all('td')[5].text),
                                    'shoot_off': subtab.find_all('td')[3].text,
                                    'pos_id': posstr_id,
                                    'counter': counter

                                }
                                temp_guest = {
                                    'comp_id': test['comp_id'],
                                    'team_full': test['guest_team'],
                                    'team_short': test['guest_team_short'],
                                    'home': False,
                                    'position': pos+1,
                                    'first_name': subtab.find_all('td')[10].text.split(',')[1].strip(),
                                    'last_name': subtab.find_all('td')[10].text.split(',')[0].strip(),
                                    'result': int(subtab.find_all('td')[8].text),
                                    'point': int(subtab.find_all('td')[7].text),
                                    'shoot_off': subtab.find_all('td')[9].text,
                                    'pos_id':posstr_id,
                                    'counter': counter

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
                            counter += 1
                        except:
                            x=None
                    data.append(test)

    result = pd.DataFrame(data)
    result_shooter = pd.DataFrame(result_data)

    result.to_csv(str(DATA_DIR/'data/team_results.csv'))
    result_shooter.to_csv(str(DATA_DIR/'data/shooter_results.csv'))



    #tabelle


    #send_text('1642888035775604', 'Update_results done')

    return


def update_table():

    kind = "table"
    tables_all = []
    clubs = []
    for weapon in inverted_weapon:

        # for i in range(0,total_competitions):
        if weapon == "Luftgewehr":
            weapon_short = "LG"
        else:
            weapon_short = "LP"
        for league in inverted_league:
            site = build_html(kind, weapon, league, str(1))
            response = requests.get(site)
            soup = bs4.BeautifulSoup(response.text, "lxml")
            table = soup.find_all('table', class_='ergebnisse')[0]
            rows = table.find_all('tr')
            for index, row in enumerate(rows):
                values = row.find_all('td')
                link_text = 'nope'
                for a in row.find_all('a', href=True):
                    if a.get_text(strip=True):
                        link_text = a['href']
                if index != 0:
                    home_team = values[1].text
                    if home_team == 'ST Hubertus Elsen':
                        home_team = 'ST Hubertus Elsen I'
                    if home_team == 'PSV Olympia Berlin':
                        if weapon_short == 'LG':
                            home_team = 'PSV Olympia Berlin LG'
                        elif '1.BuLi' in league:
                            home_team = 'PSV Olympia Berlin I'
                    if home_team == 'SG Hamm I':
                        home_team = 'SG Hamm'


                    temp = {'rank': values[0].text,
                            'club': home_team,
                            'single_won': values[2].text.split(':')[0],
                            'single_lost': values[2].text.split(':')[1],
                            'team_won': values[3].text.split(':')[0],
                            'team_lost': values[3].text.split(':')[1],
                            'club_page': link_text,
                            'id': weapon_short + league

                            }
                    temp['comps'] = (int(temp['team_won'])+int(temp['team_lost']))/2

                    tables_all.append(temp)

    tables = pd.DataFrame(tables_all)
    tables.to_csv(str(DATA_DIR/'data/buli17_tables.csv'))

    #send_text('1642888035775604', 'Update_table done')


def get_setlist():
    kind = "setlist"
    tables_all = []
    clubs = []
    first_name = []
    last_name = []
    for weapon in inverted_weapon:

        # for i in range(0,total_competitions):
        if weapon == "Luftgewehr":
            weapon_short = "LG"
        else:
            weapon_short = "LP"
        for league in inverted_league:
            site = build_html(kind, weapon, league, str(1))
            response = requests.get(site)
            soup = bs4.BeautifulSoup(response.text, "lxml")
            table = soup.find_all('table', class_='same-page')
            for index1, row in enumerate(table):
                if index1 > 0:
                    small = row.find_all('tr')

                    for index2, ro in enumerate(small):
                        if index2 == 0:

                            club = ro.find_all('b')[0].text
                            club_short = club
                            for ending in [' II', ' I', ' 2', 'FSG']:
                                if club_short.endswith(ending):
                                    club_short = club_short.replace(ending, '').strip()
                            if club == 'ST Hubertus Elsen':
                                club = 'ST Hubertus Elsen I'
                            if club == 'PSV Olympia Berlin':
                                if weapon_short == 'LG':
                                    club = 'PSV Olympia BerlinLG'
                                elif '1.BuLi' in league:
                                    club = 'PSV Olympia Berlin I'
                            if club_short == 'SG Hamm':
                                club = club_short
                        else:
                            temp = {}
                            number_of_comps = 0
                            best = [0]
                            for index3, element in enumerate(ro.find_all('td')):

                                temp['club'] = club
                                temp['club_short'] = club_short
                                temp['buli'] = league
                                temp['league'] = league.split(' ')[0]
                                temp['region'] = league.split(' ')[1]
                                temp['weapon'] = weapon_short
                                temp['id'] = weapon_short + league
                                if index3 == 0:
                                    temp['first_name'] = element.text.split(',')[1].strip()
                                    temp['last_name'] = element.text.split(',')[0].strip()
                                    if temp['first_name'] not in first_name:
                                        first_name.append(temp['first_name'])
                                    if temp['last_name'] not in last_name:
                                        last_name.append(temp['last_name'])
                                elif index3 == 1:
                                    temp['fixed'] = True if element.text == 'S' else False
                                elif index3 == 2:
                                    temp['avg'] = element.text
                                else:
                                    temp[str(index3 - 2)] = element.text
                                    testelement = int(element.text)
                                    if testelement > 0 :
                                        number_of_comps +=1
                                        best.append(testelement)
                            temp['numer_of_comps'] = number_of_comps
                            temp['best'] = max(best)

                            tables_all.append(temp)

    setlist = pd.DataFrame(tables_all)
    setlist.to_csv(str(DATA_DIR/'data/buli17_setlist.csv'))

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

        with open(str(DATA_DIR / 'data') + '/' + add + 'names_apiai.json', "w", encoding="utf8") as output_file:
            json.dump(api, output_file, ensure_ascii=False)

    #send_text('1642888035775604', 'Update_results done')





def get_meyton(hrefs = False):


    site = "http://bundesliga.meyton.info/"

    response = requests.get(site)
    soup = bs4.BeautifulSoup(response.text, "lxml")
    menu = soup.find_all('div', class_='menu')[0]
    sub = menu.find_all('a', href=True)
    # print(sub[2])
    links = {}
    for index, b in enumerate(sub):

        if b.get_text(strip=True):
            link_text = b['href']
        if index == 0:
            basis = link_text
        else:
            links[b.text] = basis + link_text

    """         
    for key, value in links.items():
        site = value
        if not hrefs:

            get_meyton_results(site)
    """
    return links


def get_meyton_results(site):

    browser.implicitly_wait(3)
    browser.get(site)
    html = browser.page_source
    soup = bs4.BeautifulSoup(html, "lxml")

    fight = soup.find(id='match-phase').text
    path = pathlib.Path(str(DATA_DIR)+'/data/competitions/temp.csv')


    if fight != 'Zur Zeit kein Wettkampf1':

        teams = soup.find(id='match-title').text.split(':')
        try:
            home_team = teams[0].strip()
            guest_team = teams[1].strip()
        except:
            browser.implicitly_wait(5)
            browser.get(site)
            html = browser.page_source
            soup = bs4.BeautifulSoup(html, "lxml")
            teams = soup.find(id='match-title').text.split(':')
            home_team = teams[0].strip()
            guest_team = teams[1].strip()

        # update database
        #check if id exists, otherwise create and 'open status
        cid = home_team+guest_team
        if CompetitionStatus.objects.filter(cid=cid).exists():
            status = CompetitionStatus.objects.get(cid=cid)
        else:
            CompetitionStatus.objects.create(cid=cid)
            status = CompetitionStatus.objects.get(cid=cid)
        #update status
        if fight == 'Probe':
            CompetitionStatus.objects.filter(cid=cid).update(practice=True)
        if fight == 'Wettkampf':
            CompetitionStatus.objects.filter(cid=cid).update(competition=True)
        if fight =='Gleichstand bei mindestens einer Paarung':
            CompetitionStatus.objects.filter(cid=cid).update(shoot_off=True)
        if fight == 'Stechen um Einzelpunkt':
            CompetitionStatus.objects.filter(cid=cid).update(shoot_off_shot=True)
        if fight == 'Wettkampf ist beendet':
            CompetitionStatus.objects.filter(cid=cid).update(finished=True)
            #test purpose
            #CompetitionStatus.objects.filter(cid=cid).update(finished=False)
            #CompetitionStatus.objects.filter(cid=cid).update(push=False)


        file = (home_team + guest_team + '.csv').replace(' ', '')
        path = pathlib.Path(str(DATA_DIR)+'/data/competitions/'+file)

        res = soup.find(id='results').find_all('tr')
        temp2 = []
        mapping = {2: 'homeA', 5: 'homeB', 8: 'homeC', 11: 'homeD', 14: 'homeE',
                   3: 'guestA', 6: 'guestB', 9: 'guestC', 12: 'guestD', 15: 'guestE'
                   }
        for index, row in enumerate(res):
            result = row.find_all('td')
            if index > 0:
                if index in [2, 3, 6, 9, 12, 15, 5, 8, 11, 14]:
                    temp = {}
                    temp['cid'] = cid
                    temp['home_team'] = home_team
                    temp['guest_team'] = guest_team
                    temp['fight'] = fight
                    temp['time'] = soup.find(id='js-clock-blticker').text
                    temp['name'] = result[0].text
                    temp['id'] = mapping[index]
                    temp['shot_nr'] = result[1].text.strip()
                    temp['shot_value'] = result[2].text.strip()
                    temp['result'] = result[4].text
                    if index in [3, 6, 9, 12, 15]:
                        try:
                            temp['points'] = result[5].text
                        except:
                            temp['points'] = None
                    else:
                        temp['points'] = None
                    series = []
                    for element in result[3].text.replace('\xa0', ' ').split(' '):
                        if element:
                            series.append(element)
                    temp['series'] = series
                    temp2.append(temp)

        final = pd.DataFrame(temp2)

    else:
        final = 'Zur Zeit kein Wettkampf'


    if fight != 'Zur Zeit kein Wettkampf':
        # check if file already exists and append data

        if path.is_file():
            open_file = pd.read_csv(path)

            added_final = open_file.append(final, ignore_index=True)
            added_final.to_csv(path, index=False)

        else:
            #if not, create file
            final.to_csv(path, index=False)



    return final


def update_results(event, **kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id, 'Update ist in arbeit...')
    get_results_pd()
    reopen_data()



def update_table_payload(event, **kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id, 'Update ist in arbeit...')
    update_table()
    reopen_data()


def update_setlist_payload(event, **kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id, 'Update ist in arbeit...')
    get_setlist()
    reopen_data()