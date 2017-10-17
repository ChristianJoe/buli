import logging
import operator
import pandas as pd

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import by_uuid, get_dates, get_results_team, get_results_shooter, get_tables
from .parser import get_meyton, get_meyton_results
import datetime

#enable logging
logger = logging.getLogger(__name__)




def table_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    buli = parameters.get('league') # first or second BuLi
    region =  parameters.get('region')
    weapon = parameters.get('weapon')

    payloads = {'buli': buli,
               'region': region,
               'weapon': weapon}

    table_payload(event,{'table_payload': payloads})


def table_payload(event,payload,*kwarks):
    sender_id = event['sender']['id']
    payloads = payload['table_payload']

    try:
        buli = payloads['buli']
    except:
        buli = ''
    try:
        region = payloads['region']
    except:
        region = ''
    try:
        weapon = payloads['weapon']
    except:
        weapon =  ''


    if region in ['West','Ost','Südwest']:
        buli = '2.BuLi'



    if buli and region and weapon:
        table_league(event,{'table_league': payloads})
    elif buli and region:
        payloadsLG = {'buli': buli,
                       'region': region,
                       'weapon': "LG"}
        payloadsLP = {'buli': buli,
                       'region': region,
                       'weapon': "LP"}

        send_buttons(sender_id,
                     'Triff eine wahl',
                     [button_postback('Luftgewehr',
                                      {'table_payload': payloadsLG}),
                      button_postback('Luftpistole',
                                      {'table_payload': payloadsLP}
                     )
                      ]
                     )
    elif buli:
        if buli == "1.BuLi":
            payload_north = {'buli': '1.BuLi',
                            'region': 'Nord',
                            'weapon': weapon}
            payload_south = {'buli': '1.BuLi',
                            'region': 'Süd',
                            'weapon': weapon}
            send_text(sender_id,
                      'Nord oder Süd',
                      quick_replies = [
                          quick_reply('Nord', payload_north),
                          quick_reply('Süd', payload_south)

                      ]
                      )
        else:
          table_second_league(event,['table_second_league'])
    else:#nothing given
        options = []
        for key in [ 'LG BuLi Nord', 'LG BuLi Süd', 'LP BuLi Nord', 'LP BuLi Süd' ]:
            payloads = {'buli': '1.BuLi',
                       'region': key.split(' ')[2],
                       'weapon': key.split(' ')[0]}
            options.append(
                quick_reply(key, {'table_league': payloads})
            )
        options.append(
                quick_reply('2.Buli', ['table_second_league'])
            )
        send_text(sender_id, 'Welche Liga?' , quick_replies = options)





def table_second_league(event,payload,**kwargs):
    #choosing second league
    sender_id = event['sender']['id']
    competitons = {
                   "2.BuLi Süd": 'Süd' ,
                   "2.BuLi Nord": 'Nord',
                   "2.BuLi West": 'West',
                   "2.BuLi Ost": 'Ost',
                   "2.BuLi Südwest": 'Südwest'
                   }

    options = []

    for  element, key in competitons.items():
        payloads = {'buli': "2.BuLi",
                    'region': key}


        options.append(
            quick_reply(key,{'table_payload': payloads })
        )


    send_text(sender_id,'Such dir eine Liga aus.', quick_replies = options)










def table_league(event,payload,**kwargs):
    sender_id = event['sender']['id']
    payloads = payload['table_league']

    offset = int(payload.get('offset', 0))
    buli = payloads['buli']
    region = payloads['region']
    weapon = payloads['weapon']

    if weapon == 'Luftgewehr':
        weapon = 'LG'
    elif weapon == 'Luftpistole':
        weapon = 'LP'

    id = weapon + buli + ' ' + region

    tables = get_tables()
    table_league = tables[tables['id']== id]

    logger.info('Ergebnisliste: {id}'.format(
        id=id))

    num_league = 4

    if table_league.shape[0] - (offset + num_league) == 1:
        num_league = 3
    elements = []
    for index in range(offset, offset + num_league):
        data = table_league.iloc[index]
        payload_button = payloads
        payload_button['club'] = data['club']
        elements.append(
            list_element(
                '{rank}. {club} '.format(
                    rank=data['rank'],
                    club=data['club']
                ),
                subtitle="TEAM   %d : %d    EINZEL   %d : %d" % (
                 data['team_won'], data['team_lost'],data['single_won'], data['single_lost'],),
                buttons=[button_postback("Wettkämpfe",  {'club_list_competitions': payload_button})]
                # image_url=candidate.get('img') or None
            )
        )

    if table_league.shape[0] - offset > num_league:
        button = button_postback("Plätze %d - %d" %(offset+num_league+1, (offset+2*num_league)),
                                 {'table_league': payloads,
                                  'offset': offset + num_league})
    else:
        button = button_postback("Andere Liga", {'table_league': {'weapon': 'LG'} })

    if offset == 0:
        send_text(sender_id, '{buli} {weapon}. Gruppe {region}'.format(
            buli=buli,
            weapon=weapon,
            region=region
                    )
                  )
    send_list(sender_id, elements, button=button)






def club_list_competitions(event,payload,**kwargs):
    sender_id = event['sender']['id']
    info = payload['club_list_competitions']
    offset = int(payload.get('offset', 0))

    weapon = info['weapon']
    club = info['club']
    league = info['buli'] +' '+ info['region']

    if weapon == "LP":
        abbrv_weapon = "Luftpistole"
    else:
        abbrv_weapon = "Luftgewehr"


    results = get_results_team()

    results_league = results[(results['league'] == league) & (results['weapon'] == abbrv_weapon)]
    results_club = results_league[(results_league['guest_team'] == club) | (results_league['home_team'] == club)]


    num_league = 4

    if results_club.shape[0] - (offset + num_league) == 1:
        num_league = 3
    elements = []
    for index in range(offset, offset + num_league):
        data = results_club.iloc[index]
        info_dict = {'home_team': data['home_team'],
                     'guest_team': data['guest_team'],
                     'comp_id' : data['comp_id']
                     }
        if data['home_points'] + data['guest_points'] != 0:
            sbtle = "%d : %d --  %d : %d" % (data['home_points'], data['guest_points'],
                                             data['home_result'], data['guest_result'])
            button_comp = [button_postback("Einzelergebnisse", {'competition_results': info_dict})]
        else:
            date = data['date'].strftime("%d.%m.%Y")
            sbtle = date+', '+ data['time'] + ' - Ausrichter: ' + data['host']
            club_oponent = data['guest_team']
            if club_oponent == club:
                club_oponent = data['home_team']
            button_comp = [button_postback('Info Gegner', {'club_info': club_oponent})]

        elements.append(
            list_element(
                '#{index} - {home} : {guest} '.format(
                    index = index,
                    home=data['home_team'],
                    guest=data['guest_team']
                ),
                subtitle=sbtle,
                buttons=button_comp
                # image_url=candidate.get('img') or None
            )
        )


    if results_club.shape[0] - offset > num_league:
        button = button_postback("Wettkämpfe %d - %d" %(offset+num_league+1, (offset+2*num_league)),
                                {'club_list_competitions': info,
                                  'offset': offset + num_league})
    else:
        button = button_postback("von vorn", ['table_second_league'])

    if offset == 0:
        send_text(sender_id, 'Wettkampfübersicht {club}'.format(
            club=club
                    )
                  )
    send_list(sender_id, elements, button=button)





def competition_results(event,payload,**kwargs):
    sender_id = event['sender']['id']
    data = payload['competition_results']

    info_dict = {'home_team': data['home_team'],
                 'guest_team': data['guest_team'],
                 'comp_id': data['comp_id']
                 }



    send_text(sender_id, 'deine info zur competition {home} gegen {guest} kommt bald'.format(
        home = data['home_team'],
        guest = data['guest_team']
    ))



def results_api(event, parameters, **kwargs):
    club = parameters.get('clubs')

    if club:
        results_club(event, {'results_club': club})




def results_club(event, payload, **kwargs):
    sender_id = event['sender']['id']
    club = payload['club']

    send_text(sender_id, 'hier das Ergebnise von '+club)



def shooter_results_api(event, parameters, **kwargs):
    first_name = parameters.get('first_name')
    last_name = parameters.get('last_name')
    club = parameters.get('club')

    payload = {'first_name': first_name,
               'last_name': last_name,
               'club' : club
               }

    shooter_results(event,payload,**kwargs)


def shooter_results(event,payload,**kwargs):
    sender_id = event['sender']['id']
    offset = int(payload.get('offset', 0))

    try:
        first_name = payload['first_name']
    except:
        first_name = None
    try:
        last_name = payload['last_name']
    except:
        last_name = None
    try:
        club = payload['club']
    except:
        club = None

    if not first_name and not last_name and club:
        club_list_competitions(event,{'club':club})
        return

    shooter = get_results_shooter()

    if last_name:
        data_last = shooter[shooter['last_name'] == last_name]
        check_unique_last_name = list(set(list(data_last['first_name'])))
        if len(check_unique_last_name) == 1:
            workdata = data_last

    if first_name:
        data_first = shooter[shooter['first_name'] == first_name]
        check_unique_first_name = list(set(list(data_first['last_name'])))
        if len(check_unique_first_name) == 1:
            workdata = data_first
        else:
            data_first_last = data_first[data_first['last_name'] == last_name]
            check_unique_last_name = list(set(list(data_first_last['first_name'])))
            if len(check_unique_last_name) == 1:
                workdata = data_first_last

    data_club = pd.DataFrame()

    if club and last_name:
        if len(check_unique_last_name) != 0:
            data_club = data_last[data_last['team_full'] == club]
    elif club and first_name:
        if len(check_unique_first_name) != 0:
            data_club = data_first[data_first['team_full'] == club]

    if not data_club.empty:
        check_unique_club = list(set(list(data_club['first_name'])))
        if len(check_unique_club) == 1:
            workdata = data_club
        else:
            send_text(sender_id,
                      'Mhmm, den Namen kenne ich noch nicht. Zumindest hat er noch keinen Wettkampf geschossen!')

    info_person = {first_name :  workdata['first_name'].iloc[0],
                    last_name :  workdata['last_name'].iloc[0]}
    club = workdata['team_full'].iloc[0]


    num_league = 4
    #if workdata.shape[0]<4:
    #    num_league = workdata.shape

    if workdata.shape[0] - (offset + num_league) == 1:
        num_league = 3
    elements = []
    for index in range(offset, offset + num_league):
        data = shooter[(shooter['comp_id'] == workdata['comp_id'].iloc[index]) & (
                        shooter['position'] == workdata['position'].iloc[index])]
        person = data[data['team_full'] == club]
        oponent = data[data['team_full']!= club]

        info_dict = {'first_name': oponent['first_name'].iloc[0],
                     'last_name': oponent['last_name'].iloc[0],
                     'club': oponent['team_full'].iloc[0]
                     }
        sbtle = "Position {position}".format(position = person['position'].iloc[0])
        if person['shoot_off'].iloc[0]:
            sbtle += "Entscheidung im Stechen: {person}:{oponent}".format(
                person = person['shoot_off'].iloc[0],
                oponent = oponent['shoot_off'].iloc[0]
            )

        button_comp = [button_postback("Info {first_name} {last_name}".format(
                first_name = oponent['first_name'].iloc[0],
                last_name = oponent['last_name'].iloc[0]
            ), {'shooter_results': info_dict})]


        elements.append(
            list_element(
                "%d : %d --  %s %s" % (person['result'].iloc[0], oponent['result'].iloc[0],
                                       oponent['first_name'].iloc[0], oponent['last_name'].iloc[0]),
                subtitle=sbtle,
                buttons=button_comp
                # image_url=candidate.get('img') or None
            )
        )

    if workdata.shape[0] - offset > num_league:
        button = button_postback("Wettkämpfe %d - %d" % (offset + num_league + 1, (offset + 2 * num_league)),
                                 {'shooter_results': info_person,
                                  'offset': offset + num_league})
    else:
        button = button_postback(club, {'club_info': club})

    if offset == 0:
        text_first_response = '{first_name} {last_name}'.format(
            first_name = workdata['first_name'].iloc[0],
            last_name = workdata['last_name'].iloc[0]
        )
        send_text(sender_id, text_first_response

                  )
    send_list(sender_id, elements, button=button)






#################################
def buli_live_api(event, parameters, **kwargs):

    buli_live(event)


######################################
def buli_live(event,**kwargs):
    sender_id = event['sender']['id']

    links = get_meyton(hrefs = True)
    options = [quick_reply('Aktualisieren', ['buli_live'])]

    for key, href in links.items():

        live = get_meyton_results(href)

        try:
            if not live.empty:
                #calculate points
                data = live['points'].dropna()
                home_points = 0
                guest_points = 0
                for row in data.iteritems():
                    home_points += int(list(row)[1].split(':')[0].strip())
                    guest_points += int(list(row)[1].split(':')[1].strip())

                reply_positions = ""
                for index in range(0, 5):
                    reply_positions += '#{position}:   {points_home}  :  {points_guest}  \n'.format(
                        position=str(index + 1),
                        points_home=live['result'].iloc[(2 * index)],
                        points_guest=live['result'].iloc[(2 * index + 1)]
                    )  # ,

                reply_overview = "{fight}\n{home} : {guest}\n{home_points}:{guest_points}".format(
                            fight = live['fight'].iloc[0],
                              home = live['home_team'].iloc[0],
                              guest = live['guest_team'].iloc[0],
                              home_points = home_points,
                              guest_points = guest_points
                        )



                send_text(sender_id, reply_overview+'\n'+ reply_positions
                       )


                reply_shooters = ""
                for index in range(0, 5):
                    reply_shooters += '#{position}: {home} : {guest}\n'.format(
                        position=str(index + 1),
                        home=live['name'].iloc[(2 * index)],

                        guest=live['name'].iloc[(2 * index + 1)],

                    )

                payload_reply = {'reply_shooters': reply_shooters,
                                'reply_positions': reply_positions,
                                'href': href}

                quickreplyname = live['home_team'].iloc[0] + ':' + live['guest_team'].iloc[0]

                options.append(
                        quick_reply(quickreplyname, {'buli_live_competition': payload_reply})
                    )

        except:
            send_text(sender_id,'Zur Zeit kein Wettkampf')


    send_text(sender_id,'Aktualisieren. Oder schau dir die Schützen im Detail an.', quick_replies = options)





def buli_live_competition(event,payload,**kwargs):
    sender_id = event['sender']['id']
    payload_reply = payload['buli_live_competition']


    send_text(sender_id,
                  payload_reply['reply_shooters'],
                  quick_replies = [quick_reply('Aktualisieren', ['buli_live'])
               ]
                  )


def shooter_live(event,payload,**kwargs):
    sender_id = event['sender']['id']
    payload_reply = payload['shooter_live']



    send_text(sender_id,
             payload_reply['reply_shooters'],
              quick_replies=[quick_reply('Aktualisieren',['buli_live'])]
              )
