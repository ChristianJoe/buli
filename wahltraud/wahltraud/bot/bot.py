import logging
from threading import Thread
from time import sleep
import os
import json
import datetime

import schedule
#from django.utils.timezone import localtime, now
from apiai import ApiAI

from backend.models import Push, FacebookUser, Wiki
from .fb import send_text, send_buttons, button_postback, PAGE_TOKEN
from .handlers.payloadhandler import PayloadHandler
from .handlers.texthandler import TextHandler
from .handlers.apiaihandler import ApiAiHandler
from .callbacks.simple import (get_started, push, subscribe, unsubscribe, wiki, story,
                               apiai_fulfillment, about_manifesto, menue_manifesto, about,
                               questions,share_bot, push_step,  menue_data,
                               more_data, sunday_poll, greetings, who_votes,
                               update_api, infos_backend, table_start, competition_start, club_info, club_info_api,
                               letsgo,champions_api,champions_LG, champions_LP, former_champions_LG, former_champions_LP,
                               club_weapon_buli_region, subscribe_weapon, unsubscribe_weapon)
from .callbacks.shared import (get_pushes, get_breaking, send_push, schema)
from .callbacks import candidate, district, browse_lists, manifesto, party, dates, parser, results
from .data import by_district_id, reopen_data, meyton_update

# TODO: The idea is simple. When you send "subscribe" to the bot, the bot server would add a record according to the sender_id to their
# database or memory , then the bot server could set a timer to distribute the news messages to those sender_id who have subscribed for the news.

# Enable logging
logger = logging.getLogger(__name__)

logger.info('FB Wahltraud Logging')

API_AI_TOKEN = os.environ.get('WAHLTRAUD_API_AI_TOKEN', 'na')

ADMINS = [
    1642888035775604,  # Christian
]


def make_event_handler():
    ai = ApiAI(API_AI_TOKEN)

    handlers = [
        ApiAiHandler(greetings, 'hi'),
        PayloadHandler(greetings, ['gruss']),
        PayloadHandler(infos_backend,['infos_backend']),
        PayloadHandler(get_started, ['start']),
        PayloadHandler(about, ['about']),
        PayloadHandler(story, ['push_id', 'next_state']),
        PayloadHandler(get_started, ['wahltraud_start_payload']),
        PayloadHandler(share_bot, ['share_bot']),
        PayloadHandler(subscribe, ['subscribe']),
        PayloadHandler(subscribe_weapon,['subscribe_weapon']),
        PayloadHandler(unsubscribe_weapon, ['unsubscribe_weapon']),

        PayloadHandler(unsubscribe, ['unsubscribe']),
        ApiAiHandler(subscribe, 'anmelden'),
        ApiAiHandler(unsubscribe, 'abmelden'),
        PayloadHandler(push_step, ['push', 'next_state']),
        PayloadHandler(push, ['push']),
        ApiAiHandler(infos_backend, 'push'),
        ApiAiHandler(wiki, 'wiki'),
        ApiAiHandler(letsgo,'los gehts'),
        #PayloadHandler(questions, ['questions']),
        PayloadHandler(menue_data, ['menue_data']),
        PayloadHandler(more_data, ['more_data']),
        PayloadHandler(menue_manifesto, ['menue_manifesto']),
        PayloadHandler(about_manifesto, ['about_manifesto']),

        ApiAiHandler(dates.dates_api, 'next_event_club'),
        ApiAiHandler(dates.dates_api, 'next_event_context'),

        PayloadHandler(club_weapon_buli_region,['club_weapon_buli_region','payl']),
        ApiAiHandler(update_api, 'update'),
        PayloadHandler(parser.update_table_payload, ['update_table_payload']),
        PayloadHandler(parser.update_results, ['update_results']),
        PayloadHandler(parser.update_setlist_payload, ['update_setlist']),

        ApiAiHandler(club_info_api, 'club_info'),
        PayloadHandler(club_info,['club_info']),

        ApiAiHandler(results.results_api, 'results'),
        PayloadHandler(results.results_club,'results_club'),

        ApiAiHandler(results.shooter_results_api,'shooter_who_is'),
        PayloadHandler(results.shooter_results,['shooter_results']),

        PayloadHandler(dates.next_event_league, ['next_event_league']),

        PayloadHandler(dates.next_event, ['next_event']),
        PayloadHandler(dates.competition_info, ['comp_id']),
        PayloadHandler(results.blue_arrows,['blue_arrows']),
        ApiAiHandler(results.table_api,'table'),

        PayloadHandler(results.table_second_league, ['table_second_league']),
        PayloadHandler(results.table_league, ['table_league']),
        PayloadHandler(results.club_list_competitions, ['club_list_competitions']),
        PayloadHandler(results.competition_results, ['competition_results']),
        PayloadHandler(results.table_payload,['table_payload']),

        ApiAiHandler(results.setlist_api, 'setlist'),
        PayloadHandler(results.setlist_payload, ['setlist_payload']),

        PayloadHandler(table_start,['table_start']),
        PayloadHandler(competition_start,['competition_start']),

        ApiAiHandler(results.buli_live_api,'buli_live'),
        PayloadHandler(results.buli_live,['buli_live']),
        PayloadHandler(results.buli_live_competition,['buli_live_competition']),
        PayloadHandler(results.shooter_live,['shooter_live']),

        ApiAiHandler(champions_api, 'amtierender deutscher Meister'),
        #ApiAiHandler(chancelor, 'bundeskanzler'),
        #ApiAiHandler(candidate.basics, 'kandidat'),
        #ApiAiHandler(party.basics, 'parteien'),
        #ApiAiHandler(party.top_candidates_apiai, 'spitzenkandidat'),
        #ApiAiHandler(sunday_poll, 'umfrage'),
        PayloadHandler(champions_LG, ['champions_LG']),
        PayloadHandler(champions_LP, ['champions_LP']),
        PayloadHandler(former_champions_LG, ['former_champions_LG']),
        PayloadHandler(former_champions_LP,['former_champions_LP']),
        #PayloadHandler(party.show_list_all, ['show_list_all']),
        #PayloadHandler(party.show_top_candidates,['show_top_candidates']),
        #ApiAiHandler(candidate.candidate_check, 'kandidatencheck'),
        #PayloadHandler(candidate.candidate_check_start,['candidate_check_start']),
        #PayloadHandler(district.result_state_17,['result_state_17']),
        #PayloadHandler(district.select_state_result,['select_state_result']),
        #PayloadHandler(district.intro_district, ['intro_district']),
        #PayloadHandler(candidate.intro_candidate, ['intro_candidate']),
        #PayloadHandler(district.show_13, ['show_13']),
        #PayloadHandler(district.result_17, ['result_17']),
        #PayloadHandler(district.result_first_vote, ['result_first_vote']),
        #PayloadHandler(district.result_second_vote, ['result_second_vote']),
        #PayloadHandler(district.novi, ['novi']),
        #PayloadHandler(district.show_structural_data, ['show_structural_data']),
        #PayloadHandler(candidate.search_candidate_list, ['search_candidate_list']),
        #PayloadHandler(candidate.payload_basics, ['payload_basics']),
        #PayloadHandler(candidate.more_infos_nrw, ['more_infos_nrw']),
        #PayloadHandler(candidate.no_video_to_show, ['no_video_to_show']),
        #PayloadHandler(candidate.show_video, ['show_video']),
        #PayloadHandler(candidate.show_random_candidate, ['show_random_candidate']),
        #PayloadHandler(district.show_candidates, ['show_candidates']),
        #ApiAiHandler(district.find_district, 'wahlkreis_finder'),
        #PayloadHandler(district.show_district, ['show_district']),
        #ApiAiHandler(browse_lists.apiai, 'liste'),
        #PayloadHandler(browse_lists.intro_lists, ['intro_lists']),
        #PayloadHandler(browse_lists.select_state, ['select_state']),
        #PayloadHandler(browse_lists.select_party, ['select_party']),
        #PayloadHandler(browse_lists.show_list, ['show_list', 'state', 'party']),
        #PayloadHandler(manifesto.manifesto_start, ['manifesto_start']),
        #PayloadHandler(manifesto.show_word_payload, ['show_word']),
        #PayloadHandler(manifesto.show_sentence_payload, ['show_sentence']),
        #PayloadHandler(manifesto.show_paragraph, ['show_paragraph']),
        #PayloadHandler(manifesto.show_manifesto, ['show_manifesto']),
        #ApiAiHandler(manifesto.show_word_apiai, 'wahlprogramm'),
        TextHandler(apiai_fulfillment, '.*'),
    ]

    def event_handler(data):
        """handle all incoming messages"""
        messaging_events = data['entry'][0]['messaging']
        logger.debug(messaging_events)

        for event in messaging_events:
            referral = event.get('referral')

            if referral:
                ref = referral.get('ref')
                logging.info('Bot wurde mit bekantem User geteilt: ' + ref)
                if ref.startswith('WK'):
                    wk = int(ref.replace("WK", ""))
                    dis = by_district_id[str(wk)]
                    send_text(
                        event['sender']['id'],
                        'Hi, schön dich wieder zu sehen! \nNovi sagt, du möchtest etwas über deinen Wahlkreis "{wk}" wissen? Sehr gerne...'.format(
                            wk=dis['district']
                        )
                    )
                    district.send_district(event['sender']['id'], dis['uuid'])
                else:
                    send_text(
                        event['sender']['id'],
                        'Willkommen zurück. Was kann ich für dich tun?'
                    )

            message = event.get('message')

            if message:
                text = message.get('text')

                if (text is not None
                    and event.get('postback') is None
                    and message.get('quick_reply') is None):

                    request = ai.text_request()
                    request.lang = 'de'
                    request.query = text
                    request.session_id = event['sender']['id']
                    response = request.getresponse()
                    nlp = json.loads(response.read().decode())
                    logging.info(nlp)
                    message['nlp'] = nlp

            for handler in handlers:
                try:
                    if handler.check_event(event):
                        try:
                            handler.handle_event(event)

                        except Exception as e:
                            logging.exception("Handling event failed")

                            try:
                                sender_id = event['sender']['id']
                                send_text(
                                    sender_id,
                                    'Huppsala, das hat nicht funktioniert :('
                                )

                                if int(sender_id) in ADMINS:
                                    txt = str(e)
                                    txt = txt.replace(PAGE_TOKEN, '[redacted]')
                                    txt = txt.replace(API_AI_TOKEN, '[redacted]')
                                    send_text(sender_id, txt)
                            except:
                                pass

                        finally:
                            break

                except:
                    logging.exception("Testing handler failed")

    return event_handler

handle_events = make_event_handler()


def push_notification():
    data = get_pushes()

    if not data:
        return

    user_list = FacebookUser.objects.values_list('uid', flat=True)

    unavailable_user_ids = list()

    for user in user_list:

        logger.debug("Send Push to: " + user)
        try:
            schema(data, user)
        except Exception as e:
            logger.exception("Push failed")
            try:
                if e.args[0]['code'] == 551:  # User is unavailable (probs deleted chat or account)
                    unavailable_user_ids.append(user)
                    logging.info('Removing user %s', user)
            except:
                pass

        sleep(2)

    for user in unavailable_user_ids:
        try:
            FacebookUser.objects.get(uid=user).delete()
        except:
            logging.exception('Removing user %s failed', user)


def push_breaking():
    data = get_breaking()

    if data is None or data.delivered:
        return

    user_list = FacebookUser.objects.values_list('uid', flat=True)

    for user in user_list:
        logger.debug("Send Push to: " + user)
        # media = '327430241009143'
        # send_attachment_by_id(user, media, 'image')
        try:
            send_push(user, data)
        except:
            logger.exception("Push failed")

        sleep(1)

    data.delivered = True
    data.save(update_fields=['delivered'])

def dsb_update():
    # check for saturday (5) or sunday(6)
    day = datetime.datetime.today().weekday()
    now = datetime.datetime.now().time()
    if day == 5:
        if now >= datetime.time(13, 30) and now <= datetime.time(20, 00):
            parser.get_results_pd()
            parser.update_table()
            parser.get_setlist()
            reopen_data()

    elif day == 6:
        if now >= datetime.time(9, 00) and now <= datetime.time(15, 00):
            parser.get_results_pd()
            parser.update_table()
            parser.get_setlist()
            reopen_data()











#schedule.every(60).seconds.do(push_breaking)
#schedule.every().day.at("18:00").do(push_notification)
schedule.every().day.at("22:00").do(dsb_update)

schedule.every(15).minutes.do(dsb_update)

schedule.every(60).seconds.do(meyton_update)



def schedule_loop():
    while True:
        schedule.run_pending()
        sleep(1)






schedule_loop_thread = Thread(target=schedule_loop, daemon=True)
schedule_loop_thread.start()
