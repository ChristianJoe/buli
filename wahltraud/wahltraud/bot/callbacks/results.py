import logging
import operator
import pandas as pd

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import by_uuid, get_dates, get_results_team, get_results_shooter, get_tables, get_club_info_weapon_buli_region
from .parser import get_meyton, get_meyton_results
from .simple import club_info
import datetime

#enable logging
logger = logging.getLogger(__name__)




def table_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    buli = parameters.get('league') # first or second BuLi
    region =  parameters.get('region')
    weapon = parameters.get('weapon')

    payloads = {'buli': buli,
               'region': region,
               'weapon': weapon}

    table_payload(event,{'table_payload': payloads})


def table_payload(event,payload,*kwarks):
    sender_id = event['sender']['id']
    payloads = payload['table_payload']

    try:
        buli = payloads['buli']
    except:
        buli = ''
    try:
        region = payloads['region']
    except:
        region = ''
    try:
        weapon = payloads['weapon']
    except:
        weapon =  ''


    if region in ['West','Ost','Südwest']:
        buli = '2.BuLi'



    if buli and region and weapon:
        table_league(event,{'table_league': payloads})
    elif buli and region:
        payloadsLG = {'buli': buli,
                       'region': region,
                       'weapon': "LG"}
        payloadsLP = {'buli': buli,
                       'region': region,
                       'weapon': "LP"}

        send_buttons(sender_id,
                     'Triff eine wahl',
                     [button_postback('Luftgewehr',
                                      {'table_payload': payloadsLG}),
                      button_postback('Luftpistole',
                                      {'table_payload': payloadsLP}
                     )
                      ]
                     )
    elif buli:
        if buli == "1.BuLi":
            payload_north = {'buli': '1.BuLi',
                            'region': 'Nord',
                            'weapon': weapon}
            payload_south = {'buli': '1.BuLi',
                            'region': 'Süd',
                            'weapon': weapon}
            send_text(sender_id,
                      'Nord oder Süd',
                      quick_replies = [
                          quick_reply('Nord', payload_north),
                          quick_reply('Süd', payload_south)

                      ]
                      )
        else:
          table_second_league(event,['table_second_league'])
    else:#nothing given
        options = []
        for key in [ 'LG BuLi Nord', 'LG BuLi Süd', 'LP BuLi Nord', 'LP BuLi Süd' ]:
            payloads = {'buli': '1.BuLi',
                       'region': key.split(' ')[2],
                       'weapon': key.split(' ')[0]}
            options.append(
                quick_reply(key, {'table_league': payloads})
            )
        options.append(
                quick_reply('2.Buli', ['table_second_league'])
            )
        send_text(sender_id, 'Welche Liga?' , quick_replies = options)





def table_second_league(event,payload,**kwargs):
    #choosing second league
    sender_id = event['sender']['id']
    competitons = {
                   "2.BuLi Süd": 'Süd' ,
                   "2.BuLi Nord": 'Nord',
                   "2.BuLi West": 'West',
                   "2.BuLi Ost": 'Ost',
                   "2.BuLi Südwest": 'Südwest'
                   }

    options = []

    for  element, key in competitons.items():
        payloads = {'buli': "2.BuLi",
                    'region': key}


        options.append(
            quick_reply(key,{'table_payload': payloads })
        )


    send_text(sender_id,'Such dir eine Liga aus.', quick_replies = options)










def table_league(event,payload,**kwargs):
    sender_id = event['sender']['id']
    payloads = payload['table_league']

    offset = int(payload.get('offset', 0))

    buli = payloads['buli']
    region = payloads['region']
    weapon = payloads['weapon']

    if weapon == 'Luftgewehr':
        weapon = 'LG'
    elif weapon == 'Luftpistole':
        weapon = 'LP'

    id = weapon + buli + ' ' + region

    tables = get_tables()
    table_league = tables[tables['id']== id]

    logger.info('Ergebnisliste: {id}'.format(
        id=id))

    num_league = 4

    if table_league.shape[0] - (offset + num_league) == 1:
        num_league = 3
    elements = []
    for index in range(offset, offset + num_league):
        data = table_league.iloc[index]
        payload_button = payloads
        payload_button['club'] = data['club']
        elements.append(
            list_element(
                '{rank}. {club} '.format(
                    rank=data['rank'],
                    club=data['club']
                ),
                subtitle="TEAM   %d : %d    EINZEL   %d : %d" % (
                 data['team_won'], data['team_lost'],data['single_won'], data['single_lost'],),
                buttons=[button_postback("Wettkämpfe",  {'club_list_competitions': payload_button})]
                # image_url=candidate.get('img') or None
            )
        )

    if table_league.shape[0] - offset > num_league:
        button = button_postback("Plätze %d - %d" %(offset+num_league+1, (offset+2*num_league)),
                                 {'table_league': payloads,
                                  'offset': offset + num_league})
    else:
        button = button_postback("Andere Liga", {'table_league': {'weapon': 'LG'} })

    if offset == 0:
        send_text(sender_id, '{buli} {weapon}. Gruppe {region}'.format(
            buli=buli,
            weapon=weapon,
            region=region
                    )
                  )
    send_list(sender_id, elements, button=button)






def club_list_competitions(event,payload,**kwargs):
    sender_id = event['sender']['id']
    info = payload['club_list_competitions']
    offset = int(payload.get('offset', 0))

    weapon = info['weapon']
    club = info['club']
    league = info['buli'] +' '+ info['region']

    if weapon == "LP":
        abbrv_weapon = "Luftpistole"
    else:
        abbrv_weapon = "Luftgewehr"


    results = get_results_team()

    results_league = results[(results['league'] == league) & (results['weapon'] == abbrv_weapon)]
    results_club = results_league[(results_league['guest_team'] == club) | (results_league['home_team'] == club)]


    num_league = 4

    if results_club.shape[0] - (offset + num_league) == 1:
        num_league = 3
    if results_club.shape[0] - (offset + num_league) < 1:
        num_league = 4 + (results_club.shape[0] - (offset + num_league))

    elements = []
    for index in range(offset, offset + num_league):
        data = results_club.iloc[index]

        if data['home_points'] + data['guest_points'] != 0:
            sbtle = "%d : %d --  %d : %d" % (data['home_points'], data['guest_points'],
                                             data['home_result'], data['guest_result'])
            button_comp = [button_postback("Paarungen", {'competition_results':  data['comp_id']})]
        else:
            date = data['date'].strftime("%d.%m.%Y")
            sbtle = date+', '+ data['time'] + ' - Ausrichter: ' + data['host']
            club_oponent = data['guest_team']
            if club_oponent == club:
                club_oponent = data['home_team']
            button_comp = [button_postback('Info Gegner', {'club_info': club_oponent})]

        elements.append(
            list_element(
                '#{index} - {home} : {guest} '.format(
                    index = index+1,
                    home=data['home_team'],
                    guest=data['guest_team']
                ),
                subtitle=sbtle,
                buttons=button_comp
                # image_url=candidate.get('img') or None
            )
        )


    if results_club.shape[0] - offset > num_league:
        button = button_postback("Wettkämpfe %d - %d" %(offset+num_league+1, (offset+2*num_league)),
                                {'club_list_competitions': info,
                                  'offset': offset + num_league})
    else:
        button = button_postback("von vorn", ['table_second_league'])

    if offset == 0:
        id = info['weapon'] + info['buli'] + ' ' + info['region']
        tables = get_tables()
        go_table = tables[(tables['club']== club)].iloc[0]

        text_reply = '{club} liegt derzeit auf Platz {pos} der {liga} {region}\n\n Teampunkte: {win} : {los}\nEinzelpunkte: {winE} : {losE}'.format(
                                 club=club,
                                 liga = info['buli'],
                                 region = info['region'],
                                 pos = go_table['rank'],
                                 win = go_table['team_won'],
                                 los = go_table['team_lost'],
                                 winE = go_table['single_won'],
                                 losE = go_table['single_lost']
                                )

        send_text(sender_id, text_reply
                  )
    send_list(sender_id, elements, button=button)





def competition_results(event,payload,**kwargs):
    sender_id = event['sender']['id']
    offset = int(payload.get('offset', 0))
    comp_id = payload['competition_results']

    results_shooter = get_results_shooter()

    results_club = results_shooter[results_shooter['comp_id'] == comp_id]

    num_league = 4

    if results_club.shape[0]/2 - (offset + num_league) == 1:
        num_league = 3
    if results_club.shape[0]/2 - (offset + num_league) < 1:
        num_league = 4 + (int(results_club.shape[0]/2) - (offset + num_league))

    elements = []
    for index in range(offset, offset + num_league):
        home = results_club.iloc[2*index]
        guest = results_club.iloc[2*index+1]

        sbtle = "{fl_home} {first_home} {last_home} : {first_guest} {last_guest} {fl_guest}".format(
            first_home = home['first_name'],
            last_home = home['last_name'],
            first_guest = guest['first_name'],
            last_guest = guest['last_name'],
            fl_home = '🎯' if home['point'] == 1 else '',
            fl_guest='🎯' if guest['point'] == 1 else ''
        )
        #button_comp = [button_postback("Einzelergebnisse", {'competition_results': data['comp_id']})]

        text = "#{pos}:    {h_ringe} : {g_ringe}".format(
            #h_punkt = home['point'],
            h_ringe = home['result'],
            g_ringe = guest['result'],
            #g_punkt = guest['point'],
            pos = home['position']
        )

        if home['shoot_off'] != guest['shoot_off']:
            text += "    --> Stechen <--  {home} : {guest}".format(home = home['shoot_off'],guest=guest['shoot_off'])

        elements.append(
            list_element(
                text,
                subtitle=sbtle,
                #buttons=button_comp
                # image_url=candidate.get('img') or None
            )
        )


    if results_club.shape[0]/2 - offset > num_league:
        button = button_postback("Paarung %d - %d" % (offset + num_league + 1, (offset + 2 * num_league-1)),
                                 {'competition_results': comp_id,
                                  'offset': offset + num_league})
    else:
        button = button_postback("Tabelle {comp}".format(
            comp = comp_id[2:][:-2]
            ),
            {'table_payload': {'buli': comp_id[2:].split(' ')[0] ,
                                 'region': comp_id[2:].split(' ')[1][:-2],
                                'weapon': comp_id[0:2],
                                                               }})

    if offset == 0:
        goal = '🎯🎯🎯🎯🎯'
        total_points_home = results_club[results_club['home'] == True]['point'].sum()
        text_first = '{home}  {home_points}  :  {guest_points}  {guest}'.format(
            home = results_club['team_full'].iloc[0],
            guest = results_club['team_full'].iloc[1],
            home_points =total_points_home,      # goal[0:total_points_home],
            guest_points =5 - total_points_home  # goal[0:(5- total_points_home)]
        )


        if len(results_club['shoot_off'].unique()) != 1:
            text_first += "\n Davon waren Punkte durch Stechen: {home}{guest}".format(
                home = goal[0:results_club[(results_club['shoot_off']!=' ') & (results_club['home']== True)]['point'].sum()],
                guest = goal[0:results_club[(results_club['shoot_off']!=' ') & (results_club['home']== False)]['point'].sum()]
            )



        send_text(sender_id,text_first)

    send_list(sender_id, elements, button=button)




def results_api(event, parameters, **kwargs):
    club = parameters.get('clubs')

    results_club(event, {'results_club': club})




def results_club(event, payload, **kwargs):
    sender_id = event['sender']['id']
    club = payload['results_club']

    club_repl = club
    for ending in ['II', 'I', '2', 'FSG']:
        club_repl = club_repl.replace(ending, '').strip()

    infoall = get_club_info_weapon_buli_region(club_repl)

    if len(infoall) == 2:
        club_info(event,{'club_info':club})
    else:
        club_list_competitions(event,{'club_list_competitions': infoall})




def shooter_results_api(event, parameters, **kwargs):
    first_name = parameters.get('first_name')
    last_name = parameters.get('last_name')
    club = parameters.get('club')

    payloads = {'first_name': first_name,
               'last_name': last_name,
               'club' : club
               }

    shooter_results(event,{'shooter_results': payloads},**kwargs)


def shooter_results(event,payload,**kwargs):
    sender_id = event['sender']['id']
    offset = int(payload.get('offset', 0))
    payloads = payload['shooter_results']

    try:
        first_name = payloads['first_name']
    except:
        first_name = None
    try:
        last_name = payloads['last_name']
    except:
        last_name = None
    try:
        club = payloads['club']
    except:
        club = None

    if not first_name and not last_name and club:
        club_list_competitions(event,{'club':club})
        return

    shooter = get_results_shooter()

    workdata = pd.DataFrame()
    if last_name:
        data_last = shooter[shooter['last_name'] == last_name]
        check_unique_last_name = list(set(list(data_last['first_name'])))
        if len(check_unique_last_name) == 1:
            workdata = data_last

    if first_name:
        data_first = shooter[shooter['first_name'] == first_name]
        check_unique_first_name = list(set(list(data_first['last_name'])))
        if len(check_unique_first_name) == 1:
            workdata = data_first
        else:
            data_first_last = data_first[data_first['last_name'] == last_name]
            check_unique_last_name2 = list(set(list(data_first_last['first_name'])))
            if len(check_unique_last_name2) == 1:
                workdata = data_first_last

    if workdata.empty:
        if club and last_name:
            data_club = shooter[(shooter['team_full'] == club) & (shooter['last_name']== last_name)]
            check_unique_club = list(set(list(data_club['first_name'])))
            if len(check_unique_club) == 1:
                workdata = data_club
    if workdata.empty:
        if club and first_name:
            data_club = shooter[(shooter['team_full'] == club) & (shooter['first_name'] == first_name)]
            check_unique_club = list(set(list(data_club['last_name'])))
            if len(check_unique_club) == 1:
                workdata = data_club
            else:
                send_text(sender_id,
                      'Ich habe irgendwie mehr als eine Person gefunden... Kannst du den Namen spezifizieren?')
                return
    try:
        num_league = 4
        if workdata.shape[0]<4:
            num_league = workdata.shape[0]
    except:
        send_text(sender_id,
                  'Mhmm, den Namen kenne ich noch nicht. Zumindest hat er noch keinen Wettkampf geschossen!')
        return

    info_person = payloads
     #   {}
    #info_person['first_name'] =  workdata['first_name'].iloc[0]
    #info_person['last_name'] =  workdata['last_name'].iloc[0]
    try:
        club = workdata['team_full'].iloc[0]
    except:
        club = club

    if workdata.shape[0] - (offset + num_league) == 1:
        num_league = 3
    elements = []
    for index in range(offset, offset + num_league):
        data = shooter[(shooter['comp_id'] == workdata['comp_id'].iloc[index]) & (
                        shooter['position'] == workdata['position'].iloc[index])]
        person = data[data['team_full'] == club]
        oponent = data[data['team_full']!= club]

        info_dict = {'first_name': oponent['first_name'].iloc[0],
                     'last_name': oponent['last_name'].iloc[0]

                     }
        sbtle = "Position {position}".format(position = person['position'].iloc[0])

        if person['shoot_off'].iloc[0].strip() != '':
            sbtle += " -- Entscheidung im Stechen: {person}:{oponent}".format(
                person = person['shoot_off'].iloc[0],
                oponent = oponent['shoot_off'].iloc[0]
            )

        button_comp = [button_postback("Info {first_name} {last_name}".format(
                first_name = oponent['first_name'].iloc[0],
                last_name = oponent['last_name'].iloc[0]
            ), {'shooter_results': info_dict})]

        list_text_title  = "%d : %d --  %s %s (%s)" % (person['result'].iloc[0], oponent['result'].iloc[0],
                                    oponent['first_name'].iloc[0], oponent['last_name'].iloc[0],
                                    oponent['team_full'].iloc[0])
        elements.append(
            list_element(
                list_text_title,
                subtitle=sbtle,
                buttons=button_comp
                # image_url=candidate.get('img') or None
            )
        )

    if workdata.shape[0] - offset > num_league:
        button = button_postback("Wettkämpfe %d - %d" % (offset + num_league + 1, (offset + 2 * num_league)),
                                 {'shooter_results': info_person,
                                  'offset': offset + num_league})
    else:
        button = button_postback(club, {'club_info': club})

    if offset == 0:
        pd.to_numeric(workdata['result'], errors='ignore')
        pd.to_numeric(workdata['point'], errors='ignore')
        avg = workdata['result'].mean()
        adj = ''
        if avg > 390:
            adj = 'gute'
            if avg> 393:
                adj = 'extrem gute'
                if avg > 395:
                    adj = 'starke'
                    if avg > 396:
                        adj = 'wahnsinnige'
                        if avg > 397:
                            adj = 'unglaubliche'
                            if avg > 398:
                                adj = 'galaktische'
                                if avg > 399:
                                   adj = 'unmenschliche'
                                else:
                                    adj = 'passable'


        text_first_response = '{first_name} {last_name} startet diese Saison für {club}.\n' \
                              '{competitions} Wettkämpfe, davon {wins} gewonnen.\n' \
                              'Liga-Ø: {adj} {avg_result}\n\n' \
                              'Hier die bisherigen Begegnungen:'.format(
            first_name = workdata['first_name'].iloc[0],
            last_name = workdata['last_name'].iloc[0],
            competitions=workdata.shape[0],
            wins = sum(workdata['point']),
            avg_result = avg,
            adj = adj,
            club = workdata['team_full'].iloc[0]
        )
        send_text(sender_id, text_first_response

                  )
    if workdata.shape[0] != 1:
        send_list(sender_id, elements, button=button)
    else:
        send_buttons(sender_id,
                     list_text_title+'\n'+sbtle,
                     buttons = [button_comp[0],
                         button
                      ]
                     )






#################################
def buli_live_api(event, parameters, **kwargs):

    buli_live(event)


######################################
def buli_live(event,**kwargs):
    sender_id = event['sender']['id']

    links = get_meyton(hrefs = True)
    options = [quick_reply('Aktualisieren', ['buli_live'])]

    for key, href in links.items():

        live = get_meyton_results(href)

        try:
            if not live.empty:
                #calculate points
                data = live['points'].dropna()
                home_points = 0
                guest_points = 0
                for row in data.iteritems():
                    home_points += int(list(row)[1].split(':')[0].strip())
                    guest_points += int(list(row)[1].split(':')[1].strip())

                reply_positions = ""
                for index in range(0, 5):
                    reply_positions += '#{position}:   {points_home}  :  {points_guest}  \n'.format(
                        position=str(index + 1),
                        points_home=live['result'].iloc[(2 * index)],
                        points_guest=live['result'].iloc[(2 * index + 1)]
                    )  # ,

                reply_overview = "{fight}\n{home} : {guest}\n{home_points}:{guest_points}".format(
                            fight = live['fight'].iloc[0],
                              home = live['home_team'].iloc[0],
                              guest = live['guest_team'].iloc[0],
                              home_points = home_points,
                              guest_points = guest_points
                        )



                send_text(sender_id, reply_overview+'\n'+ reply_positions
                       )


                reply_shooters = ""
                for index in range(0, 5):
                    reply_shooters += '#{position}: {home} : {guest}\n'.format(
                        position=str(index + 1),
                        home=live['name'].iloc[(2 * index)],

                        guest=live['name'].iloc[(2 * index + 1)],

                    )

                payload_reply = {'reply_shooters': reply_shooters,
                                'reply_positions': reply_positions,
                                'href': href}

                quickreplyname = live['home_team'].iloc[0] + ':' + live['guest_team'].iloc[0]

                options.append(
                        quick_reply(quickreplyname, {'buli_live_competition': payload_reply})
                    )

        except:
            send_text(sender_id,'Zur Zeit kein Wettkampf')


    send_text(sender_id,'Aktualisieren. Oder schau dir die Schützen im Detail an.', quick_replies = options)





def buli_live_competition(event,payload,**kwargs):
    sender_id = event['sender']['id']
    payload_reply = payload['buli_live_competition']


    send_text(sender_id,
                  payload_reply['reply_shooters'],
                  quick_replies = [quick_reply('Aktualisieren', ['buli_live'])
               ]
                  )


def shooter_live(event,payload,**kwargs):
    sender_id = event['sender']['id']
    payload_reply = payload['shooter_live']



    send_text(sender_id,
             payload_reply['reply_shooters'],
              quick_replies=[quick_reply('Aktualisieren',['buli_live'])]
              )
