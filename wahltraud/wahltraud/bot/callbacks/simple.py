
import logging
import datetime

from fuzzywuzzy import fuzz, process
from django.conf import settings
from django.utils import timezone

from pathlib import Path
from backend.models import FacebookUser, Wiki, Push, Info
from ..fb import (send_buttons, button_postback, send_text, quick_reply, send_generic,
                  generic_element, button_web_url, button_share, send_attachment,
                  send_attachment_by_id, guess_attachment_type)
from .shared import get_pushes, schema, send_push, get_pushes_by_date
from ..data import by_district_id, get_club_info_weapon_buli_region, get_results_team, take_info


logger = logging.getLogger(__name__)


def update_api(event,**kwargs):
    sender_id = event['sender']['id']

    if sender_id == '1642888035775604':
        send_buttons(sender_id, 'Welches Update',
                     buttons=[
                            button_postback("Ergebnisse",
                                          ['update_results']
                                        ),
                            button_postback('Tabelle', ['update_table_payload']),
                          button_postback('Setzliste', ['update_setlist'])
                     ])
    else:
        send_text(sender_id, 'jo jo jo, kommt')


def club_info_api(event,parameters,**kwargs):
    club = parameters.get('clubs')

    club_info(event,{'club_info': club})




def club_info(event,payload,**kwargs):
    sender_id = event['sender']['id']
    club = payload['club_info']

    club_repl = club
    #for ending in [' II', ' I', ' 2', 'FSG']:
    #    if club_repl.endswith(ending):
    #        club_repl = club_repl.replace(ending, '').strip()

    infoall = club_weapon_buli_region(event,{'club_weapon_buli_region': club_repl, 'payl': 'club_info'})
    if not infoall:
        return

    addbutton = False
    info = infoall
    if len(infoall) == 2:
        addbutton = True
        info = infoall[0]
        info2 = infoall[1]
        for element in infoall:
            if element['club'] == club:
                info = element
                addbutton = False
                break

    if len(info) == 4:

        buttons = [button_postback('Wettkämpfe',
                                {'club_list_competitions': info}),
                      button_postback('Tabelle {buli} {region}'.format(
                          buli = info['buli'],
                          region = info['region']
                      ),
                                       {'table_league': info}),
                      button_postback('Setzliste',
                                      {'setlist_payload': club})
                       ]

        if addbutton:
            buttons = [buttons[0],buttons[-1]]
            buttons.append(
                button_postback(info2['club'],
                                {'club_info': info2['club']}
                                )
            )
        send_buttons(sender_id,
                     'Die Mannschaft {club} startet in der {buli} {weapon} {region}.'.format(
                         club=info['club'],
                         weapon=info['weapon'],
                         buli=info['buli'],
                         region=info['region']
                     ),
                     buttons = buttons

                     )


    else:

        send_text(sender_id, 'Info zu {club}, {menge}'.format(club= club,
                                                          menge = len(info)))



def club_weapon_buli_region(event,payload,**kwargs):
    sender_id = event['sender']['id']
    club = payload['club_weapon_buli_region']
    payl = payload['payl']

    club_repl = club
    #for ending in [' II', ' I', ' 2', 'FSG']:
    #    if club_repl.endswith(ending):
    #        club_repl = club_repl.replace(ending, '').strip()
    results_team = get_results_team()

    club_all = results_team[(results_team['guest_team'] == club_repl) | (results_team['guest_team_short'] == club_repl)]

    elements = list(set(list(club_all['guest_team'])))

    if len(elements) == 1:
        club_pd = club_all[club_all['guest_team'] == elements[0]].iloc[0]
        info = take_info(club_pd)
        return info
    else:
        infos = []
        buttons = []
        for clubAB in elements:
            club_pd = club_all[club_all['guest_team'] == clubAB].iloc[0]
            infos.append(take_info(club_pd))
            buttons.append(button_postback(clubAB,{payl: clubAB}))
        send_buttons(sender_id,
                     '{club} hat mehrere Mannschaften am Start.'.format(club = club),
                     buttons = buttons)
        return None





def letsgo(event,**kwargs):

    get_started(event,**kwargs)



def greetings(event, **kwargs):
    sender_id = event['sender']['id']
    infos = Info.objects.all().order_by('-id')[:1]

    reply = event['message']['nlp']['result']['fulfillment']['speech']

    if infos:
        send_text(sender_id, reply, [quick_reply('Ergebnis-Dienst',['subscribe']),
                                     quick_reply('Neueste Funktion',['infos_backend'])])

    else:
        send_text(sender_id, reply)


def infos_backend(event,**kwargs):
    sender_id = event['sender']['id']
    infos = Info.objects.all().order_by('-id')[:1]

    info = infos[0]

    if info.attachment_id:
        send_attachment_by_id(
            sender_id,
            info.attachment_id,
            guess_attachment_type(str(info.media))
        )

    send_text(sender_id, info.content)



def get_started(event, **kwargs):
    sender_id = event['sender']['id']
    try:
        referral = event.get('postback').get('referral')
    except:
        referral = None

    if referral:
        ref = referral.get('ref')
        logging.info('Bot wurde mit neuem User geteilt: ' + ref)
        if ref.startswith("WK"):
            wk = int(ref.replace("WK", ""))
            district = by_district_id[str(wk)]

            reply = """
Ah, ein neuer Gast! Wie schön, dass mein Freund Novi 🤖 dich zu mir geschickt hat!

Hallo, ich bin Wahltraud 🐳
Wenn du den Button \"Zeige Wahlkreis-Info\" anklickst, werde ich dich zunächst mal über deinen angefragten Wahlkreis informieren.
Allerdings habe ich noch viel mehr auf Lager - z.B. Informationen zu Kandidaten, Parteien oder deren Wahlprogrammen.
Du kannst auch jeden Abend eine Info zur Wahl erhalten. Wenn du das möchtest, klicke auf \"Anmelden\".
Wenn Du genauer wissen möchtest, was ich kann, klicke auf \"Erklär mal\". Oder leg direkt los und sende mir eine Nachricht."""
            send_buttons(sender_id, reply,
                         buttons=[
                           # button_postback("Zeige Wahlkreis-Info",
                        #                 {'show_district': district['uuid']}),
                            button_postback('Anmelden', ['subscribe']),
                           # button_postback('Erklär mal...', ['about'])
                         ])
    else:
        now = timezone.localtime(timezone.now())
        date = now.date()
        time = now.time()

        if time.hour < 18:
            last_push = Push.objects.filter(
                published=True).exclude(pub_date__date__gte=date).latest('pub_date')
        else:
            last_push = Push.objects.filter(
                published=True).exclude(pub_date__date__gt=date).latest('pub_date')

        reply = """
Hallo, ich bin BotBuLi.
Wenn Du Dich mit mir schreibst, kann ich Dir viele Infos zur Bundesliga Sportschießen nennen. Klicke einen Button oder schreibe 'Hallo':
"""
        send_buttons(sender_id, reply,
                     buttons=[
                        button_postback('Ergebnis-Dienst', ['subscribe']),
                        #button_postback('Live Ergebniss',
                        #                {'push': last_push.id, 'next_state': 'intro'}),
                        button_postback( 'Start', ['infos_backend']),
                        button_postback('Erklär mal...', ['about']),
                     ])

def about(event, **kwargs):
    sender_id = event['sender']['id']
    reply = '''
Ich bin ein freundlicher Bot der dich über die Bundesliga Sportschießen informiert.
Die Idee ist, dass du mir Fragen stellst die dich interessieren. Ich versuche diese zu beantworten. Ich bin ein lernendes Computerprogramm und 
durch deine Fragen können die Programmiere sehen, sehen was coole neue Funktionen sind. Also frag einfach drauf los. 
            '''
    send_buttons(sender_id, reply,
                buttons = [
                    button_postback("Was kann ich fragen?", ['infos_backend']),
                    button_postback("Tabellen", ['table_start']),
                    button_postback("Daten-Quellen", ['menue_data'])
                ])

def push(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    date = parameters.get('date')


    if not date:
        data = get_pushes(True)
        if len(data) == 0:
            schema(data, sender_id)
            #reply = 'Dein Wahl-Update ist noch in Arbeit. Versuche es nach 18 Uhr wieder...'
            #send_text(sender_id, reply)
        else:
            schema(data, sender_id)

    else:
        if len(date) == 1:
            find_date = datetime.datetime.strptime(date[0], '%Y-%m-%d').date()
            data = get_pushes_by_date(find_date)

        if len(data) == 0:
            reply = 'Für dieses Datum liegen mir keine Zusammenfassung vor. Wähle ein Datum, wähle ein anderes Wochenende.'
            send_text(sender_id, reply)
        else:
            schema(data, sender_id)


def share_bot(event, **kwargs):
    sender_id = event['sender']['id']
    reply = "Teile BotBuLi mit deinen Freunden!"

    title = "BotBuLi informiert die über die 1. und 2. Bundesliga im Sportschießen."
    subtitle = "Befrage den Info Bot zu den Vereinen und Schützen."
    image_url = "https://cc8b346a.ngrok.io/static/bot/final_backround_transparent.png"
    shared_content = [generic_element(title, subtitle, image_url, buttons = [button_web_url("Schreibe BotBuLi", "https://www.m.me/BotBuLi?ref=shared")])]
    message = generic_element("Teile BotBuLi mit deinen Freunden!", buttons = [button_share(shared_content)])

    send_generic(sender_id,
                elements = [message])

def subscribe(event, **kwargs):
    user_id = event['sender']['id']

    buttons = []
    if FacebookUser.objects.filter(uid=user_id).exists():
        p = FacebookUser.objects.get(uid=user_id)
    else:
        FacebookUser.objects.create(uid=user_id)
        p = FacebookUser.objects.get(uid=user_id)

    reply = "Sobald ein Wettkampf der 1.Bundesliga beendet ist erhälst du das Ergebnis per Push-Benachrichtigung von mir!\n" \
            "Du bist für folgende Ergebnis-Ticker angemeldet:\n\n"
    if p.rifle and p.pistole:
        reply += "Luftgewehr und Luftpistole"
        buttons.append(button_postback('Abmelden Gewehr',{'unsubscribe_weapon': 'rifle'}))
        buttons.append(button_postback('Abmelden Pistole',{'unsubscribe_weapon' : 'pistole'}))
        buttons.append(button_postback('Komplett abmelden',{'unsubscribe_weapon' : 'both'}))

    elif p.pistole:
        reply += "Luftpistole"
        buttons.append(button_postback('Anmelden Gewehr',{'subscribe_weapon' : 'rifle'}))
        buttons.append(button_postback('Abmelden Pistole',{'unsubscribe_weapon' : 'pistole'}))
    elif p.rifle:
        reply += "Luftgewehr"
        buttons.append(button_postback('Abmelden Gewehr',{'unsubscribe_weapon': 'rifle'}))
        buttons.append(button_postback('Anmelden Pistole',{'subscribe_weapon' : 'pistole'}))
    else:
        reply += 'Noch gar nicht angemeldet...'
        buttons.append(button_postback('LG & LP anmelden',{'subscribe_weapon' : 'both'}))
        buttons.append(button_postback('Anmelden Gewehr',{'subscribe_weapon' : 'rifle'}))
        buttons.append(button_postback('Anmelden Pistole',{'subscribe_weapon' : 'pistole'}))

    send_buttons(user_id, reply,
                 buttons=buttons,
                 )




def subscribe_weapon(event,payload, **kwargs):
    user_id = event['sender']['id']
    weapon = payload['subscribe_weapon']


    if weapon == 'rifle':
        FacebookUser.objects.filter(uid=user_id).update(rifle=True)
    if weapon == 'pistole':
        FacebookUser.objects.filter(uid=user_id).update(pistole=True)
    if weapon == 'both':
        FacebookUser.objects.filter(uid=user_id).update(rifle=True)
        FacebookUser.objects.filter(uid=user_id).update(pistole=True)

    logger.debug('subscribed user with ID ' + user_id + ' for ' + weapon)


    send_text(user_id,'🙌 Tip Top! Ab jetzt verpasst du keine {weapon} Live-Ergebnis mehr und erhälst spannende Infos!'.format(
        weapon = 'LP' if weapon == 'pistole' else('LG' if weapon == 'rifle' else 'LG und LP')
    )
              )


def unsubscribe_weapon(event, payload, **kwargs):
    user_id = event['sender']['id']
    weapon = payload['unsubscribe_weapon']

    if weapon == 'rifle':
        FacebookUser.objects.filter(uid=user_id).update(rifle=False)
    if weapon == 'pistole':
        FacebookUser.objects.filter(uid=user_id).update(pistole=False)
    if weapon == 'both':
        FacebookUser.objects.filter(uid=user_id).update(rifle=False)
        FacebookUser.objects.filter(uid=user_id).update(pistole=False)

    logger.debug('subscribed user with ID ' + user_id + ' for ' + weapon)
    p = FacebookUser.objects.get(uid=user_id)
    if not p.pistole and not p.rifle:
        p.delete()
        reply = 'Ja schade...😞. Gibt es einen Grund für dein Abmeldung? PS: Einfach \"anmelden\" schreiben und du bist wieder dabei!'
    else:
        reply = 'Alles klar. keine {weapon} News mehr. Schreib mir einfach \"anmelden\" und du bist wieder dabei!'.format(
            weapon = 'LG' if weapon == 'rifle' else 'LP'
        )

    send_text(user_id, reply)






def unsubscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        logger.debug('deleted user with ID: ' + str(FacebookUser.objects.get(uid=user_id)))
        FacebookUser.objects.get(uid=user_id).delete()
        send_text(user_id,
                "Schade. Du erhälst hiermit keine Benachrichtigungen mehr. "
                "Du kannst dich jederzeit wieder über das Menü anmelden!"
        )
    else:
        reply = "Du bist noch kein Nutzer der BuLi-News. Wenn du dich anmelden möchtest wähle \"Anmelden\" über das Menü."
        send_text(user_id, reply)



def competition_start(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id,
            "Im wesentlichen kannst du mich nach jedem Wettkampf aus der 1. oder 2. Bundesliga fragen und ich sage dir, wie er ausgegangen respektive wann er stattfindet."
            ""
            "Frag zum Beispiel: \"Wie lief der Wettkampf zwischen Kelheim und Waldkirch?\""#,
              #[quick_reply('Nächste Wettkämpfe', ['next_event'])
               #quick_reply('Ausrichter', ['next_event'])]

              )

''



def table_start(event, **kwargs):
    sender_id = event['sender']['id']

    send_buttons(sender_id,
                 "Ich kenne alle aktuellen Tabellenstände der 1. und 2. BuLi. Glaubste nicht?",
                 [button_postback('1. BuLi Nord',
                                  {'table_payload': {'buli': "1.BuLi", "region": "Nord"}}),
                  button_postback('1. BuLi Süd',
                                  {'table_payload': {'buli': "1.BuLi", "region":  "Süd"}}
                                  ),
                  button_postback('2. BuLi',
                                  ['table_second_league']
                  )
                  ]
                 )

def questions(event,**kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id,
              "Die Interviews stoppen nach exakt vier Minuten. Theoretisch hätten diese 22+6 Fragen beantwortet werden können:\n"
              "https://blog.wdr.de/ihrewahl/die-fragen-stehen-fest/",
              [quick_reply('Zeige Kandidaten', ['candidate_check_start'])]
              )



def menue_manifesto(event, **kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id,
              'Was steht eigentlich in so einem Wahlprogramm? '
              'Kaum ein Wähler liest sich ein Wahlprogramm durch. Ich biete Dir einen Einblick '
              'in die Programme von CDU/CSU, SPD, DIE LINKE, DIE GRÜNEN, FDP und AfD.\n'
              'Ich zeige dir einzelne Sätze, in denen ein Schlagwort für das du dich interessierst vorkommt.',
              [quick_reply('Zeig mir Sätze', ['manifesto_start']), quick_reply('Wie geht`s?', {'about_manifesto': 'one'})])

def about_manifesto(event, payload, **kwargs):
    sender_id = event['sender']['id']
    state = payload['about_manifesto']

    if state == 'one':
        send_text(sender_id,
                  'Nenne mir ein Schlagwort und ich schaue nach wie oft ich das Wort in den Programmen gefunden habe.'
                  ' Frage mich zum Beispiel nach \"Steuern\". Interessiert du dich für das Programm einer bestimmten Partei, so gib diese einfach mit an.',
                  [quick_reply('Ok! Los geht`s', ['manifesto_start']),
                   quick_reply('weiter', {'about_manifesto': 'two'})])
    elif state == 'two':
        send_text(sender_id,
                  'Ein einzelner Satz ist oft nicht hilfreich, darum kannst du dir den Kontext anzeigen lassen. '
                  'Falls du richtig neugierig geworden bist, bekommst du auch den Link zum Wahlprogramm.',
                  [quick_reply('Ok! Los geht`s', ['manifesto_start']),
                  quick_reply('Noch was?',{'about_manifesto': 'three'})])
    elif state == 'three':
            send_text(sender_id,
                      'Ich suche wirklich nur ein Schlagwort und keine Themen.'
                      ' Findest du also etwas nicht, versuche es am bestem mit einem ähnlichen Schlagwort.',
                      [quick_reply('Ok! Los geht`s', ['manifesto_start'])])


def menue_data(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, """
Um dich mit so vielen Informationen beliefern zu können, musste ich mich natürlich selbst erstmal schlau machen.
Folgende Quellen habe ich dazu verwendet:
- http://bundesliga.dsb.de/
- http://bundesliga.meyton.info/
- Homepages der Vereine""",
    [quick_reply('Meine Daten???', ['more_data'])])

def more_data(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, """
Damit ich verstehen kann was du von mir willst, schicke ich die von dir verschickte Textnachricht an dialogflow.com einen Google Assistant.
Die Daten auf die ich zurückgreife kannst du dir auch auf GitHub anschauen\nhttps://github.com/ChristianJoe/buli\n
Darüber hinaus halte ich mich an die Facebook Datenschutzbestimmungen \nhttps://www.facebook.com/about/privacy"""
    )

def story(event, payload, **kwargs):
    sender_id = event['sender']['id']
    push_id = payload['push_id']
    next_state = payload['next_state']
    data = Push.objects.get(id=push_id)
    send_push(sender_id, data, next_state)


def wiki(event, parameters, **kwargs):
    user_id = event['sender']['id']
    text = parameters.get('wiki')

    wikis = Wiki.objects.all()
    best_match = process.extractOne(
        text,
        wikis,
        scorer=fuzz.token_set_ratio,
        score_cutoff=90)

    '''
    try:
        best_match = [Wiki.objects.get(input=text)]
    except Wiki.DoesNotExist:
        best_match = None
    '''

    if not best_match:
        reply = "Tut mir Leid, darauf habe noch ich keine Antwort. Frag mich die Tage nochmal."
    else:
        match = best_match[0]
        if match.output == 'empty':
            reply = "Moment, das muss ich nachschauen. Eine Antwort habe ich bald.".format(word=text)
        else:
            reply = match.output

        if match.attachment_id:
            try:
                send_attachment_by_id(
                    user_id,
                    str(match.attachment_id),
                    type=guess_attachment_type(str(match.media))
                )
            except:
                logging.exception('Sending attachment failed')

    if reply:
        send_text(user_id, reply)


def apiai_fulfillment(event, **kwargs):
    sender_id = event['sender']['id']

    fulfillment = event['message']['nlp']['result']['fulfillment']
    if fulfillment['speech']:
        send_text(sender_id, fulfillment['speech'])

def push_step(event, payload, **kwargs):
    sender_id = event['sender']['id']
    push_id = payload['push']
    next_state = payload['next_state']

    push_ = Push.objects.get(id=push_id)
    send_push(sender_id, push_, state=next_state)


def sunday_poll(event, **kwargs):
    sender_id = event['sender']['id']

    quick_replies = [
        #quick_reply(
        #    'infratest dimap',
        #    ['menue_data']
        #),
        quick_reply(
            'Info Parteien',
            {'show_parties': 'etabliert'}
        )
    ]

    send_text(sender_id,
              'Hier das Ergebnis der aktuellen Sonntagsfrage von infratest dimap vom 14.September.'
              )

    send_attachment(
        sender_id,
        settings.SITE_URL + '/static/bot/sonntagsfrage.jpg'
    )

    send_text(sender_id,
              'Wenn du etwas zu einer bestimmten Partei wissen möchtest, gib einfach ihren Namen ein.',
              quick_replies
              )


def champions_LP(event,**kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id,
              '''
              Aktuelle und damit amtierender Deutscher Meister ist der SV Kelheim-Gmünd. 
              In einem Spannenden Finale der Saison 2016/17 setze er sich mit 4:1 gegen SV 1935 Kriftel
              durch. Es ist bereits der 3. Titel für Kelheim-Gmünd.\n Rekordmeister ist die SGi Walkdenburg mit 7 Titeln.
              ''')
    send_text(sender_id,
              'Ich bin gespannt, wer dieses Jahr gewinnt!',
              [quick_reply('Bisherige Meister',['former_champions_LP']),
              quick_reply('Luftgewehr',['champions_LG'])
               ]
              )


def former_champions_LP(event,**kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id,  """Hier die bisherigen Deutschen Mannschaftsmeister mit der Luftpistole:
                                         
                    2015/16 SGi Waldkirch
                    2014/15 SV Kelheim-Gmünd (2)
                    2013/14 SGi Waldenburg (7)
                    2012/13 SV 1935 Kriftel 
                    2011/12 SGi Waldenburg (6)
                    2010/11 SGi Waldenburg (5)
                    2009/10 SGi Waldenburg (4)
                    2008/09 SV Kelheim-Gmünd 
                    2007/08 SGi Waldenburg (3)
                    2006/07 ESV Weil am Rhein
                    2005/06 SGi Waldenburg (2)
                    2004/05 SGi Waldenburg 
                    2003/04 VSS Haltern (2)
                    2002/03 PSV Olympia Berlin (5)
                    2001/02 VSS Haltern 
                    2000/01 PSV Olympia Berlin (4)
                    1999/00 PSV Olympia Berlin (3)
                    1998/99 PSV Olympia Berlin (2)
                    1997/98 PSV Olympia Berlin
                    """#,
                    #[quick_reply('Luftgewehr',['champions_LG'])]
              )


def champions_api(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    weapon = parameters.get('weapon')

    if weapon == 'LG':
        champions_LG(event)
    elif weapon == 'LP':
        champions_LP(event)
    else:
        send_buttons(sender_id,
                     "In welcher Diziplin?",
                     [button_postback('Luftgewehr',
                                      ['champions_LG']),
                      button_postback('Luftpistole',
                                      ['champions_LP']
                                      )
                      ]
                     )



def champions_LG(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id,
                'Amtierender Meister der Bundesliga Luftgewehr ist SSV St. Hubertus Elsen.'
                'Im Finale der Saison 16/17 haben sie sich mit 3:2 gegen Eichenlaub Saltendorf durchgesetzt.'
                'Es bereits der 4.Titel für Elsen. Sie sind somit alleiniger Rekordmeister!\n\n'
                'Wer es dieses Jahr wohl den Spiegel nach Hause holt???'
                ,
              [quick_reply('Vergangene Meister',['former_champions_LG']),
              quick_reply('Luftpistole',['champions_LG'])
               ]
              )



def former_champions_LG(event,**kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id,"""Die bisherigen Deutschen Manschaftsmeister im Luftgewehr:
    
    2015/16 SSV St. Hubertus Elsen (3)
    2014/15 SG Coburg (3)
    2013/14 HSG München (3)
    2012/13 HSG München (2)
    2011/12 SSV St. Hubertus Elsen (2)
    2010/11 Der Bund München (3)
    2009/10 HSG München
    2008/09 SG Coburg (2)
    2007/08 SG Coburg
    2006/07 Post SV Plattling
    2005/06 SSV St. Hubertus Elsen
    2004/05 BSV Buer-Bülse (3)
    2003/04 SV Affalterbach (3)
    2002/03 BSV Buer-Bülse (2)
    2001/02 BSV Buer-Bülse
    2000/01 Der Bund München (2)
    1999/00 Der Bund München 
    1998/99 SV Affalterbach (2)
    1997/98 SV Affalterbach"""#,
             # quick_reply('Meister LP',['champions_LP'])
              )

def buli_live_start(event,**kwargs):
    sender_id = event['sender']['id']

    send_buttons(sender_id,
              'Wenn ein Wettkampf in der 1. Bundesliga läuft, kannst du mich nach den Live-Ergebnissen fragen. '
              'Hast du dich für LG und/oder LP angemeldet, schicke ich dir die Ergebnisse als Push sobald der Wettkampf beendet ist!',
                 buttons=[
                     button_postback('Zeig Live Ergebnisse',['buli_live']),
                     button_postback('LG/LP anmelden!!',['subscribe'])
                 ])

def interviews_start(event,**kwarg):
    sender_id = event['sender']['id']

    send_text(sender_id,
              "An dieser Stelle findest du bald Interviews.\n"
              #"Du bist selbst Schütze und hättest Spaß an einem kurzen Interview? "
     )



def who_votes(event, **kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id,
              '''
              Wer in Deutschland wählen will, muss
1. die 🇩🇪 Staatsbürgerschaft besitzen
2. am Wahltag mindestens 18 sein (Du wurdest am 25.9.1999 geboren? Sorry...) &
3. mindestens drei Monate lang den Hauptwohnsitz in der Bundesrepublik gehabt haben.

Deutsche, die im Ausland leben, müssen irgendwann in den letzten 25 Jahren mal drei Monate in Deutschland gewohnt haben - sonst erlischt das aktive Wahlrecht.

Das aktive Wahlrecht kann man auch verlieren, wenn man z.B. für eine besondere Straftat verurteilt wurde oder schuldunfähig in der Psychiatrie ist. Details: https://www.bundestag.de/service/glossar/glossar/A/akt_wahlrecht/246252
              ''')
