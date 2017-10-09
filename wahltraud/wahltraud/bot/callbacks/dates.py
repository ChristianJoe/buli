import logging
import operator

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import by_uuid, get_dates
import datetime
import pandas as pd


def dates_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')


    next_event(event,{'club':club})



def next_event(event,payload):
    sender_id = event['sender']['id']
    club = payload['club']

    dates = get_dates()

    now = datetime.date.today()

    if not club:
        for i in range(0, 100):
            look_up_date = now + datetime.timedelta(days=i)
            next_dates = dates[dates['date'] == look_up_date]
            if not next_dates.empty:
                break


        text =  'Der nächste Wettkampftag ist am {date}.'.format(
                            date = look_up_date''
                        )
    else:
        dates_club = dates[dates['club'] == club]
        league = dates_club['league'].iloc[0]
        strdate = ''
        for i in range(0, dates_club.shape[0]):
            if i > 0:
                strdate += ' und am '
            strdate += dates_club['date'].iloc[i].strftime("%d.%m.%Y")
        text = club + 'ist Ausrichter der'+ league + ' am  ' + strdate + '.'

    send_text(sender_id, text)