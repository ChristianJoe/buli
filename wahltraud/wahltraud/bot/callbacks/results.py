import logging
import operator
import pandas as pd

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import by_uuid, get_dates, get_results_team, get_results_shooter, get_tables
from .parser import get_meyton, get_meyton_results
import datetime



def table_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    buli = parameters.get('league') # first or second BuLi
    region =  parameters.get('region')
    weapon = parameters.get('weapon')



    if buli and region and weapon:
        league = weapon+buli+' '+region
        table_league(event,{'table_league': league})
    else:
        competitons = { "1.BuLi Nord": 'BuLi Nord',
                        "1.BuLi Süd": 'BuLi Süd'
                        }
        options = []
        for element, key in competitons.items():
            options.append(
                quick_reply(key, {'table_league': element})
            )
        options.append(
                quick_reply('2.Buli', ['table_second_league'])
            )
        send_text(sender_id, 'Welche Liga?' , quick_replies = options)


def table_league(event,payload,**kwargs):
    sender_id = event['sender']['id']
    league = payload['table_league']

    tables = get_tables()
    table_league = tables[tables['id']== league]
    send_text(sender_id,'Hier Die Tabelle '+league)


    send_text(sender_id, '#1: TuS Hilgert')





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

    links = get_meyton()
    options = []
    for  key, href in links.items():
        options.append(
            quick_reply(key,{'buli_live_competition': href})
        )


    send_text(sender_id,'Live Ergebnisse folgender Ausrichter', quick_replies = options)



def buli_live_competition(event,payload,**kwargs):
    sender_id = event['sender']['id']
    href = payload['buli_live_competition']

    live = get_meyton_results(href)

    if live.empty:

        send_text(sender_id, live )

    else:
        send_text(sender_id,
                  '{fight}'
                {home} : {guest}'.format(
                    fight = live['fight'],
                      home = live['home_team'].iloc[0],
                      guest = live['guest_team'].iloc[0]
                )
                  )
        for index in range(0,5):

            send_text(sender_id,
                      '#{position}: {home}  {points_home}:{points_guest}  {guest}'.format(
                          position = str(index),
                          home = live['name'].iloc[(2*index)],
                          points_home = live['result'].iloc[(2*index)],
                          guest=live['name'].iloc[(2 * index+1)],
                          points_guest=live['result'].iloc[(2 * index+1)]
                      )
                      )

