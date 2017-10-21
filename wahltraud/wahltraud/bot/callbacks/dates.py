import logging
import operator

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import by_uuid, get_dates, get_results_team, get_results_shooter, get_club_info_weapon_buli_region
import datetime


def dates_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')
    date = parameters.get('date')
    league = parameters.get('league')
    weapon = parameters.get('weapon')
    region = parameters.get('region')

    if club:
        next_event(event,{'next_event':club})
    elif league and weapon and region:
        next_event_league(sender_id, {'next_event_league': {'buli': league,
                                                            'region': region,
                                                            'weapon': weapon}} )
    elif region and weapon:
        if region in ['West', 'Ost', 'Südwest']:
            league = '2.BuLi'
            next_event_league(sender_id, {'next_event_league': {'buli': league,
                                                                'region': region,
                                                                'weapon': weapon}})
        else:
            send_text(sender_id, 'Mhmm. 1.BuLi oder 2. BuLi? Oder hast du einen Verein nachdem ich gucken soll?',
                      [quick_reply('1. Bundesliga', {next_event_league:{'buli': '1.BuLi',
                                                                'region': region,
                                                                'weapon': weapon}
                                               }
                                   ),
                       quick_reply('2. Bundesliga', {next_event_league: {'buli': '2.BuLi',
                                                                   'region': region,
                                                                   'weapon': weapon}
                                               }
                                   ),
                      ])
    elif league and region:
        send_text(sender_id, 'LG oder eher LP??',
                        [quick_reply('LG', {next_event_league: {'buli': league,
                                                                           'region': region,
                                                                           'weapon': "LG"}
                                                       }
                                     ),
                         quick_reply('LP', {next_event_league: {'buli': league,
                                                                           'region': region,
                                                                           'weapon': "LP"}
                                                       }
                                     ),
                         ]
                                  )
    elif league:
        if league == "1.BuLi":
            send_text(sender_id,'Gewehr oder Pistole? Nord oder Süd? ')
        else:
            send_text(sender_id,'Gewehr oder Pistole? Nord? Süd? West? Ost? Südwest?')
    else:
        send_text(sender_id,'Welcher Verein, oder welche Liga interessiert dich?')



def next_event_league(event,payload,**kwargs):
    sender_id = event['sender']['id']
    info = payload['next_event_league']

    dates = get_results_team()


    send_text(sender_id, 'hier info zur liga')



def next_event(event,payload,**kwargs):
    sender_id = event['sender']['id']
    club = payload['next_event']
    host = payload.get('host', False)
    offset = payload.get('offset',0)

    dates = get_results_team()
    now = datetime.date.today()

    dates = dates.sort_values(['date', 'time'])
    now = datetime.date.today()
    if not host:
        events = dates[(dates['guest_team'] == club) |
                       (dates['guest_team_short'] == club) |
                       (dates['home_team'] == club) |
                       (dates['home_team_short'] == club)]
        events = events[events['date'] >= now]
    else:
        events = dates[dates['host'] == club]



    num_league = 4
    if events.shape[0] - (offset + num_league) == 1:
        num_league = 3
    if events.shape[0] - (offset + num_league) < 1:
        num_league = 4 + (events.shape[0] - (offset + num_league))
    elements = []
    for index in range(offset, offset + num_league):
        data = events.iloc[index]
        list_text = "{home} - {guest}".format(
            home = data['home_team'],
            guest = data['guest_team']
        )
        sbtl = "{date}, {time}, Ausrichter: {host}".format(
            date = data['date'].strftime("%d.%m.%Y"),
            time = data['time'],
            host = data['host']
        )
        elements.append(
            list_element(
                list_text,
                subtitle=sbtl,
                buttons=[button_postback("Ausrichter {club}".format(club=data['guest_team']),
                                         {'next_event': data['guest_team'],
                                          'host': True
                                          }
                                         )
                         ]
                # image_url=candidate.get('img') or None
            )
        )

    if events.shape[0] - offset > num_league:
        button = button_postback("Nächsten Termine",
                                 {'next_event': club,
                                  'offset': offset + num_league})
    else:
        button = button_postback("Ausrichter {club}".format(club=club), {'next_event': club,
                                                                         'host': True})

    if offset == 0:
        if not host:
            reply = 'Dann schauen wir mal wann {club} wieder an den Start geht!'.format(club=club)
            send_buttons(sender_id,
                         reply,
                         button_postback("Ausrichter {club}".format(club=club), {'next_event': club,
                                                                                 'host': True})
                         )
        else:
            reply = '{club} ist Ausrichter für folgende Paarungen:'.format(club=club)
            send_text(sender_id, reply)

    send_list(sender_id, elements, button=button)











def competition_info(event, payload, **kwargs):
    sender_id = event['sender']['id']
    comp_id = payload['comp_id']

    data = get_results_team()
    data_comp_id = data[data['comp_id']== comp_id]

    for  index,row in enumerate(data_comp_id.iterrows()):

        send_text(sender_id, '{time}: {home} : {guest} '.format(
            time = row.time,
            home = row.home_team,
            guest = row.guest_team
        )
                  )