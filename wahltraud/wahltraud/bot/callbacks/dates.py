import logging
import operator

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
#from ..data import by_uuid
from datetime


def dates_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')

    if not club:
        send_text(sender_id, 'Der nächste Wettkampf findet am 14.10. statt.')
    else:
        next_event(event,{'club':club})



def next_event(event,payload):
    sender_id = event['sender']['id']
    club = payload['club']

    dates = get_dates()
    now = datetime.date.today()
    for i in range(0, 100):
        look_up_date = now + datetime.timedelta(days=i)
        next_dates = dates[dates['date'] == look_up_date]
        if not next_dates.empty:
            break
    next_dates

    send_text(sender_id, 'Der nächste Wettkampftag ist am {date}.'
              .format(
                        date = look_up_date
                    ))