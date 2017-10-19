
import json
import random
import logging
from pathlib import Path
from collections import defaultdict
import operator
from itertools import groupby
import pandas as pd


logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).absolute().parent

party_list = json.load(open(str(DATA_DIR/'parteien_info.json')))['list']
candidate_list = json.load(open(str(DATA_DIR/'alle_kandidaten.json')))['list']
district_list = json.load(open(str(DATA_DIR/'wahlkreis_info.json')))['districts']
election13_dict = json.load(open(str(DATA_DIR/'wahlkreis_info.json')))['election13']
election17_dict = json.load(open(str(DATA_DIR/'results/results_17.json')))['election_17']
digital_word_list = json.load(open(str(DATA_DIR/'digital_words.json')))['words']


structural_data_district = pd.read_csv(DATA_DIR/'btw17_strukturdaten.csv', delimiter = ';')

### Daten shooting
results_team = pd.read_csv(DATA_DIR / 'team_results.csv')
dates = pd.read_csv(DATA_DIR / 'parser/buli17dates.csv')
tables = pd.read_csv(DATA_DIR / 'buli17_tables.csv')
results_shooter = pd.read_csv(DATA_DIR / 'shooter_results.csv')
#setlist = pd.read_csv(DATA_DIR / 'buli17_setlist.csv')

def reopen_data():
    global tables
    tables = pd.read_csv(DATA_DIR / 'buli17_tables.csv')
    global results_shooter
    results_shooter = pd.read_csv(DATA_DIR / 'shooter_results.csv')
    global results_team
    results_team = pd.read_csv(DATA_DIR / 'team_results.csv')
    global setlist
    setlist = pd.read_csv(DATA_DIR / 'buli17_tables.csv')



def get_results_shooter():
    return results_shooter


def get_results_team():
    results_team['date'] = pd.to_datetime(results_team['date'],format='%d.%m.%Y')

    return results_team


def get_dates():
    # load data BuLi
    dates['date'] = pd.to_datetime(dates['date'])
    dates_sorted = dates.sort_values(by='date')
    return dates_sorted



def get_tables():
    return tables










def get_club_info_weapon_buli_region(club):
    club_all = results_team[results_team['guest_team_short'] == club]
    elements = list(set(list(club_all['guest_team'].values)))
    if len(elements) == 1:
        club_pd = club_all[club_all['guest_team'] == elements[0]].iloc[0]
        info = take_info(club_pd)
        return info
    else:
        infos = []
        for clubAB in elements:
            club_pd = club_all[club_all['guest_team'] == clubAB].iloc[0]
            infos.append(take_info(club_pd))
        return infos


def take_info(club_pd):
    info = {'club': club_pd['guest_team'],
            'buli': club_pd['league'].split(' ')[0],
            'region': club_pd['league'].split(' ')[1],
            'weapon': club_pd['weapon']
            }
    return info














by_first_name = defaultdict(set)
by_last_name = defaultdict(set)
by_plz = defaultdict(set)
by_city = defaultdict(set)
result_by_district_id = dict()
by_district_id = dict()
by_uuid = dict()
by_party = defaultdict(set)

state_lists = defaultdict(lambda: defaultdict(list))
party_candidates = defaultdict(list)
party_candidates_grouped = defaultdict(dict)

for result in election17_dict:
    result_by_district_id[result['district_id']] = result

for candidate in candidate_list:
    by_first_name[candidate['first_name']].add(candidate['uuid'])
    by_last_name[candidate['last_name']].add(candidate['uuid'])

    if candidate.get('list_nr') is not None:
        state_lists[candidate['list_name']][candidate['party']].append(candidate)

    party_candidates[candidate['party']].append(candidate)

    by_uuid[candidate['uuid']] = candidate

for district in district_list:
    for plz in district['plz']:
        by_plz[plz].add(district['uuid'])

    by_district_id[district['district_id']] = district

    for city in district['cities']:
        by_city[city].add(district['uuid'])

    by_uuid[district['uuid']] = district

for party in party_list:
    by_party[party['party']] = party

for state in state_lists.values():
    for party in state.keys():
        state[party] = list(sorted(state[party], key=operator.itemgetter('list_nr')))

for party in party_candidates.keys():
    party_candidates[party] = list(sorted(
        party_candidates[party],
        key=lambda c: (c['last_name'].lower(), c['first_name'].lower(), c['uuid'])))

for party, candidates in party_candidates.items():
    '''
    party_candidates_grouped[party] = {
        k: list(v)
        for k, v in groupby(candidates, key=(lambda x: x['last_name'][0].upper()))
    }
    '''
    frm = None
    lst = list()

    chunk_size = max(int(len(candidates) / 11) + 1, 4)
    grouped = groupby(candidates, key=(lambda x: x['last_name'][0].upper()))
    num_groups = len(list(grouped))
    grouped = groupby(candidates, key=(lambda x: x['last_name'][0].upper()))  # don't remove!

    for i, (k, v) in enumerate(grouped):
        if not frm:
            frm = k

        lst.extend(v)
        to = k

        if len(lst) >= chunk_size or num_groups - 1 == i:
            party_candidates_grouped[party]['%s - %s' % (frm, to)] = lst
            frm = None
            lst = list()


def random_candidate():
    return random.choice(candidate_list)

def get_digital_words():
    return digital_word_list

def get_election13_dict():
    return election13_dict

def find_party(party_wanted):
    return by_party.get(party_wanted)

def get_structural_data(str_nr):
    #district nr as str
    data = structural_data_district.loc[structural_data_district['Wahlkreis-Nr.'] == int(str_nr)]
    struct = {}
    struct['u18'] = list(data['Alter von ... bis ... Jahren am 31.12.2015 - unter 18 (%)'])[0],
    struct['a1824'] = list(data['Alter von ... bis ... Jahren am 31.12.2015 - 18-24 (%)'])[0],
    struct['a2534'] = list(data['Alter von ... bis ... Jahren am 31.12.2015 - 25-34 (%)'])[0],
    struct['a3559'] = list(data['Alter von ... bis ... Jahren am 31.12.2015 - 35-59 (%)'])[0],
    struct['a6075'] = list(data['Alter von ... bis ... Jahren am 31.12.2015 - 60-74 (%)'])[0],
    struct['a75'] = list(data['Alter von ... bis ... Jahren am 31.12.2015 - 75 und mehr (%)'])[0],
    struct['perm2'] = \
    list(data['Bevölkerung am 31.12.2015 - Insgesamt (in 1000)'] * 1000 / data['Fläche am 31.12.2015 (km²)'])[0],
    struct['voters_tot'] = list(1000 * data['Bevölkerung am 31.12.2015 - Insgesamt (in 1000)'] * (
    1 - (data['Alter von ... bis ... Jahren am 31.12.2015 - unter 18 (%)'] / 100)) * (
                                1 - (data['Bevölkerung am 31.12.2015 - Ausländer (%)'] / 100)))[0],
    struct['unemployed'] = list(data['Arbeitslosenquote März 2017 - insgesamt'])[0],
    struct['population'] = list(data['Bevölkerung am 31.12.2015 - Insgesamt (in 1000)'] * 1000)[0],
    new = {}
    for key, value in struct.items():
        new[key] = list(struct[key])[0]
    new['voters'] = new['voters_tot'] / new['population'] * 100
    return new



def find_candidates(first_name, last_name):
    """Returns a list of candidates that have the given first and last name"""
    out = by_first_name[first_name] & by_last_name[last_name]
    if not out:
        last_name_matches = by_last_name[last_name]
        first_name_matches = by_first_name[first_name]

        if (len(last_name_matches) + len(first_name_matches)) <5:
            out =  first_name_matches | last_name_matches
        else:
            if 0 < len(last_name_matches) < len(first_name_matches) or not first_name_matches:
                out = last_name_matches
            else:
                out = first_name_matches

    return [by_uuid[uuid] for uuid in out]

MANIFESTO_DIR = Path(__file__).absolute().parent.parent/'output'

manifesto_file = MANIFESTO_DIR/'all.json'

all_words_list = json.load(open(str(manifesto_file)))['data']
all_words = {word['word']: word for word in all_words_list}
random_words_list = [
    word['word']
    for word in all_words_list
    if word['word'][0].isupper() and word['count'] > 10
]

party_abbr = {
    'cdu': 'CDU',
    'spd': 'SPD',
    'fdp': 'FDP',
    'linke': 'DIE LINKE',
    'gruene': 'GRÜNE',
    'afd': 'AfD',
}

party_rev = {v: k for k, v in party_abbr.items()}

manifestos = dict()

for party in party_abbr:
    with open(str(MANIFESTO_DIR/('%s.txt' % party))) as fp:
        manifestos[party] = [line.strip() for line in fp.readlines()]
