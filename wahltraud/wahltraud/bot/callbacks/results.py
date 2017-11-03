import logging
import operator
import pandas as pd
import locale
from time import sleep


from backend.models import FacebookUser, ShooterResults, CompetitionStatus

from ..fb import send_buttons, button_postback, send_text, send_attachment, send_list, list_element, quick_reply
from ..data import (by_uuid, get_dates, get_results_team, get_results_shooter,
                    get_tables, get_club_info_weapon_buli_region,get_setlist, get_live_results, get_team_avg)
from .parser import get_meyton, get_meyton_results
from .simple import club_info
import datetime

#enable logging
logger = logging.getLogger(__name__)
locale.setlocale(locale.LC_NUMERIC, 'de_DE.UTF-8')

def best_shooter_api(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')
    league = parameters.get('league')
    weapon = parameters.get('weapon')
    region = parameters.get('region')

    if weapon == 'Luftgewehr':
        weapon = 'LG'
    if weapon == 'Luftpistole':
        weapon = 'LP'

    try:
        if not weapon:
            if FacebookUser.objects.get(uid=sender_id).rifle:
                weapon = 'LG'
            elif FacebookUser.objects.get(uid=sender_id).pistole:
                weapon = 'LP'
    except:
        send_text(sender_id, 'Gewehr oder Pistole?')
        return

    if not club and not league and not weapon and not region:
        send_text(sender_id,'So insgesamt??? Gewehr oder Pistole?')
        return

    info = {
        'club' : club,
        'league' : league,
        'weapon': weapon,
        'region': region,
        'best': False
    }

    best_shooter(event,{'best_shooter': info})





def best_shooter(event, payload, **kwargs):
    sender_id = event['sender']['id']
    info = payload['best_shooter']
    club = info['club']
    league = info['league']
    weapon = info['weapon']
    region = info['region']
    best = info['best']

    results = get_setlist()
    if weapon:
        results = results[results['weapon'] == weapon]

    if not club and not league and not region:
        results = results[results['weapon']==weapon]
    elif not club and not region:
        results = results[results['league']== league]
        send_text(sender_id,'Hier die Besten aus der '+league+':')
    elif not club and not league:
        results = results[results['region']== region]
        send_text(sender_id,'Hier die Besten aus der Region '+region+':')
    elif not club:
        if region in ['West','Ost','Südwest']:
            league = '2.BuLi'
        results = results[(results['region']==region) & (results['league']==league)]
        send_text(sender_id,'Hier die Besten aus der der {league} {region}:'.format(
            league = league,
            region= region
        ))

    elif club:
        results = results[results['club_short']==club]
    if results.empty:
        send_text(sender_id, 'Mhmm, hier ist wohl was schief gelaufen.')


    if best:
        single = results.sort_values(by=['best'], ascending=False)

        reply_single = ''
        best_result = single['best'].max()
        single_final = single[single['best'] == best_result]
        for index,row in single_final.iterrows():
            reply_single += "{first_name} {last_name} - {team} - {buli}\n".format(
                first_name=row['first_name'],
                last_name = row['last_name'],
                team = row['club_short'],
                buli=row['buli']
            )
        reply =  'Im {weapon} stehen {best_result} Ringe als Saisonbestleistung in den Büchern. Folgende Schützen haben dieses Ergebnis bereits erziehlt:\n\n'.format(
            weapon=weapon,
                      best_result=best_result,
                      ) + reply_single
        info['best'] = False
        quick = [quick_reply('Bestes Ø-Ergebnis',{'best_shooter': info})]

    else:
        avg = results.sort_values(by=['avg'], ascending=False)
        reply_avg = ''
        max_comp = avg['numer_of_comps'].max()
        #this formula takes into account how many falues are counted
        fail = sum([1/x for x in range(2,max_comp)])+0.5
        avg_final = avg[avg['numer_of_comps']>(max_comp-fail)].iloc[0:7]
        for index,row in avg_final.iterrows():
            reply_avg += "Ø {avg} ({comp}) - {first_name} {last_name} - {team} - {buli}\n\n".format(
                first_name=row['first_name'],
                last_name = row['last_name'],
                team = row['club_short'],
                buli=row['buli'],
                comp = row['numer_of_comps'],
                avg = row['avg']
            )
        reply = 'Hier die Top Schützen {weapon}:\n\n'.format(
            weapon='mit dem LG' if weapon=='LG' else 'mit der Luftpistole',
                                ) +reply_avg+'(In Klammern steht die Anzahl absolvierter Wettkämpfe.)'
        info['best'] = True
        quick = [quick_reply('Bestes Einzelergebnis?', {'best_shooter': info})]

    send_text(sender_id,
              reply,
              quick_replies = quick
              )







def table_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    buli = parameters.get('league') # first or second BuLi
    region =  parameters.get('region')
    weapon = parameters.get('weapon')


    if not weapon:
        try:
            if not weapon:
                if FacebookUser.objects.get(uid=sender_id).rifle:
                    weapon = 'LG'
                elif FacebookUser.objects.get(uid=sender_id).pistole:
                    weapon = 'LP'
        except:
            weapon = None



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
                      'Nord oder Süd ist hier die Frage...',
                      quick_replies = [
                          quick_reply('Nord',{'table_payload': payload_north}),
                          quick_reply('Süd', {'table_payload': payload_south})

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
        during_comp = False
        if table_league['comps'].max() != table_league['comps'].min():
            during_comp = True
        send_text(sender_id, 'Ich präsentiere die Tabelle der \n\n{buli} {region} - {weapon}\n\n{wording} {nter}. Wettkampftag:'.format(
            buli=buli,
            weapon=weapon,
            region=region,
            nter = int(table_league['comps'].max()),
            wording = 'am' if during_comp == True else 'nach dem'
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



    results = get_results_team()


    results_club = results[(results['guest_team'] == club) | (results['home_team'] == club)]


    num_league = 4

    if results_club.shape[0] - (offset + num_league) == 1:
        num_league = 3
    if results_club.shape[0] - (offset + num_league) < 1:
        num_league = 4 + (results_club.shape[0] - (offset + num_league))

    elements = []
    for index in range(offset, offset + num_league):
        data = results_club.iloc[index]

        if data['home_points'] + data['guest_points'] != 0:
            title = '#{index} - {fl_home} {home} : {guest} {fl_guest} '.format(
                index=index + 1,
                home=data['home_team'],
                guest=data['guest_team'],
                fl_home='🎉' if data['home_points'] > 2 else '',
                fl_guest='🎉' if data['guest_points'] >2  else ''
            )
            sbtle = "%d : %d --  %d : %d" % (data['home_points'], data['guest_points'],
                                             data['home_result'], data['guest_result'])
            button_comp = [button_postback("Paarungen", {'competition_results':  data['comp_id']})]
        else:
            title = '#{index} - {home} : {guest}'.format(
                index=index + 1,
                home=data['home_team'],
                guest=data['guest_team']
            )
            date = data['date'].strftime("%d.%m.%Y")
            sbtle = date+', '+ data['time'] + ' - Ausrichter: ' + data['host']
            club_oponent = data['guest_team']
            if club_oponent == club:
                club_oponent = data['home_team']
            button_comp = [button_postback('Info Gegner', {'club_info': club_oponent})]

        elements.append(
            list_element(
                title = title,
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

        text_reply = '{club} liegt derzeit auf Platz {pos} der {liga} {region}\n\nTeampunkte: {win} : {los}\nEinzelpunkte: {winE} : {losE}'.format(
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
            text += "    💣 - {home} : {guest}".format(home = home['shoot_off'],guest=guest['shoot_off'])

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
        text_first = '{home_points}-{fl_home}- {home}\nvs.\n{guest_points}-{fl_guest}- {guest}'.format(
            home = results_club['team_full'].iloc[0],
            guest = results_club['team_full'].iloc[1],
            home_points =total_points_home,      # goal[0:total_points_home],
            guest_points =5 - total_points_home , # goal[0:(5- total_points_home)]
            fl_home = '🎉' if total_points_home >=3 else '  ',
            fl_guest = '🎉' if (5-total_points_home)>=3else '  '
        )


        if len(results_club['shoot_off'].unique()) != 1:
            text_first += "\nPunkte durch Stechen: {home}{guest}".format(
                home = goal[0:results_club[(results_club['shoot_off']!=' ') & (results_club['home']== True)]['point'].sum()],
                guest = goal[0:results_club[(results_club['shoot_off']!=' ') & (results_club['home']== False)]['point'].sum()]
            )



        send_text(sender_id,text_first)

    send_list(sender_id, elements, button=button)




def results_api(event, parameters, **kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')
    club1 = parameters.get('clubs1')

    if club1 and club != club1:
        results = get_results_team()
        if club1:
            try:
                data = results[(results['guest_team_short'] == club) & (results['home_team_short'] == club1)].iloc[0]
            except:
                try:
                    data = results[(results['guest_team_short'] == club1) & (results['home_team_short'] == club)].iloc[0]
                except:
                    info0 = get_club_info_weapon_buli_region(club)
                    info1 = get_club_info_weapon_buli_region(club1)
                    buttons = []
                    for info in [info0,info1]:
                        if len(info) == 2:
                            buttons.append(button_postback(info[0]['club'],{'club_list_competitions': info[0]}))
                            buttons.append(button_postback(info[1]['club'],{'club_list_competitions': info[1]}))
                        else:
                            buttons.append(button_postback(info['club'],{'club_list_competitions': info}))

                    send_buttons(sender_id,
                                 "Diese Wettkampf-Paarung find ich nicht in meinem Archiv.",
                                 buttons = buttons)
                    return
        if data['guest_result'] == 0:
            text = """Der Wettkampf zwischen {club} und {club1} in der {league} hat nocht nicht stattgefunden.
                
                   Termin: {date}, {time} 
                   Ausrichter: {host}""".format(
                club = data['home_team'],
                club1 = data['guest_team'],
                league = data['league'],
                date = data['date'].strftime("%d.%m.%Y"),
                time = data['time'],
                host = data['host']
            )
            info = {'club':data['home_team'],
                     'club1': data['guest_team']
                    }
            send_buttons(sender_id,
                         text,
                         buttons = [button_postback('Team-Vergleich',
                                         {'club_comparison': info
                                          }
                                         )]
                         )
            return
        else:
            comp_id = data['comp_id']


        competition_results(event,{'competition_results': comp_id})

    else:
        results_club(event, {'results_club': club})





def club_comparison(event,payload,**kwargs):
    sender_id = event['sender']['id']
    club = payload['club_comparison']['club']
    club1 = payload['club_comparison']['club1']

    avg = get_team_avg()
    c = avg[avg['club'] == club].iloc[0]
    c1 = avg[avg['club'] == club1].iloc[0]

    reply = '{club}\n       vs.\n             {club1}\n\n'.format(club = club,
                                          club1 = club1)
    reply +='Tabelle: {h_rank}. vs. {g_rank}.\nØ-Total: {h_result} vs. {g_result}\n\nØ-Ringe an Position:\n'.format(
        h_rank = int(c['rank']),
        g_rank = int(c1['rank']),
        h_result = c['avg_result'],
        g_result = c1['avg_result']
    )
    home = 0
    guest = 0
    shoot_off = []
    for i in range(1,6):
        if c[i]> c1[i]:
            home +=1
        elif c1[i] > c[i]:
            guest +=1
        else:
            shoot_off.append(i)
            if c1['avg_result']>c['avg_result']:
                guest +=1
            else:
                home +=1

        reply += '#{i} - {h_avg} : {g_avg}\n'.format(
            i = i,
            h_avg = c[i],
            g_avg = c1[i]
        )
    send_text(sender_id,'Ein Vergleich zur Begegnung:')
    send_text(sender_id,reply)

    send_text(sender_id,
              'Mein Tip: {club} {verb} mit {points} gegen {club1}'.format(
                  club = club,
                  club1 = club1,
                  verb = 'gewinnt' if (home >= 3) else 'verliert',
                  points = str(home) + ' : ' + str(guest)
              ))







def results_club(event, payload, **kwargs):
    sender_id = event['sender']['id']
    club = payload['results_club']

    club_repl = club
    for ending in [' II', ' I', ' 2', 'FSG']:
        if club_repl.endswith(ending):
            club_repl = club_repl.replace(ending, '').strip()

    infoall = get_club_info_weapon_buli_region(club_repl)

    if len(infoall) == 2:
        club_info(event,{'club_info':club})
    else:
        club_list_competitions(event,{'club_list_competitions': infoall})




def shooter_results_api(event, parameters, **kwargs):
    first_name = parameters.get('first_name')
    last_name = parameters.get('last_name')
    club = parameters.get('clubs')

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


    if last_name:
        data_last = shooter[shooter['last_name'] == last_name]
        check_unique_last_name = list(set(list(data_last['first_name'])))
        if len(check_unique_last_name) == 1:
            workdata = data_last
        elif club:
            data_club = shooter[(shooter['team_short'] == club) & (shooter['last_name'] == last_name)]
            check_unique_club = list(set(list(data_club['first_name'])))
            if len(check_unique_club) == 1:
                workdata = data_club



    if first_name:
        data_first = shooter[shooter['first_name'] == first_name]
        check_unique_first_name = list(set(list(data_first['last_name'])))
        if len(check_unique_first_name) == 1:
            workdata = data_first
        elif last_name:
            data_first_last = data_first[data_first['last_name'] == last_name]
            check_unique_last_name2 = list(set(list(data_first_last['first_name'])))
            if len(check_unique_last_name2) == 1:
                workdata = data_first_last
        elif club:
            data_club = shooter[(shooter['team_short'] == club) & (shooter['first_name'] == first_name)]
            check_unique_club = list(set(list(data_club['last_name'])))
            if len(check_unique_club) == 1:
                workdata = data_club
            else:
                send_text(sender_id,
                          'Ich habe irgendwie mehr als eine Person gefunden... Kannst du den Namen spezifizieren?')
                return

    #if workdata.empty:
    #    send_text(sender_id,'Ich konnte den Namen nicht eindeutig zuordnen...')
    #    return

    try:
        num_league = 4
        if workdata.shape[0]<4:
            num_league = workdata.shape[0]
    except:
        set_list = get_setlist()
        if last_name and first_name:
            sets = set_list[(set_list['last_name']== last_name) & (set_list['first_name'] == first_name)]
        elif last_name and club:
            sets = set_list[(set_list['last_name'] == last_name) & (set_list['club_short'] == club)]
        elif first_name and club:
            sets = set_list[(set_list['first_name'] == first_name) & (set_list['club_short'] == club)]
        elif last_name:
            sets= set_list[(set_list['last_name'] == last_name)]
        elif first_name:
            sets = set_list[(set_list['first_name'] == first_name)]

        if sets.empty:
            reply = "Sorry, aber ich finde nichts und niemanden der zu deiner Suche passt."
            send_text(sender_id,reply)
            return

        quicks = []
        if offset==0 and sets.shape[0]>1:
            send_text(sender_id, "Mhmm, ich habe {number} Schützen gefunden, die auf deine Anfrage passen. Meinst du...".format(
                number = sets.shape[0]
            ))

        row = sets.iloc[offset]
        comps = 11-(row == 0).astype(int).sum()
        reply = "{first_name} {last_name} schießt für {club} und hat {shot} Wettkämpfe in der aktuellen Saison bestritten.\n\n{fixsub} mit einem Ø von {avg}".format(
            first_name = row['first_name'],
            last_name = row['last_name'],
            club = row['club_short'],
            shot = 'noch keine' if comps<= 0 else comps,
            fixsub = 'Stammschütze' if row['fixed'] == True else 'Ersatzschütze',
            avg = row['avg']
        )

        if sets.shape[0]>1:
            if comps >0:
                shooter_info = {'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'club': row['club_short']}
                quicks.append(quick_reply('Genau! Mehr Info bitte!',{'shooter_results': shooter_info}))
            quicks.append(quick_reply('Nicht richtig.',{'shooter_results': payloads, 'offset': offset+1}))

        quicks.append(quick_reply('Setzliste '+row['club_short'], {'setlist_payload':row['club_short']}))

        send_text(sender_id,
                  reply,
                  quick_replies=quicks

                  )
        return

    info_person = payloads
     #   {}
    #info_person['first_name'] =  workdata['first_name'].iloc[0]
    #info_person['last_name'] =  workdata['last_name'].iloc[0]
    try:
        club = workdata['team_full'].iloc[0]
    except:
        club = club

    more_clubs = False
    if len(list(set(list(workdata['team_full'])))) > 1:
        more_clubs = True


    if workdata.shape[0] - (offset + num_league) == 1:
        num_league = 3
    elements = []
    for index in range(offset, offset + num_league):
        data = shooter[(shooter['pos_id'] == workdata['pos_id'].iloc[index])
                        # & (shooter['position'] == workdata['position'].iloc[index])
             ]
        person = data[data['team_full'] == club]
        oponent = data[data['team_full']!= club]

        info_dict = {'first_name': oponent['first_name'].iloc[0],
                     'last_name': oponent['last_name'].iloc[0]

                     }
        sbtle = "Position {position}".format(position = person['position'].iloc[0])

        if person['shoot_off'].iloc[0].strip() != '':
            sbtle += " -💣- {person}:{oponent}".format(
                person = person['shoot_off'].iloc[0],
                oponent = oponent['shoot_off'].iloc[0]
            )
        if more_clubs:
            sbtle += " -- {club}".format(
                club = person['team_full'].iloc[0]
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
        best = workdata['result'].max()
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
        send_text(sender_id,'Hier ein paar Infos zu {first_name} {last_name}:'.format(
            first_name=person['first_name'].iloc[0],
            last_name=person['last_name'].iloc[0],
        ))


        text_first_response = '{club}\n\n' \
                              '{competitions} Wettkämpfe\n{wins} gewonnen\n' \
                              'Saison-Bestleistung: {best} \nLiga-Ø: {adj} {avg_result}\n\n' \
                              'Hier die bisherigen Begegnungen:'.format(
            competitions=workdata.shape[0],
            wins = sum(workdata['point']),
            avg_result = avg,
            best = best,
            adj = adj,
            club = workdata['team_short'].iloc[0]
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


def setlist_api(event,parameters,**kwargs):
    sender_id = event['sender']['id']
    club = parameters.get('clubs')

    if not club:
        send_text(sender_id, 'Von welchem Verein soll ich dir die Setzliste zeigen?')
        return
    setlist_payload(event,
                    {'setlist_payload': club}
                    )


### Alte Setzliste vielleicht zu bestimmten tagen
'''
def setlist_payload(event,payload,**kwargs):
    sender_id = event['sender']['id']
    club = payload['setlist_payload']

    setlist = get_setlist()
    set_club = setlist[(setlist['club_short'] == club) | (setlist['club'] == club)]





    clubs = list(set(list(set_club['club'])))
    for i in range(1, 13):
        if sum(set_club[str(i)]) != 0:
            day = i
        else:
            break


    if len(clubs) == 1:
        reply1 = 'Hier die Setzliste nach dem {day}. Wettkampf von {club}:'.format(
            club=club,
            day= day
                 )
        send_text(sender_id, reply1)

        reply =''
        for index, row in set_club.iterrows():

            summe =  sum([row[str(i)] for i in range(1, day)]) / (day - 1)
            avg = float(row['avg'].replace(',', '.'))
            tendency = '    ' if (row[str(day)] == 0) else ('↘' if (summe > avg) else ('➡' if ((summe == avg) or summe == 0) else '↗'))


            reply += "({comps}) Ø {avg} {tendency} - {first_name}. {last_name}\n".format(
                avg=row['avg'],
                first_name=row['first_name'][0],
                last_name=row['last_name'],
                tendency=tendency,
                comps = sum(x is not 0 for x in [row[str(i)] for i in range(1,11)])
            )
        reply += "Für die Ergebnisse der einzelnen Schützen gib Ihren Namen und den Verein ein."

        send_text(sender_id,reply, [quick_reply('Blauer Pfeil?',['blue_arrows'])]
                  )


    elif len(clubs) == 2:
        send_buttons(sender_id,
                    'Die Setzliste welcher Mannschaft genau?',
                    [button_postback(clubs[0],{'setlist_payload': clubs[0]}),
                     button_postback(clubs[1],{'setlist_payload': clubs[1]})
                    ]
                    )
    else:
        send_text(sender_id, 'Kein Team mit dem Namen '+ club+' gefunden')
'''

def setlist_payload(event,payload,**kwargs):
    sender_id = event['sender']['id']
    club = payload['setlist_payload']

    set_list = get_setlist()
    shooter = get_results_shooter()

    set_club = set_list[(set_list['club_short'] == club) | (set_list['club'] == club)]

    clubs = list(set(list(set_club['club'])))

    if len(clubs) >1 and len(clubs)<=3:
        buttons = []
        for el in clubs:
            buttons.append(
                button_postback(el, {'setlist_payload': el})
            )
        send_buttons(sender_id,
                     'Die Setzliste welcher Mannschaft genau?',
                     buttons = buttons
                     )
    elif len(clubs) <=0 or len(clubs)>3:
        send_text(sender_id,
                  'Mhmm, da ist was schief gegangen...'
                  )
    else:
        final_list = []
        number = []
        for index, row in set_club.iterrows():
            first = row['first_name']
            last = row['last_name']
            shooter_pers = shooter[(shooter['first_name'] == first) & (shooter['last_name'] == last) & (shooter['team_full']==club)]
            temp = {'first_name': first,
                    'last_name': last
                    }
            if not shooter_pers.empty:
                avg = 0
                counter = 0
                alle = []
                temp['comps'] = shooter_pers.shape[0]

                for index2, row2 in shooter_pers.iterrows():
                    if row2['counter'] not in number:
                        number.append(row2['counter'])
                    temp[row2['counter']] = row2['result']
                    alle.append(row2['result'])
                    avg += float(row2['result'])
                    counter += 1
                    temp['avg' + str(row2['counter'])] = round(avg / (counter), 2)
                temp['avg'] = round(avg / (counter), 2)
                temp['best'] = max(alle)
                temp[100] = float(row['avg'].replace(',', '.'))
            else:
                temp['avg'] = float(row['avg'].replace(',', '.'))
                temp[100] = float(row['avg'].replace(',', '.'))

            final_list.append(temp)
        king = pd.DataFrame(final_list)
        king = king.sort_values(by=['avg', 'comps'], ascending=False)
        king.head()
        col = {}
        number = sorted(number)
        for i, val in enumerate(number):
            col[val] = i + 1
            col['avg' + str(val)] = 100 + i + 1
        king = king.rename(columns=col)
        king = king.fillna(0)
        num = len(number)
        king['trend'] = king[100]
        king['trend'] = -99
        trend = -99 # set, such hat nothing happend earlier
        for index, row in king.iterrows():
            avg_ind = row[100 + num]
            if row[num] != 0:
                for i in range(1, 12):
                    if row[100 + num - 1] != 0 and num - i >= 0:
                        if avg_ind > row[100 + num - 1]:
                            trend = 1
                            break
                        elif avg_ind < row[100 + num - 1]:
                            trend = -1
                            break
                        else:
                            trend = 0
                            break
                king.loc[index, 'trend'] = trend
        reply1 = 'Hier die Setzliste nach dem {day}. Wettkampf von {club}:'.format(
            club=club,
            day = num
        )
        send_text(sender_id, reply1)

        reply = ''
        for index, row in king.iterrows():


            tendency = '    ' if (row['trend'] == -99) else (
            '↘' if (row['trend'] == -1) else ('➡' if ((row['trend']==0)) else '↗'))

            reply += "({comps}) Ø {avg} {tendency} - {first_name}. {last_name}\n".format(
                avg= locale.format('%.2f',row['avg']),
                first_name=row['first_name'][0],
                last_name=row['last_name'],
                tendency=tendency,
                comps=int(row['comps'])
            )
        reply += "Für die Ergebnisse der einzelnen Schützen gib Ihren Namen und den Verein ein."

        send_text(sender_id, reply, [quick_reply(' Was bedeuten ↗➡↘', ['blue_arrows'])]
                  )





def blue_arrows(event, **kwargs):
    sender_id = event['sender']['id']

    send_text(sender_id,
              """Die Schützen mit Pfeil haben den letzten Wettkampf mitgeschossen.\n
              Darüber hinaus signalisiert der Pfeil ob der Schütze beim letzten Wettkampf seinen Liga-Ø verbessern konnte oder nicht!""" \

              )


############
############
#################################
def buli_live_api(event, parameters, **kwargs):

    buli_live(event)


######################################
def buli_live(event,payload=None,**kwargs):
    sender_id = event['sender']['id']

    #links = get_meyton(hrefs = True)
    options = [quick_reply('Aktualisieren', ['buli_live'])]
    live_update_all = True
    if isinstance(payload,pd.DataFrame):
        live_results = [payload]
        live_update_all = False
    else:
        live_results = get_live_results()
    elements = []
    counter = -1
    for live in live_results:
        #live = get_meyton_results(href)
        counter += 1
        try:
            if not live.empty:
                #calculate points
                data = live['points'].dropna()
                home_points = 0
                guest_points = 0
                try:
                    for row in data.iteritems():
                        home_points += int(list(row)[1].split(':')[0].strip())
                        guest_points += int(list(row)[1].split(':')[1].strip())
                except:
                    home_points = 0
                    guest_points = 0

                fight = live['fight'].iloc[0]

                reply_positions = ""
                sbtl = ''
                for index in range(0, 5):
                    res_home = live['result'].iloc[(2 * index)]
                    res_guest = live['result'].iloc[(2 * index + 1)]
                    try:
                        point_home = int(live['points'].iloc[(2* index +1)].split(':')[0].strip())
                        point_guest = int(live['points'].iloc[(2* index +1)].split(':')[1].strip())
                    except:
                        point_home = 0
                        point_guest = 0

                    home_series = ''
                    guest_series = ''
                    for ser in live['series'].iloc[(2* index)]:
                        home_series += ser if (int(ser)>0 and int(ser)!= 100) else ( '💯'  if int(ser)== 100 else '__')
                        home_series += ' '
                    home_series = home_series[:-1]
                    for ser in live['series'].iloc[(2* index+1)]:
                        guest_series += ser if (int(ser)>0 and int(ser)!= 100) else ( '💯'  if int(ser)== 100 else '__')
                        guest_series += ' '
                    guest_series = guest_series[:-1]
                    shoot_off_home = '     '
                    shoot_off_guest = '     '
                    shoot_off_sbtl = ''
                    if fight == 'Wettkampf ist beendet' and res_home == res_guest:
                        shoot_off_home = '💣 ' + str(live['shot_value'].iloc[(2 * index)] )
                        shoot_off_guest = '💣 ' + str(live['shot_value'].iloc[(2 * index+1)] )
                        shoot_off_sbtl = '('+str(live['shot_value'].iloc[(2 * index)] ) + ':' + str(live['shot_value'].iloc[(2 * index+1)])+')'
                    home_win = '🔸' if (point_home == 1) else '    '
                    guest_win = '🔸' if (point_guest == 1) else '    '
                    try:
                        name_home = live['name'].iloc[(2 * index)].split(', ')[1][0]+'. '+live['name'].iloc[(2 * index)].split(', ')[0]
                        name_guest = live['name'].iloc[(2 * index+1)].split(', ')[1][0]+'. '+live['name'].iloc[(2 * index+1)].split(', ')[0]
                    except:
                        name_home = live['name'].iloc[(2 * index)]
                        name_guest = live['name'].iloc[(2 * index+1)]

                    reply_positions += '{home_win}-{points_home}- {home}\n{shoot_off_home}   {home_series} \n{guest_win}-{points_guest}- {guest}\n{shoot_off_guest}   {guest_series}\n\n'.format(
                        position=str(index + 1),
                        points_home=res_home,
                        points_guest=res_guest,
                        home_win = home_win,
                        guest_win = guest_win,
                        shoot_off_home = shoot_off_home,
                        shoot_off_guest = shoot_off_guest,
                        home=name_home,
                        guest=name_guest,
                        home_series = home_series,
                        guest_series = guest_series
                    )

                    sbtl += '{home_win}{points_home}:{points_guest}{guest_win}{shoot_off}|'.format(
                        position=str(index + 1),
                        points_home=res_home,
                        points_guest=res_guest,
                        home_win = home_win,
                        guest_win = guest_win,
                        shoot_off = shoot_off_sbtl
                    )  


                reply_overview = "{home_win}-{home_points} - {home}\nvs.\n{guest_win}-{guest_points} - {guest}\n\n{status}  {fight}\n\n".format(
                              status = '⛔' if (fight == 'Wettkampf ist beendet') else ('✅' if (fight == 'Wettkampf') else '⚠'),
                              points = '' if fight == 'Wettkampf ist beendet' else (str(guest_points) + '  (Punkte - Hochrechnung)'),
                              fight =fight,
                              home = live['home_team'].iloc[0],
                              guest = live['guest_team'].iloc[0],
                              home_points = home_points,
                              guest_points = guest_points,
                              home_win = '🎉' if ((fight == 'Wettkampf ist beendet') and (home_points >2) ) else '   ',
                              guest_win = '🎉' if ( (fight == 'Wettkampf ist beendet') and (guest_points >2)) else '   '
                        )


                reply_shooters = ""
                for index in range(0, 5):
                    reply_shooters += '#{position}: {home} : {guest}\n'.format(
                        position=str(index + 1),
                        home=live['name'].iloc[(2 * index)],
                        guest=live['name'].iloc[(2 * index + 1)],

                    )

                payload_reply = {'reply_comp': reply_overview + '\n' + reply_positions,
                                }

                quickreplyname = live['home_team'].iloc[0] + ':' + live['guest_team'].iloc[0]

                options.append(
                        quick_reply(quickreplyname, {'buli_live_competition': payload_reply})
                    )

                if not live_update_all:  # final Ergebnis nach Wettkampf beendet
                    send_buttons(sender_id,
                                 reply_overview,
                                 buttons = [button_postback('Einzelergebnisse',
                                                            {'buli_live_competition': payload_reply})
                                     ])
                else:
                    #send_buttons(sender_id, reply_overview + '\n' + reply_positions,
                    #             [button_postback('Schützen anzeigen', {'buli_live_competition': payload_reply})])
                    title = "{status} - {home_win}{home} {home_points}:{guest_points} {guest}{guest_win}".format(
                              status = '⛔' if (fight == 'Wettkampf ist beendet') else ('✅' if (fight == 'Wettkampf') else ('❌' if (fight=='Zur Zeit kein Wettkampf')else ('💣' if ('Stechen' in fight ) else '⚠'))),
                              fight =fight,
                              home = live['home_team'].iloc[0],
                              guest = live['guest_team'].iloc[0],
                              home_points = home_points,
                              guest_points = guest_points,
                              home_win = '🎉' if ((home_points >2) and (fight == 'Wettkampf ist beendet')) else ' ',
                              guest_win = '🎉' if ((guest_points >2) and (fight == 'Wettkampf ist beendet')) else ' '
                        )


                    elements.append(
                        list_element(title = title,
                                     subtitle = sbtl ,
                                     buttons = [
                                         button_postback('Details',
                                                         {'buli_live_competition': payload_reply})
                                     ])
                    )

        except:
            options.append(quick_reply('Nächster Wettkampf?', ['next_event_payload_to_api']))
            town = ['Wieckenberg', 'Gölzau', 'Petersaurach']
            club = ['SV Wieckenberg', 'SV Gölzau','SV Petersaurach']
            elements.append(list_element(title = 'Zur Zeit kein Wettkampf in ' +town[counter] ,
                                         subtitle= 'Echt nicht, sorry',
                                         buttons = [
                                             button_postback('Partien in '+town[counter],
                                                             {'next_event': club[counter], 'host': True})
                                         ]
            ))
            nothing = '123'

    if live_update_all:
        if len(elements)==1:
            try:
                send_text(sender_id, reply_overview + '\n' + reply_positions)
                return
            except:
                send_text(sender_id,'Zur Zeit kein Wettkampf!.', quick_replies = options)
                return
        send_text(sender_id, 'Hier der Live-Überblick:\n✅/⛔ Wettkampf läuft/ist beendet\n⚠ - Probe; 💣 - Stechen\n❌ - Zur Zeit kein Wettkampf')
        send_list(sender_id,
              elements=elements,
              button=button_postback('Aktualisieren', ['buli_live']))





###############
def buli_live_competition(event,payload,**kwargs):
    sender_id = event['sender']['id']
    payload_reply = payload['buli_live_competition']


    send_text(sender_id,
                  payload_reply['reply_comp'],
                  quick_replies = [quick_reply('Aktualisieren', ['buli_live'])
               ]
                  )

##################
def shooter_live(event,payload,**kwargs):
    sender_id = event['sender']['id']
    payload_reply = payload['shooter_live']



    send_text(sender_id,
             payload_reply['reply_comps'],
              quick_replies=[quick_reply('Aktualisieren',['buli_live'])]
              )



def push_live_results():
    # check database and status
    live_results = get_live_results()

    if isinstance(live_results, list):
        for final in live_results:
            if isinstance(final, pd.DataFrame):
                try:
                    cid = final['cid'].iloc[0]
                    status = CompetitionStatus.objects.get(cid=cid)
                    if status.shoot_off and not status.shoot_off_shot:
                        reply = ''
                        rep = ''
                        pos = ''
                        point_home = 0
                        point_guest = 0
                        for index in range(0, 5):
                            res_home = final['result'].iloc[(2 * index)]
                            res_guest = final['result'].iloc[(2 * index + 1)]
                            point_home += int(final['points'].iloc[(2 * index + 1)].split(':')[0].strip())
                            point_guest += int(final['points'].iloc[(2 * index + 1)].split(':')[1].strip())
                            if res_home == res_guest:
                                pos += str(index+1) + rep
                                rep = ' und '
                        if point_home <=2 and point_guest <=2:
                            reply += '+++ STECHEN UM DEN SIEG +++\nIn der Paarung {home} gegen {guest} steht es derzeit {standing}. Der Sieg wird an Position {pos} im Stechen entschieden'.format(
                            home=final['home_team'].iloc[0],
                            guest=final['guest_team'].iloc[0],
                            standing = str(point_home) + ':' + str(point_guest),
                            pos = pos
                                )
                        else:
                            reply += 'In der Paarung {home} gegen {guest} steht es derzeit {standing}.Ein Stechen erfolgt an Position {pos}.'.format(
                                home=final['home_team'].iloc[0],
                                guest=final['guest_team'].iloc[0],
                                standing=str(point_home) + ':' + str(point_guest),
                                pos=pos
                            )
                        user_list = FacebookUser.objects.values_list('uid', flat=True)
                        for uid in user_list:
                            if FacebookUser.objects.get(uid=uid).pistole:
                                sender_id = uid
                                sender_id = "1642888035775604"
                                send_text(sender_id,reply,quick_replies = [quick_reply('Einzelergebnisse', {'buli_live' : final} ),
                                                                           quick_reply('Live-Ergebnis', ['buli_live'])] )
                                send_text(sender_id,uid)
                        CompetitionStatus.objects.filter(cid=cid).update(shoot_off_shot=True)
                    elif status.finished and not status.push:
                        user_list = FacebookUser.objects.values_list('uid', flat=True)
                        for uid in user_list:
                            if FacebookUser.objects.get(uid=uid).pistole:
                                test = 'ja'
                                #send_text(1642888035775604,'push raus an'+uid)
                                #event = {'sender':{'id':1642888035775604}}
                                uid = 1642888035775604
                                event = {'sender':{'id':uid}}
                                buli_live(event, payload=final)
                                #sleep(0.5)
                            #send_text(1642888035775604, 'live ergebnis von wettkampf beendet')
                        CompetitionStatus.objects.filter(cid=cid).update(push=True)
                    elif status.push:
                        test = 'nein'
                        #send_text(1642888035775604, 'already_send')
                except:
                    test = 'fail'
            else:
                #send_text(1642888035775604,final)
                return