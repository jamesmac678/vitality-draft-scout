import mwclient
import requests
import os
import datetime
import time

TEAM_NAME = "Gen.G"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_GENG")

site = mwclient.Site('lol.fandom.com', path='/')
site.header_headers = {
    'User-Agent': 'VitalityScoutBot/1.2 (Mac Coaching Project)'
}

def get_drafts():
    # Looking back 45 days to capture the recent tournament cycle
    start_date = (datetime.datetime.now() - datetime.timedelta(days=45)).strftime('%Y-%m-%d')
    
    where_clause = f"(Team1='{TEAM_NAME}' OR Team2='{TEAM_NAME}') AND DateTime_UTC >= '{start_date}'"
    
    try:
        # Simplified field list to prevent MWException
        results = site.api('cargoquery',
            tables="ScoreboardGames",
            fields="Team1, Team2, WinTeam, ScoreboardID_Wiki, ChampionPicks, MatchID, GameNum",
            where=where_clause,
            order_by="DateTime_UTC DESC",
            limit="20"
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
        print("No data retrieved. API may be down or rate-limited.")
        return

    # We only want the most recent 2 series for this test drop
    for m_id in list(series_data.keys())[:2]:
        games = sorted(series_data[m_id], key=lambda x: x['GameNum'])
        embeds = []
        
        for game in games:
            embed = {
                "title": f"Game {game['GameNum']}: {game['Team1']} vs {game['Team2']}",
                "description": f"**Picks:** `{game['ChampionPicks'].replace(',', ' | ')}`",
                "url": f"https://lol.fandom.com/wiki/{game['ScoreboardID_Wiki'].replace(' ', '_')}",
                "color": 5814783 if game['WinTeam'] == TEAM_NAME else 15158332
            }
            embeds.append(embed)

        payload = {
            "content": f"## 🇰🇷 Latest Series: {TEAM_NAME}",
            "embeds": embeds
        }
        requests.post(WEBHOOK_URL, json=payload)
        time.sleep(1)

if __name__ == "__main__":
    data = get_drafts()
    post_to_discord(data)
