import requests
from bs4 import BeautifulSoup

def get_team_stats(team_abbr):
    """
    Scrapes comprehensive team stats from basketball-reference.com for the 2023-2024 season.
    
    Args:
        team_abbr (str): Team abbreviation (e.g. 'LAL', 'GSW')
    
    Returns:
        dict: Dictionary of team stats or error message.
    """
    url = f"https://www.basketball-reference.com/teams/{team_abbr}/2024.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
    except requests.RequestException as e:
        return {"error": f"Failed to retrieve data for team {team_abbr}: {str(e)}"}

    soup = BeautifulSoup(res.text, "html.parser")
    
    # Initialize stats dictionary
    stats = {
        "team": team_abbr,
        "basic_stats": {},
        "advanced_stats": {},
        "team_info": {}
    }
    
    # Get team name and basic info
    team_info = soup.find("div", {"id": "info"})
    if team_info:
        stats["team_info"]["name"] = team_info.find("h1").get_text(strip=True).replace("2023-24 ", "")
        stats["team_info"]["record"] = team_info.find("div", {"id": "meta"}).find_all("p")[1].get_text(strip=True)
    
    # Get basic stats from team_and_opponent table
    table = soup.find("table", id="team_and_opponent")
    if table:
        for row in table.tbody.find_all("tr"):
            label = row.find("th").get_text(strip=True)
            value = row.find("td").get_text(strip=True)
            stats["basic_stats"][label] = value
    
    # Get advanced stats from advanced-team table
    advanced_table = soup.find("table", id="advanced-team")
    if advanced_table:
        for row in advanced_table.tbody.find_all("tr"):
            label = row.find("th").get_text(strip=True)
            value = row.find("td").get_text(strip=True)
            stats["advanced_stats"][label] = value
    
    return stats