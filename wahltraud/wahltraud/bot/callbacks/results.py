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

    payload = {'buli': buli,
               'region': region,
               'weapon': weapon}


    if buli and region and weapon:
        table_league(event,{'table_league': payload})
    else:#nothing given
        options = []
        for key in [ 'BuLi Nord', 'BuLi Süd' ]:
            payload = {'buli': '1.BuLi',
                       'region': key.split(' ')[1],
                       'weapon': 'LG'}
            options.append(
                quick_reply(key, {'table_league': payload})
            )
        options.append(
                quick_reply('2.Buli', ['table_second_league'])
            )
        send_text(sender_id, 'Welche Liga?' , quick_replies = options)





def table_second_league(event,**kwargs):
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
        options.append(
            quick_reply(key,{'table_league': element})
        )


    send_text(sender_id,'Such dir eine Liga aus.', quick_replies = options)










def table_league(event,payload,**kwargs):
    sender_id = event['sender']['id']
    payloads = payload['table_league']

    offset = int(payload.get('offset', 0))
    buli = payloads['buli']
    region = payloads['region']
    weapon = payloads['weapon']

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
                '#{rank} {club} '.format(
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
        button = button_postback("Andere Liga", {'table_league': payloads})

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
        if data['home_points'] + data['guest_points'] != 0:
            sbtle = "%d : %d  " % (data['home_points'], data['guest_points'])
            button_comp = [button_postback("Einzelergebnisse", {'competition_results': data})]
        else:
            sbtle = data['time'] + ' Ausrichter ' + data['host']
            button_comp = [button_postback('Info Gegner', ['info_club'])]

        elements.append(
            list_element(
                '{home} : {guest} '.format(
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
    first_name = payload['first_name']
    last_name = payload['last_name']
    club = payload['club']

    results = get_results_shooter()

    if not club:
        if not first_name:
            send_text(sender_id,'Hier Ergebnisse zu_'+ last_name+'.')
        elif not last_name:
            send_text(sender_id, 'Hier Ergebnisse zu ' + first_name+'.')
        else:
            data = results[(results['last_name'] == last_name) & (results['first_name'] == first_name)]

            send_text(sender_id, 'Hier Ergebnisse von {first_name} {last_name}: {points} ' .format(
                first_name = first_name,
                last_name =  last_name,
                points = data['result'].iloc[0]
            )
                      )

    elif not first_name:
        if not last_name:
            send_text(sender_id, 'Hier Ergebnisse zu ' + club+'.')
        else:
            send_text(sender_id, 'Hier Ergebnisse zu ' + last_name + ' vom ' + club+'.')
    else:
        send_text(sender_id, 'Hier Ergebnisse von '+first_name+' '+last_name+' vom '+ club+'.')



def buli_live_api(event, parameters, **kwargs):

    buli_live(event)



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
