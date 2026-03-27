import mwclient
import requests
import os
import datetime

# Configuration
TEAM_NAME = "Gen.G"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_GENG")

site = mwclient.Site('lol.fandom.com', path='/')

def get_drafts(days_back=30):
    start_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    # Query for games involving the team
    where_clause = f"(Team1='{TEAM_NAME}' OR Team2='{TEAM_NAME}') AND DateTime_UTC >= '{start_date}'"
    results = site.api('cargoquery',
        tables="ScoreboardGames",
        fields="Team1, Team2, WinTeam, ScoreboardID_Wiki, ChampionPicks, Venue, GameNum, MatchID",
        where=where_clause,
        order_by="DateTime_UTC DESC"
    )

    # Group games by MatchID (to keep the series together)
    series_dict = {}
    for match in results['cargoquery']:
        data = match['title']
        m_id = data['MatchID']
        if m_id not in series_dict:
            series_dict[m_id] = []
        series_dict[m_id].append(data)
    
    return series_dict

def post_to_discord(series_data):
    for m_id, games in series_data.items():
        # Sort games by Game Number
        games.sort(key=lambda x: x['GameNum'])
        
        embeds = []
        t1, t2 = games[0]['Team1'], games[0]['Team2']
        
        for game in games:
            # Format the draft string visually
            picks = game['ChampionPicks'].replace(',', ' | ')
            
            embed = {
                "title": f"Game {game['GameNum']}: {t1} vs {t2}",
                "description": f"**Draft:**\n`{picks}`",
                "url": f"https://lol.fandom.com/wiki/{game['ScoreboardID_Wiki'].replace(' ', '_')}",
                "color": 5814783 if game['WinTeam'] == TEAM_NAME else 15158332,
                "footer": {"text": f"Series ID: {m_id}"}
            }
            embeds.append(embed)

        # Discord allows up to 10 embeds in one message (perfect for Bo3/Bo5)
        payload = {
            "content": f"## 📊 Series Report: {t1} vs {t2} (Fearless Mode Context)",
            "embeds": embeds
        }
        requests.post(WEBHOOK_URL, json=payload)

if __name__ == "__main__":
    data = get_drafts(30) # Backtest 30 days
    post_to_discord(data)
