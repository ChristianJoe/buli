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
        elements.append(
            list_element(
                '#{rank} {club} '.format(
                    rank=data['rank'],
                    club=data['club']
                ),
                subtitle="%d : %d   %d : %d" % (
                data['single_won'], data['single_lost'], data['team_won'], data['team_lost']),
                buttons=[button_postback("Wettkämpfe", {'list_competitions': {'club_list_competitions': data['club']}})]
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


def club_list_cometitions(event,payload,**kwargs):
    sender_id = event['sender']['id']





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
