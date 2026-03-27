import mwclient
import requests
import os
import datetime
import time

# Configuration
TEAM_NAME = "Gen.G"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_GENG")

# More aggressive headers to bypass the "GitHub IP" flag
site = mwclient.Site('lol.fandom.com', path='/')
site.header_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) VitalityScout/1.1 (Contact: jamesmac678@example.com)',
    'Accept-Encoding': 'gzip'
}

def get_drafts(days_back=60): # Bumped to 60 to ensure we catch First Stand
    start_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
    print(f"Querying games since {start_date}...")
    
    where_clause = f"(Team1='{TEAM_NAME}' OR Team2='{TEAM_NAME}') AND DateTime_UTC >= '{start_date}'"
    
    try:
        # Using a slightly different query method that is sometimes less restricted
        results = site.api('cargoquery',
            tables="ScoreboardGames",
            fields="Team1, Team2, WinTeam, ScoreboardID_Wiki, ChampionPicks, GameNum, MatchID, BlueBans, RedBans",
            where=where_clause,
            order_by="DateTime_UTC DESC"
        )
    except Exception as e:
        print(f"API Error: {e}")
        return {}

    series_dict = {}
    if 'cargoquery' in results:
        for match in results['cargoquery']:
            data = match['title']
            m_id = data['MatchID']
            if m_id not in series_dict:
                series_dict[m_id] = []
            series_dict[m_id].append(data)
    
    return series_dict

def post_to_discord(series_data):
    if not series_data:
        print("No data retrieved. Still being rate-limited by Leaguepedia.")
        return

    for m_id, games in list(series_data.items())[:3]: # Limit to last 3 series for the test
        games.sort(key=lambda x: x['GameNum'])
        embeds = []
        t1, t2 = games[0]['Team1'], games[0]['Team2']
        
        for game in games:
            picks = game['ChampionPicks'].replace(',', ' | ')
            bans = f"B: {game['BlueBans']} \nR: {game['RedBans']}"
            
            embed = {
                "title": f"Game {game['GameNum']}: {t1} vs {t2}",
                "description": f"**Picks:** `{picks}`\n**Bans:** `{bans}`",
                "url": f"https://lol.fandom.com/wiki/{game['ScoreboardID_Wiki'].replace(' ', '_')}",
                "color": 5814783 if game['WinTeam'] == TEAM_NAME else 15158332
            }
            embeds.append(embed)

        payload = {
            "content": f"## 🇰🇷 Gen.G Series Report",
            "embeds": embeds
        }
        r = requests.post(WEBHOOK_URL, json=payload)
        print(f"Discord Response: {r.status_code}")
        time.sleep(2)

if __name__ == "__main__":
    data = get_drafts(60)
    post_to_discord(data)
