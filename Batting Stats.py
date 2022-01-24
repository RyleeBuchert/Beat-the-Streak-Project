import statsapi as mlb
import pandas as pd
import pybaseball as pyb
import Baseball_Model
import requests
import time
from bs4 import BeautifulSoup
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)


def get_game_id_list(team, year):
    team_lookup = mlb.lookup_team(team)
    team_id = team_lookup[0]['id']

    date_dict = {
        "2016_start": "04/03/2016",
        "2016_end": "10/02/2016",
        "2017_start": "04/02/2017",
        "2017_end": "10/01/2017",
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
    for i in range(0, 3):
        if team_data[i]['status'] == 'Final' or team_data[i]['status'] == 'Completed Early: Rain':
            game_id_list.append(team_data[i]['game_id'])

    return game_id_list


def get_batter_list_game(game_id):
    batter_data = mlb.boxscore_data(game_id)

    batting_list = []
    for i in range(0, len(batter_data['home']['batters'])):
        player_lookup = mlb.player_stats(batter_data['home']['batters'][i], group="hitting", type="season")
        player_name = player_lookup.split()

        if len(player_name) == 5:
            first_name = player_name[0]
            last_name = player_name[2]
            last_name = last_name[0:len(last_name) - 1]
        elif len(player_name) == 6:
            first_name = player_name[0]
            last_name = player_name[3]
            last_name = last_name[0:len(last_name) - 1]
        else:
            first_name = player_name[0]
            last_name = player_name[2]
            last_name = last_name[0:len(last_name) - 1]

        name_string = format(f'{first_name} {last_name}')
        batting_list.append(name_string)

    return batting_list


def get_batting_data_game(game_id):
    game_data = mlb.boxscore_data(game_id)

    position_list = []
    player_id_list = []
    hits_list = []
    season_avg_list = []
    num_ab_list = []
    batting_spot_list = []

    for i in range(1, len(game_data['homeBatters'])):
        position_list.append(game_data['homeBatters'][i]['position'])
        player_id_list.append(game_data['homeBatters'][i]['personId'])
        hits_list.append(int(game_data['homeBatters'][i]['h']))
        season_avg_list.append(float(game_data['homeBatters'][i]['avg']))
        num_ab_list.append(int(game_data['homeBatters'][i]['ab']))

        if game_data['homeBatters'][i]['substitution']:
            spot = 'Sub'
            batting_spot_list.append(spot)
        elif not game_data['homeBatters'][i]['substitution']:
            spot = game_data['homeBatters'][i]['battingOrder'][0]
            batting_spot_list.append(spot)
        else:
            spot = 'NA'
            batting_spot_list.append(spot)

    game_id_list = [game_id] * len(position_list)

    batting_game_data = pd.DataFrame()
    batting_game_data['Game ID'] = game_id_list
    batting_game_data['Player ID'] = player_id_list
    batting_game_data['Position'] = position_list
    batting_game_data['Hits'] = hits_list
    batting_game_data['Season Avg'] = season_avg_list
    batting_game_data['AB'] = num_ab_list
    batting_game_data['Spot'] = batting_spot_list

    batting_game_data = batting_game_data.drop(batting_game_data[batting_game_data['Position'] == 'P'].index)
    batting_game_data = batting_game_data.drop(batting_game_data[batting_game_data['Spot'] == 'Sub'].index)
    batting_list = []

    for i in range(0, len(batting_game_data)):
        player_id = batting_game_data.iloc[i, 1]
        player_lookup = mlb.player_stats(player_id, group="hitting", type="season")
        player_name = player_lookup.split()

        if len(player_name) == 5:
            first_name = player_name[0]
            last_name = player_name[2]
            last_name = last_name[0:len(last_name) - 1]
        elif len(player_name) == 6:
            first_name = player_name[0]
            last_name = player_name[3]
            last_name = last_name[0:len(last_name) - 1]
        elif len(player_name) == 4:
            first_name = player_name[0]
            last_name = player_name[1]
            last_name = last_name[0:len(last_name) - 1]
        else:
            first_name = player_name[0]
            last_name = player_name[2]
            last_name = last_name[0:len(last_name) - 1]

        name_string = format(f'{first_name} {last_name}')
        batting_list.append(name_string)

    batting_game_data['Name'] = batting_list
    cols = batting_game_data.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    batting_game_data = batting_game_data[cols]

    multi_year_avg_list = []
    batter_hand_list = []
    for i in range(0, len(batting_game_data)):
        multi_year_avg_list.append(get_average(batting_game_data.iloc[i, 0]))
        batter_hand_list.append(get_batter_hand_v2(batting_game_data.iloc[i, 0]))
    batting_game_data['Multi-Year Avg'] = multi_year_avg_list
    batting_game_data['Bats'] = batter_hand_list

    return batting_game_data


def get_batting_data_season(team, year):
    game_id_list = get_game_id_list(team, year)

    game_list = []
    for game in game_id_list:
        game_list.append(get_batting_data_game(game))

    season_batting_data = pd.concat(game_list)

    return season_batting_data


def combine_game_data(team_data, team, year):
    team_lookup = mlb.lookup_team(team)
    team_id = team_lookup[0]['fileCode']
    # pitcher_data = pd.read_csv(format(f"Data Files/{team_id}_2019.csv"))
    pitcher_data = Baseball_Model.get_team_data(team, year)

    home_game = []
    pitcher_name = []
    pitcher_hand = []
    pitcher_hits_nine = []
    for i in range(0, len(team_data)):
        index = pitcher_data[pitcher_data['game_id'] == team_data.iloc[i, 1]].index[0]
        home_game.append(pitcher_data.iloc[index, 2])
        pitcher_name.append(pitcher_data.iloc[index, 3])
        pitcher_hand.append(pitcher_data.iloc[index, 5])
        pitcher_hits_nine.append(pitcher_data.iloc[index, 6])

    team_data['Home'] = home_game
    team_data['Opp Pitcher'] = pitcher_name
    team_data['Opp Hand'] = pitcher_hand
    team_data['Opp Hits Nine'] = pitcher_hits_nine

    adv_matchup_list = []
    for i in range(0, len(team_data)):
        if (team_data.iloc[i, 9] == 'Left') and (team_data.iloc[i, 12] == 'Right'):
            adv_matchup_list.append(1)
        elif (team_data.iloc[i, 9] == 'Right') and (team_data.iloc[i, 12] == 'Left'):
            adv_matchup_list.append(1)
        elif team_data.iloc[i, 9] == 'Both':
            adv_matchup_list.append(1)
        else:
            adv_matchup_list.append(0)
    team_data['Adv Matchup'] = adv_matchup_list

    return team_data


def get_average(batter_name):
    batter_data = pd.read_csv("Data Files/batter_data.csv")

    try:
        index = batter_data[batter_data['Name'] == batter_name].index[0]
        avg = batter_data['BA'][index]

        return avg
    except IndexError:
        return 'NA'


def get_batter_hand(batter_name):
    name = batter_name.split()

    try:
        if name[0] == 'Matthew':
            name[0] = 'Matt'
        if len(name) == 3:
            if name[2] == 'Sr.' or name[2] == 'Jr.':
                last = name[1]
                first = name[0]
            else:
                last = name[2]
                first = name[0] + " " + name[1]
        elif len(name) == 2:
            last = name[1]
            first = name[0]
        else:
            last = name[1]
            first = name[0]

        player_id = pyb.playerid_lookup(last=last, first=first)

        bbref_id = player_id['key_bbref'][0]
        bbref_code = bbref_id[0]

        source = requests.get(format(f'https://www.baseball-reference.com/players/{bbref_code}/{bbref_id}.shtml')).text
        soup = BeautifulSoup(source, 'lxml')
        profile = soup.find('div', class_='players')

        hand = profile.find_all('p')[1].text
        hand = hand.split('Bats: ')

        output = hand[1]
        output = output.split("\n")[0]
        output = output.replace("\n", "")
        output = output.rstrip()
        return output

    except KeyError:
        return 'NA'

    except IndexError:
        return 'NA'

    except TypeError:
        return 'NA'

    except AttributeError:
        return 'NA'


def get_batter_hand_v2(batter_name):
    batter_data = pd.read_csv("Data Files/batter_data_v2.csv")

    try:
        index = batter_data[batter_data['Name'] == batter_name].index[0]
        hand = batter_data['Bats'][index]

        return hand

    except IndexError:
        return 'NA'


def get_full_team_data(team, year):
    batting_data = get_batting_data_season(team, year)
    combined_data = combine_game_data(batting_data, team, year)

    return combined_data
