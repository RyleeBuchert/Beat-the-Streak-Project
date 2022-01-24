import statsapi as mlb
import pybaseball as pyb
import pandas as pd


def inning_converter(innings_pitched):
    ip_string = str(innings_pitched)

    if ip_string[len(ip_string)-2:len(ip_string)] == '.1':
        ip = int(innings_pitched) + 0.333333
    elif ip_string[len(ip_string)-2:len(ip_string)] == '.2':
        ip = int(innings_pitched) + 0.666667
    else:
        ip = innings_pitched

    return ip


def get_hits_nine(pitcher_name):
    pitcher_data = pd.read_csv("Data Files/pitcher_data.csv")

    try:
        index = pitcher_data[pitcher_data['Name'] == pitcher_name].index[0]
        hits = pitcher_data['H'][index]
        ip = inning_converter(pitcher_data['IP'][index])

        hits_nine = (hits / ip) * 9.0

        return hits_nine
    except IndexError:
        return 'NA'


def get_player_data(player_name):
    player = mlb.lookup_player(lookup_value=player_name, season=2019)
    player_data = mlb.player_stats(personId=player[0]['id'], type="career")
    return player_data


# data = pd.DataFrame(pyb.pitching_stats_range(start_dt='2018-01-01', end_dt='2020-12-31'))
# print(data.head())
#
# data.to_csv('pitcher_data.csv')


def get_team_data(team, year):
    team_lookup = mlb.lookup_team(team)
    team_id = team_lookup[0]['id']
    team_file_code = team_lookup[0]['fileCode']

    date_dict = {
        "2018_start": "03/28/2018",
        "2018_end": "09/30/2018",
        "2019_start": "03/27/2019",
        "2019_end": "09/29/2019",
        "2020_start": "07/23/2020",
        "2020_end": "09/27/2020"
    }

    start_string = format(f'{year}_start')
    end_string = format(f'{year}_end')
    team_data = mlb.schedule(start_date=date_dict[start_string], end_date=date_dict[end_string], team=team_id)

    game_id_list = []
    game_date_list = []
    home_list = []
    opposing_pitcher_list = []
    opposing_team_list = []

    for i in range(0, len(team_data)):
        if team_data[i]['status'] == 'Final' or team_data[i]['status'] == 'Completed Early: Rain':
            game_id_list.append(team_data[i]['game_id'])
            game_date_list.append(team_data[i]['game_date'])

            if team_data[i]['home_name'] == team_lookup[0]['name']:
                home_list.append(1)
                opposing_pitcher_list.append(team_data[i]['away_probable_pitcher'])
                opposing_team_list.append(team_data[i]['away_name'])

            else:
                home_list.append(0)
                opposing_pitcher_list.append(team_data[i]['home_probable_pitcher'])
                opposing_team_list.append(team_data[i]['home_name'])

        if len(game_id_list) == 162:
            break

    team_opp_pitcher_data = pd.DataFrame()
    team_opp_pitcher_data['game_id'] = game_id_list
    team_opp_pitcher_data['game_date'] = game_date_list
    team_opp_pitcher_data['home'] = home_list
    team_opp_pitcher_data['opp_pitcher'] = opposing_pitcher_list
    team_opp_pitcher_data['opp_team'] = opposing_team_list

    # opp_pitcher_hand = []
    # for i in range(0, 162):
    #     opp_pitcher_hand.append(get_pitcher_hand(nyy.iloc[i, 3]))
    # team_opp_pitcher_data['opp_pitcher_hand'] = opp_pitcher_hand

    opp_hits_nine = []
    for i in range(0, 162):
        opp_hits_nine.append(get_hits_nine(team_opp_pitcher_data.iloc[i, 3]))
    team_opp_pitcher_data['opp_hits_nine'] = opp_hits_nine

    team_opp_pitcher_data.to_csv(format(f'{team_file_code}_{year}.csv'))


get_team_data(team='mets', year=2019)
