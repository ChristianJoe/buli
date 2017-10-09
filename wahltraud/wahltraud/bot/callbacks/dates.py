import logging
import operator

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import by_uuid, get_dates
import datetime


def dates_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')


    next_event(event,{'club':club})



def next_event(event,payload):
    sender_id = event['sender']['id']
    club = payload['club']

    dates = get_dates()
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
        dates_club = dates[dates['club'] == club]

        text = club + ' ist Ausrichter folgender Wettkämpfe:'

        for i in range(0, dates_club.shape[0]):
            league = dates_club['league'].iloc[i]
            date = dates_club['date'].iloc[i].strftime("%d.%m.%Y")
            options.append(
                quick_reply(
                    date + ' ' + league,
                    {'comp_id': dates_club['id'].iloc[i]})
            )

    send_text(sender_id, text, quick_reply = options)


def competition_info(event, payload):
    sender_id = event['sender']['id']
    dates_id = payload['comp_id']

    send_text(sender_id, 'Hier gibt es Info über '+dates_id)