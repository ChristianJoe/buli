import logging
import operator

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import by_uuid, get_dates, get_results_team, get_results_shooter, get_club_info_weapon_buli_region
import datetime
from backend.models import FacebookUser



def next_event_payload_to_api(event,**kwargs):
    parameters = {'clubs': None,
                  'date': None,
                  'league': '1.BuLi',
                  'weapon': None,
                  'region': None
                  }

    dates_api(event,parameters)


def dates_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')
    date = parameters.get('date')
    league = parameters.get('league')
    weapon = parameters.get('weapon')
    region = parameters.get('region')

    if not weapon:
        try:
            if not weapon:
                if FacebookUser.objects.get(uid=sender_id).rifle:
                    weapon = 'LG'
                elif FacebookUser.objects.get(uid=sender_id).pistole:
                    weapon = 'LP'
        except:
            weapon = None



    if club:
        next_event(event,{'next_event':club})
    elif league and weapon and region:
        next_event_league(event, {'next_event_league': {'buli': league,
                                                            'region': region,
                                                            'weapon': weapon}} )
    elif region and weapon:
        if region in ['West', 'Ost', 'Südwest']:
            league = '2.BuLi'
            next_event_league(event, {'next_event_league': {'buli': league,
                                                                'region': region,
                                                                'weapon': weapon}})
        else:
            send_text(sender_id, 'Mhmm. 1.BuLi oder 2. BuLi? Oder hast du einen Verein nachdem ich gucken soll?',
                      [quick_reply('1. Bundesliga', {'next_event_league':{'buli': '1.BuLi',
                                                                'region': region,
                                                                'weapon': weapon}
                                               }
                                   ),
                       quick_reply('2. Bundesliga', {'next_event_league': {'buli': '2.BuLi',
                                                                   'region': region,
                                                                   'weapon': weapon}
                                               }
                                   ),
                      ])
    elif league and region:
        if region in ['West', 'Ost', 'Südwest']:
            league = '2.BuLi'
        send_text(sender_id, 'LG oder eher LP??',
                        [quick_reply('LG', {'next_event_league': {'buli': league,
                                                               'region': region,
                                                               'weapon': 'LG'}
                                                       }
                                     ),
                         quick_reply('LP', {'next_event_league': {'buli': league,
                                                               'region': region,
                                                               'weapon': 'LP'}
                                                       }
                                     ),
                         quick_reply('Immer LG/LP', ['subscribe']

                                     ),
                         ]
                                  )
    elif league and weapon:
        quick = []
        if league in '2.BuLi':
            regions = ['West','Nord','Ost','Süd','Südwest']
        else:
            regions = ['Nord','Süd']
        for region in regions:
            quick.append(quick_reply(region, {'next_event_league': {'buli': league,
                                                        'region': region,
                                                        'weapon': weapon}
                                  }))

        send_text(sender_id,
                  'Choose wisely!',
                  quick_replies=quick
                  )
    elif league:
        if league == "1.BuLi":
            send_text(sender_id,'Gewehr oder Pistole? Nord oder Süd? ')
        else:
            send_text(sender_id,'Gewehr oder Pistole? Nord? Süd? West? Ost? Südwest?')
    else:
        send_text(sender_id,'Die nächsten Begegnungen in welcher Liga respektive welches Vereins interessieren dich?')



def next_event_league(event,payload,**kwargs):
    sender_id = event['sender']['id']
    info = payload['next_event_league']
    offset = payload.get('offset',0)
    buli = info['buli']
    region = info['region']
    weapon = info['weapon']
    we_long = {'LG': 'Luftgewehr',
               'LP': 'Luftpistole'
               }


    dates = get_results_team()

    dates = dates.sort_values(['date', 'time'])
    now = datetime.date.today()
    events = dates[(dates['league'] == buli + ' ' + region) &
                   (dates['weapon'] == we_long[weapon])]
    events = events[events['date'] >= now]


    num_league = 4
    if events.shape[0] - (offset + num_league) == 1:
        num_league = 3
    if events.shape[0] - (offset + num_league) < 1:
        num_league = 4 + (events.shape[0] - (offset + num_league))
    elements = []
    for index in range(offset, offset + num_league):
        data = events.iloc[index]
        list_text = "{today} {home} - {guest}".format(
            home = data['home_team'],
            guest = data['guest_team'],
            today = "**HEUTE**" if data['date'].date() == now else ''
        )
        sbtl = "{date}, {time}, Ausrichter: {host}".format(
            date = data['date'].strftime("%d.%m.%Y"),
            time = data['time'],
            host = data['host']
        )
        elements.append(
            list_element(
                title = list_text,
                subtitle=sbtl,
                #buttons=[button_postback("Ausrichter {club}".format(club=data['host']),
                #                         {'next_event': data['host'],
                #                          'host': True
                #                          }
                #                         )
                #         ]
                buttons = [button_postback('Team-Vergleich',
                                           {'club_comparison': {'club': data['home_team'],
                                                               'club1': data['guest_team']}
                                            }
                                            )
                        ]
                #
                # image_url=candidate.get('img') or None
            )
        )

    if events.shape[0] - offset > num_league:
        button = button_postback("Weiter Termine",
                                 {'next_event_league': info,
                                  'offset': offset + num_league})
    else:
        button = button_postback("Tabelle {liga}".format(liga=buli+' '+region),
                                 {'table_league':{'buli': buli,
                                                'region': region,
                                                'weapon': weapon}
                                  }
                                 )

    if offset == 0:
        reply = 'Hier die nächsten Begegnungen in der {weapon} {buli} {region}'.format(
                                                            buli=buli,
                                                        region=region,
                                                        weapon=weapon
                                                        )
        send_text(sender_id, reply)

    send_list(sender_id, elements, button=button)






def next_event(event,payload,**kwargs):
    sender_id = event['sender']['id']
    club = payload['next_event']
    host = payload.get('host', False)
    offset = payload.get('offset',0)

    dates = get_results_team()

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
        list_text = "{today}{home} - {guest}".format(
            home = data['home_team'],
            guest = data['guest_team'],
            today="**HEUTE** " if data['date'].date() == now else ''
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
                buttons=[button_postback('Team-Vergleich',
                                           {'club_comparison': {'club': data['home_team'],
                                                               'club1': data['guest_team']}
                                            }
                                            )
                         ]
                # image_url=candidate.get('img') or None
            )
        )
    if events.shape[0] - offset > num_league:
        if not host:
            button = button_postback("Nächsten Termine",
                                     {'next_event': club,
                                      'offset': offset + num_league})
        else:
            button = button_postback("Weiter Begegnungen",
                                     {'next_event': club,
                                      'offset': offset+num_league,
                                      'host': True
                                     })
    else:
        if not host:
            button = button_postback("Ausrichter {club}".format(club=club), {'next_event': club,
                                                                         'host': True})
        else:
            button = button_postback('Ergebnisse {club}'.format(club=club), {'results_club': club})


    if offset == 0:
        if not host:
            reply = 'Dann schauen wir mal wann {club} wieder an den Start geht!'.format(club=club)
            send_buttons(sender_id,
                         reply,
                         [button_postback("Ausrichter {club}".format(club=club), {'next_event': club,
                                                                                 'host': True})]
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