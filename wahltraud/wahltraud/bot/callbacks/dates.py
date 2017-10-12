import logging
import operator

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import by_uuid, get_dates, get_results_team, get_results_shooter
import datetime


def dates_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')


    next_event(event,{'club':club})



def next_event(event,payload,**kwargs):
    sender_id = event['sender']['id']
    club = payload['club']

    dates = get_results_team()
    options = []
    now = datetime.date.today()

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
                    {'comp_id': next_dates['id'].iloc[i]}
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
                    {'comp_id': dates_club['id'].iloc[i]})
            )

    send_text(sender_id, text, quick_replies = options)


def competition_info(event, payload, **kwargs):
    sender_id = event['sender']['id']
    comp_id = payload['comp_id']

    data = get_results_team()
    data_comp_id = data[data['comp_id']== comp_id]

    for row in data_comp_id.iterrows():

        send_text(sender_id, '{time}: {home} : {guest} '.format(
            time = data_comp_id['time'].iloc[0],
            home = data_comp_id['home_team'].iloc[0],
            guest = data_comp_id('guest_team').iloc[0]
        )
                  )