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
            send_text(sender_id, 'Mhmm. 1.BuLi oder 2. BuLi? Oder hast du einen Verein nachdem ich gucken soll?')
    elif league and region:
        send_text(sender_id, 'LG oder eher LP??')
    elif league:
        if league == "1.BuLi":
            send_text(sender_id,'Nord? Süd?')
        else:
            send_text(sender_id,'Nord? Süd? West? Ost? Südwest?')
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


    dates = get_results_team()
    options = []
    now = datetime.date.today()

    send_text(sender_id, "Hier zeige ich dir demnächst das Event von {club} an, welches nach dem {date} stattfindet. (Feature in Entwicklung)".format(
        date=now.strftime("%d.%m.%Y"),
        club= club
    ))


    if not club:
        for i in range(0, 100):
            look_up_date = now + datetime.timedelta(days=i)
            next_dates = dates[dates['date'] == look_up_date]
            if not next_dates.empty:
                break


        text =  'Der nächste Wettkampftag ist am {date}.'.format(
                            date = look_up_date.strftime("%d.%m.%Y")
                        )
        # quick replies
        for i in range(0, next_dates.shape[0]):
            league =  next_dates['league'].iloc[i]
            options.append(
                quick_reply(
                    league,
                    {'comp_id': next_dates['comp_id'].iloc[i]}
                )
            )
    else:
        dates_club = dates[dates['host'] == club]

        text = club + ' ist Ausrichter folgender Wettkämpfe:'

        for i in range(0, dates_club.shape[0]):
            league = dates_club['league'].iloc[i]
            date = dates_club['date'].iloc[i].strftime("%d.%m.%Y")
            options.append(
                quick_reply(
                    date + ' ' + league,
                    {'comp_id': dates_club['comp_id'].iloc[i]})
            )

    send_text(sender_id, text, quick_replies = options)
    '''

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