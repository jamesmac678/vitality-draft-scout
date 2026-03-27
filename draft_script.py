import mwclient
import requests
import os
import datetime
import time

# Configuration
TEAM_NAME = "Gen.G"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_GENG")

# Adding a User Agent is critical for Leaguepedia API access
site = mwclient.Site('lol.fandom.com', path='/')
site.user_agent = 'VitalityDraftBot/1.0 (jamesmac678@example.com)' # Replace with your email if you like

def get_drafts(days_back=30):
    start_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    where_clause = f"(Team1='{TEAM_NAME}' OR Team2='{TEAM_NAME}') AND DateTime_UTC >= '{start_date}'"
    
    try:
        results = site.api('cargoquery',
            tables="ScoreboardGames",
            fields="Team1, Team2, WinTeam, ScoreboardID_Wiki, ChampionPicks, Venue, GameNum, MatchID, BlueBans, RedBans",
            where=where_clause,
            order_by="DateTime_UTC DESC"
        )
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}

    series_dict = {}
    for match in results['cargoquery']:
        data = match['title']
        m_id = data['MatchID']
        if m_id not in series_dict:
            series_dict[m_id] = []
        series_dict[m_id].append(data)
    
    return series_dict

def post_to_discord(series_data):
    if not series_data:
        print("No recent matches found to post.")
        return

    for m_id, games in series_data.items():
        games.sort(key=lambda x: x['GameNum'])
        embeds = []
        t1, t2 = games[0]['Team1'], games[0]['Team2']
        
        for game in games:
            picks = game['ChampionPicks'].replace(',', ' | ')
            # Adding bans for Fearless context
            bans = f"Blue: {game['BlueBans']} \nRed: {game['RedBans']}"
            
            embed = {
                "title": f"Game {game['GameNum']}: {t1} vs {t2}",
                "description": f"**Draft Picks:**\n`{picks}`\n\n**Bans:**\n`{bans}`",
                "url": f"https://lol.fandom.com/wiki/{game['ScoreboardID_Wiki'].replace(' ', '_')}",
                "color": 5814783 if game['WinTeam'] == TEAM_NAME else 15158332
            }
            embeds.append(embed)

        payload = {
            "content": f"## 📊 Series Report: {t1} vs {t2}",
            "embeds": embeds[:10] 
        }
        requests.post(WEBHOOK_URL, json=payload)
        time.sleep(2) # Brief pause between series to avoid Discord rate limits

if __name__ == "__main__":
    data = get_drafts(30)
    post_to_discord(data)
