import logging
import operator

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
#from ..data import by_uuid



def dates_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')

    if not club:
        send_text(sender_id, 'Der nächste Wettkampf findet am 14.10. statt.')
    else:
        send_text(sender_id, 'Der nächste Wettkampf bei '+club)

