import logging
import operator
import pandas as pd

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import by_uuid, get_dates, get_results
import datetime





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
    sender_id = ['sender']['id']
    first_name = payload['first_name']
    last_name = payload['last_name']
    club = payload['club_name']

    results = get_results()

    if not club:
        if not first_name:
            send_text(sender_id,'Hier Ergebnisse zu_'+ last_name+'.')
        elif not last_name:
            send_text(sender_id, 'Hier Ergebnisse zu ' + first_name+'.')
        else:
            data = results[results['last_name'] == last_name and results['first_name']== 'first_name']
            points = data['result'].iloc[0]

            send_text(sender_id, 'Hier Ergebnisse zu ' + first_name + ' ' + last_name+':'+points)

    elif not first_name:
        if not last_name:
            send_text(sender_id, 'Hier Ergebnisse zu ' + club+'.')
        else:
            send_text(sender_id, 'Hier Ergebnisse zu ' + last_name + ' vom ' + club+'.')
    else:
        send_text(sender_id, 'Hier Ergebnisse von '+first_name+' '+last_name+' vom '+ club+'.')

