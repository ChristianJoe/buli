
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
from ..data import by_district_id, get_club_info_weapon_buli_region


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

    infoall = get_club_info_weapon_buli_region(club_repl)

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






def letsgo(event,**kwargs):

    get_started(event,**kwargs)



def greetings(event, **kwargs):
    sender_id = event['sender']['id']
    infos = Info.objects.all().order_by('-id')[:1]

    reply = event['message']['nlp']['result']['fulfillment']['speech']

    if infos:
        send_text(sender_id, reply, [quick_reply('Neueste Funktion',['infos_backend'])])

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
Wenn Du Dich mit mir unterhältst, kann ich Dir viele Infos zur Bundesliga Sportschießen nennen:
"""
        send_buttons(sender_id, reply,
                     buttons=[
                        button_postback('Anmelden', ['subscribe']),
                        #button_postback('Tägliche Nachricht',
                        #                {'push': last_push.id, 'next_state': 'intro'}),
                        #button_postback( 'Mein Wahlkreis', ['intro_district']),
                        button_postback('Erklär mal...', ['about']),
                     ])

def about(event, **kwargs):
    sender_id = event['sender']['id']
    reply = '''
Ich bin ein freundlicher Bot mit dem Ziel dich objektiv über die Bundesliga Sportschießen zu informieren.
Alle Informationen die ich dir liefer findest du an vielen Stellen (siehe Daten-Quellen) im Netz. Ich trage die Infos zusammen und du kannst mich gezielt ausfragen.
Du kannst ganz normal mit mir schreiben und ich antworte so gut ich kann.
Durch deine Fragen können die Menschen die mich programmieren sehen, was dich interessiert. Dadurch 'lerne' ich und kann deine Frage vielleicht bald beantworten.

Starte einfach indem du mich mit \"Hallo\" begrüßt!.
            '''
    send_buttons(sender_id, reply,
                buttons = [
                    button_postback("Tabellen", ['table_start']),
                    button_postback("Wettkämpfe", ['competition_start']),
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

    title = "BotBuLi informiert die über die Bundesliga im Sportschießen."
    subtitle = "Befrage den Info Bot zu den Vereinen der 1. und 2. BuLi im Sportschießen, den Schützen und vieles mehr."
    image_url = "https://cc8b346a.ngrok.io/static/bot/final_backround_transparent.png"
    shared_content = [generic_element(title, subtitle, image_url, buttons = [button_web_url("Schreibe BotBuLi", "https://www.m.me/BotBuLi?ref=shared")])]
    message = generic_element("Teile BotBuLi mit deinen Freunden!", buttons = [button_share(shared_content)])

    send_generic(sender_id,
                elements = [message])

def subscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        now = timezone.localtime(timezone.now())
        date = now.date()
        time = now.time()
        reply = "Du bist bereits für Push-Nachrichten angemeldet."
        last_push = Push.objects.filter(
            published=True).exclude(pub_date__date__gt=date).latest('pub_date')

        send_buttons(user_id, reply,
                     buttons=[
                         button_postback('Letzte Push-Nachricht',
                                         {'push': last_push.id, 'next_state': 'intro'}),
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

        FacebookUser.objects.create(uid=user_id)
        logger.debug('subscribed user with ID ' + str(FacebookUser.objects.latest('add_date')))
        reply = """
Danke für deine Anmeldung! Du erhältst nun nach jedem Wettkampftag eine kurze Zusammenfassung der Ergebnisse.
"""
        send_buttons(user_id, reply,
                     buttons=[
                        button_postback('Letzter Wettkampftag',
                                        {'push': last_push.id, 'next_state': 'intro'}),
                     ])


def unsubscribe(event, **kwargs):
    user_id = event['sender']['id']

    if FacebookUser.objects.filter(uid=user_id).exists():
        logger.debug('deleted user with ID: ' + str(FacebookUser.objects.get(uid=user_id)))
        FacebookUser.objects.get(uid=user_id).delete()
        send_text(user_id,
                "Schade, dass dir mein Service nicht gefallen hat. Du wurdest aus der Empfängerliste für Zusammenfassungen gestrichen. "
                "Hätte ich was besser machen können, dann schreib es mir gerne. Ich freue mich über Feedback."
        )
    else:
        reply = "Du bist noch kein Nutzer der BuLi-News. Wenn du dich anmelden möchtest wähle \"Anmelden\" über das Menü."
        send_text(user_id, reply)



def competition_start(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id,
            "Im wesentlichen kannst du mich nach jedem Wettkampf aus der 1. und/oder 2. Bundesliga fragen und ich sage dir, wie er ausgegangen respektive wann er stattfindet."
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
    [quick_reply('Und meine Daten', ['more_data'])])

def more_data(event, **kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id, """
Damit ich verstehen kann was du von mir willst, schicke ich die von dir verschickte Textnachricht an dialogflow.com einen Google Assistant.
Die Daten auf die ich zurückgreife kannst du dir auch auf GitHub anschauen\nhttps://github.com/ChristianJoe/buli\n
Ich halte mich an die Facebook Datenschutzbestimmungen \nhttps://www.facebook.com/about/privacy"""
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
              durch.
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
                    2014/15 SV Kelheim-Gmünd
                    2013/14 SGi Waldenburg
                    2012/13 SV 1935 Kriftel
                    2011/12 SGi Waldenburg
                    2010/11 SGi Waldenburg
                    2009/10 SGi Waldenburg
                    2008/09 SV Kelheim-Gmünd
                    2007/08 SGi Waldenburg
                    2006/07 ESV Weil am Rhein
                    2005/06 SGi Waldenburg
                    2004/05 SGi Waldenburg
                    2003/04 VSS Haltern
                    2002/03 PSV Olympia Berlin
                    2001/02 VSS Haltern
                    2000/01 PSV Olympia Berlin
                    1999/00 PSV Olympia Berlin
                    1998/99 PSV Olympia Berlin
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
              '''
                Amtierender Meister des Bundesliga Sportschießen Luftgewehr ist der SSV St. Hubertus Elsen.
                Im Finale haben sie sich mit 3:2 gegen Eichenlaub Saltendorf durchgesetzt.
                ''',
              [quick_reply('Vergangene Meister',['former_champions_LG']),
              quick_reply('Luftpistole',['champions_LG'])
               ]
              )



def former_champions_LG(event,**kwargs):
    sender_id = event['sender']['id']
    send_text(sender_id,"""Die bisherigen Deutschen Manschaftsmeister im Luftgewehr:
    
    2015/16 SSV St. Hubertus Elsen
    2014/15 SG Coburg
    2013/14 HSG München
    2012/13 HSG München
    2011/12 SSV St. Hubertus Elsen
    2010/11 Der Bund München
    2009/10 HSG München
    2008/09 SG Coburg
    2007/08 SG Coburg
    2006/07 Post SV Plattling
    2005/06 SSV St. Hubertus Elsen
    2004/05 BSV Buer-Bülse
    2003/04 SV Affalterbach
    2002/03 BSV Buer-Bülse
    2001/02 BSV Buer-Bülse
    2000/01 Der Bund München
    1999/00 Der Bund München
    1998/99 SV Affalterbach
    1997/98 SV Affalterbach"""#,
             # quick_reply('Meister LP',['champions_LP'])
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
