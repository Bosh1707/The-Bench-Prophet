import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
import time
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

class NBADataScraper:
    def __init__(self, base_url="https://www.basketball-reference.com"):
        self.base_url = base_url
        self.team_data = {}  # Cache for team data
        self.game_results = []  # Store game results
        self.team_abbreviations = {}  # Team names to its abbreviations
        self.load_team_abbreviations()
    
    def load_team_abbreviations(self):
        """Load NBA team abbreviations for URLs"""
        self.team_abbreviations = {
            "Atlanta Hawks": "ATL",
            "Boston Celtics": "BOS",
            "Brooklyn Nets": "BRK",
            "Charlotte Hornets": "CHO",
            "Chicago Bulls": "CHI",
            "Cleveland Cavaliers": "CLE",
            "Dallas Mavericks": "DAL",
            "Denver Nuggets": "DEN",
            "Detroit Pistons": "DET",
            "Golden State Warriors": "GSW",
            "Houston Rockets": "HOU",
            "Indiana Pacers": "IND",
            "Los Angeles Clippers": "LAC",
            "Los Angeles Lakers": "LAL",
            "Memphis Grizzlies": "MEM",
            "Miami Heat": "MIA",
            "Milwaukee Bucks": "MIL",
            "Minnesota Timberwolves": "MIN",
            "New Orleans Pelicans": "NOP",
            "New York Knicks": "NYK",
            "Oklahoma City Thunder": "OKC",
            "Orlando Magic": "ORL",
            "Philadelphia 76ers": "PHI",
            "Phoenix Suns": "PHO",
            "Portland Trail Blazers": "POR",
            "Sacramento Kings": "SAC",
            "San Antonio Spurs": "SAS",
            "Toronto Raptors": "TOR",
            "Utah Jazz": "UTA",
            "Washington Wizards": "WAS"
        }

    def clean_text(self, text):
        if not isinstance(text, str):
            return text
        return text.replace(',', '').replace('*', '').strip()
    
    def get_team_abbreviation(self, team_name):
        clean_name = team_name.strip()
        if clean_name in self.team_abbreviations:
            return self.team_abbreviations[clean_name]
        for name, abbr in self.team_abbreviations.items():
            if clean_name in name or name in clean_name:
                return abbr
        print(f"Warning: No abbreviation found for team '{team_name}'")
        return None

    def scrape_nba_month(self, url):
        print(f"Scraping: {url}")
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None
        soup = BeautifulSoup(response.content, 'html.parser')
        schedule_table = soup.find('table', {'id': 'schedule'})
        if not schedule_table:
            tables = soup.find_all('table')
            for table in tables:
                if table.find('th', string=re.compile("Visitor|Home|Date", re.IGNORECASE)):
                    schedule_table = table
                    break
        if not schedule_table:
            print("Could not find schedule table on the page")
            return None
        headers = []
        header_row = schedule_table.find('thead')
        if header_row:
            header_cells = header_row.find_all('th')
            headers = [th.text.strip() for th in header_cells]
            print(f"Found headers: {headers}")
        else:
            print("No thead found in table")
            return None

        # Whatever you want to remove just put it in here, must match exactly
        columns_to_remove = ['LOG', 'Arena', 'Start (ET)', 'Attend.', 'Notes']
        indices_to_remove = [i for i, header in enumerate(headers) if header in columns_to_remove]

        # Filter headers to keep only the desired ones
        filtered_headers = [header for i, header in enumerate(headers) if i not in indices_to_remove]
        print(f"Filtered headers: {filtered_headers}")

        rows = []
        all_rows = schedule_table.find('tbody').find_all('tr')

        for row in all_rows:
            if 'thead' in row.get('class', []):
                continue
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:
                continue

            row_data = []
            for cell in cells:
                if cell.find('a'):
                    team_link = cell.find('a')
                    if team_link.get('title'):
                        row_data.append(team_link['title'])
                    else:
                        row_data.append(self.clean_text(cell.text))
                else:
                    row_data.append(self.clean_text(cell.text))

            # Filter row data to exclude the columns being removed
            filtered_row_data = [data for i, data in enumerate(row_data) if i not in indices_to_remove]

            while len(filtered_row_data) < len(filtered_headers):
                filtered_row_data.append('')

            if any(cell for cell in filtered_row_data):
                rows.append(filtered_row_data)

        if not rows:
            print("No data rows found in the table after filtering")
            return None

        df = pd.DataFrame(rows, columns=filtered_headers)

        # Re-calculating visitor and home points based on the new header order that we want
        visitor_pts_idx = None
        home_pts_idx = None
        for i, header in enumerate(filtered_headers):
            if header == 'PTS' and visitor_pts_idx is None:
                visitor_pts_idx = i
            elif header == 'PTS' and visitor_pts_idx is not None:
                home_pts_idx = i

        if visitor_pts_idx is not None and home_pts_idx is not None:
            df['Visitor_PTS'] = df.iloc[:, visitor_pts_idx].apply(self.parse_pts)
            df['Home_PTS'] = df.iloc[:, home_pts_idx].apply(self.parse_pts)
        else:
            print(f"Warning: Could not reliably identify points columns after filtering. Filtered headers: {filtered_headers}")

        month_match = re.search(r'games-(\w+)\.html', url)
        year_match = re.search(r'NBA_(\d+)', url)

        if month_match and year_match:
            month = month_match.group(1)
            year = year_match.group(1)
            df['Month'] = month
            df['Season'] = f"{int(year)-1}-{year}"

        for _, row in df.iterrows():
            game_dict = row.to_dict()
            # Ensure Visitor_PTS and Home_PTS exists in the data
            if 'Visitor_PTS' not in game_dict and 'PTS' in game_dict:
                game_dict['Visitor_PTS'] = self.parse_pts(game_dict['PTS'])
            if 'Home_PTS' not in game_dict and 'PTS.1' in game_dict:
                game_dict['Home_PTS'] = self.parse_pts(game_dict['PTS.1'])
            self.game_results.append(game_dict)

        return df

    def scrape_full_season(self, season_year, months): # Scraps data for one full season
        all_data = []
        for month in months:
            url = f"{self.base_url}/leagues/NBA_{season_year}_games-{month}.html"
            month_data = self.scrape_nba_month(url)          
            if month_data is not None and not month_data.empty:
                all_data.append(month_data)
                print(f"Successfully scraped {month} {season_year} data: {len(month_data)} rows")
            else:
                print(f"Failed to scrape {month} {season_year} data")
            
            time.sleep(1)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            return combined_df
        else:
            return None

    def get_team_season_stats(self, team_abbr, season):
        # Check if we already have this team's data cached
        cache_key = f"{team_abbr}_{season}"
        if cache_key in self.team_data:
            return self.team_data[cache_key]
        
        # Changing the season name formatting to 2023-24 instead of 2023-2024
        season_short = season.replace("-20", "-")
        
        url = f"{self.base_url}/teams/{team_abbr}/{season_short}.html"
        print(f"Fetching team stats: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching team stats: {e}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        team_stats = {}
        
        try:
            record_div = soup.find('div', {'data-template': 'Partials/Teams/Summary'})
            if record_div:
                record_p = record_div.find('p')
                if record_p:
                    record_text = record_p.text
                    record_match = re.search(r'Record:\s+(\d+-\d+)', record_text)
                    if record_match:
                        team_stats['record'] = record_match.group(1)
            
            advanced_div = soup.find('div', {'id': 'all_team_and_opponent'})
            if advanced_div:
                table = advanced_div.find('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['th', 'td'])
                        if len(cells) > 1:
                            if cells[0].text.strip() == 'Team':
                                team_stats['offensive_rating'] = cells[8].text.strip() if len(cells) > 8 else 'N/A'
                            if cells[0].text.strip() == 'Opponent':
                                team_stats['defensive_rating'] = cells[8].text.strip() if len(cells) > 8 else 'N/A'
        except Exception as e:
            print(f"Error parsing team stats: {e}")
        
        self.team_data[cache_key] = team_stats
        
        # Add a small delay to be nice to the server, recommended by peers
        time.sleep(1)
        
        return team_stats

    def calculate_recent_performance(self, team_name, date, season, num_games=5):
        team_abbr = self.get_team_abbreviation(team_name)
        if not team_abbr:
            return {'recent_wins': 0, 'recent_losses': 0, 'win_percentage': 0.0}
        
        # Converting date to datetime object if it's not already
        if isinstance(date, str):
            try:
                # Trying different date formats
                try:
                    date = datetime.strptime(date, '%a %b %d %Y')
                except ValueError:
                    date = datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                print(f"Error parsing date: {date}")
                return {'recent_wins': 0, 'recent_losses': 0, 'win_percentage': 0.0}
        
        recent_games = []
        
        for game in self.game_results:
            game_date_str = game.get('Date', '')
            visitor_team = game.get('Visitor/Neutral', '')
            home_team = game.get('Home/Neutral', '')
            
            if team_name not in visitor_team and team_name not in home_team:
                continue
                
            try:
                # Try different date formats
                try:
                    game_date = datetime.strptime(game_date_str, '%a %b %d %Y')
                except ValueError:
                    game_date = datetime.strptime(game_date_str, '%Y-%m-%d')
                    
                if game_date < date:
                    recent_games.append(game)
            except ValueError:
                continue
        
        recent_games.sort(key=lambda g: datetime.strptime(g.get('Date', ''), '%a %b %d %Y') 
                         if 'Date' in g and g['Date'] else datetime.now(), reverse=True)
        recent_games = recent_games[:num_games]
        
        wins, losses = 0, 0
        
        for game in recent_games:
            visitor_team = game.get('Visitor/Neutral', '')
            home_team = game.get('Home/Neutral', '')
            visitor_pts = self.parse_pts(game.get('PTS', 0))
            home_pts = self.parse_pts(game.get('PTS.1', 0))
            
            if team_name in visitor_team:
                if visitor_pts > home_pts:
                    wins += 1
                else:
                    losses += 1
            elif team_name in home_team:
                if home_pts > visitor_pts:
                    wins += 1
                else:
                    losses += 1
        
        total_games = wins + losses
        win_percentage = (wins / total_games) * 100 if total_games > 0 else 0
        
        return {
            'recent_wins': wins,
            'recent_losses': losses,
            'win_percentage': round(win_percentage, 1)
        }

    def calculate_head_to_head(self, team1, team2, season):
        h2h_games = []
    
        for game in self.game_results:
            visitor_team = game.get('Visitor/Neutral', '')
            home_team = game.get('Home/Neutral', '')
            game_season = game.get('Season', '')
        
            if game_season != season:
                continue
        
            if ((team1 in visitor_team and team2 in home_team) or 
                (team2 in visitor_team and team1 in home_team)):
                h2h_games.append(game)
    
        team1_wins = 0
        team2_wins = 0
    
        for game in h2h_games:
            visitor_team = game.get('Visitor/Neutral', '')
            home_team = game.get('Home/Neutral', '')
        
            if 'Visitor_PTS' in game and 'Home_PTS' in game:
                visitor_pts = self.parse_pts(game.get('Visitor_PTS', 0))
                home_pts = self.parse_pts(game.get('Home_PTS', 0))
            else:
                visitor_pts = self.parse_pts(game.get('PTS', 0))
                home_pts = self.parse_pts(game.get('PTS.1', 0))
        
            if team1 in visitor_team:
                if visitor_pts > home_pts:
                    team1_wins += 1
                else:
                    team2_wins += 1
            elif team1 in home_team:
                if home_pts > visitor_pts:
                    team1_wins += 1
                else:
                    team2_wins += 1
    
        return {
            f"{team1}_wins": team1_wins,
            f"{team2}_wins": team2_wins,
            'total_games': team1_wins + team2_wins
        }
        
    def parse_pts(self, pts_value):
        if pd.isna(pts_value) or pts_value == '':
            return 0
        
        pts_str = str(pts_value).strip()
    
        try:
            return int(pts_str)
        except (ValueError, TypeError):
            try:
                nums = re.findall(r'\d+', pts_str)
                if nums:
                    return int(nums[0])
                return 0
            except (ValueError, TypeError):
                print(f"Warning: Could not parse points value: '{pts_value}'")
                return 0

    def enhance_game_data(self):
        enhanced_games = []
    
        for game in self.game_results:
            if not game.get('Visitor/Neutral') or not game.get('Home/Neutral') or not game.get('Date'):
                continue
            
            visitor_team = game.get('Visitor/Neutral', '')
            home_team = game.get('Home/Neutral', '')
            date = game.get('Date', '')
            season = game.get('Season', '')
        
            visitor_pts = 0
            home_pts = 0
        
            if 'Visitor_PTS' in game and not pd.isna(game['Visitor_PTS']):
                visitor_pts = self.parse_pts(game['Visitor_PTS'])
            elif 'PTS' in game and not pd.isna(game['PTS']):
                visitor_pts = self.parse_pts(game['PTS'])
            
            if 'Home_PTS' in game and not pd.isna(game['Home_PTS']):
                home_pts = self.parse_pts(game['Home_PTS'])
            elif 'PTS.1' in game and not pd.isna(game['PTS.1']):
                home_pts = self.parse_pts(game['PTS.1'])
        
            if visitor_pts == 0 or home_pts == 0:
                for key, value in game.items():
                    if 'PTS' in key and key not in ['Visitor_PTS', 'Home_PTS', 'PTS', 'PTS.1']:
                        pts_value = self.parse_pts(value)
                        if pts_value > 0:
                            if visitor_pts == 0:
                                visitor_pts = pts_value
                            elif home_pts == 0:
                                home_pts = pts_value
                                break
        
            if visitor_pts == 0 or home_pts == 0:
                print(f"Warning: Zero points detected for game {date}: {visitor_team} vs {home_team}")
                print(f"Point-related fields in game data: {[k for k in game.keys() if 'PTS' in k or 'pts' in k.lower()]}")
        
            visitor_recent = self.calculate_recent_performance(visitor_team, date, season)
            home_recent = self.calculate_recent_performance(home_team, date, season)
        
            h2h = self.calculate_head_to_head(visitor_team, home_team, season)
        
            enhanced_game = game.copy()
        
            enhanced_game['Visitor_PTS'] = visitor_pts
            enhanced_game['Home_PTS'] = home_pts
        
            enhanced_game.update({
                'Recent Wins (Home)': home_recent['recent_wins'],
                'Recent Losses (Home)': home_recent['recent_losses'],
                'Recent Win % (Home)': home_recent['win_percentage'],
                'Recent Wins (Visitor)': visitor_recent['recent_wins'],
                'Recent Losses (Visitor)': visitor_recent['recent_losses'],
                'Recent Win % (Visitor)': visitor_recent['win_percentage'],
                'Matchup Wins (Home)': h2h[f"{home_team}_wins"],
                'Matchup Wins (Visitor)': h2h[f"{visitor_team}_wins"],
                'Total Matchups': h2h['total_games']
            })
        
            enhanced_games.append(enhanced_game)
    
        return pd.DataFrame(enhanced_games)

    def calculate_days_since_last_match(self, all_game_data):
        team_last_played = {}
        enhanced_data_with_days = []
        for game in all_game_data:
            game_date_str = game.get('Date')
            visitor_team = game.get('Visitor/Neutral')
            home_team = game.get('Home/Neutral')

            if not game_date_str or not visitor_team or not home_team:
                enhanced_data_with_days.append(game)
                continue

            try:
                game_date = datetime.strptime(game_date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    game_date = datetime.strptime(game_date_str, '%a %b %d %Y')
                except ValueError:
                    print(f"Warning: Could not parse date: {game_date_str}")
                    enhanced_data_with_days.append(game)
                    continue

            days_since_visitor_last = None
            if visitor_team in team_last_played:
                time_difference = game_date - team_last_played[visitor_team]
                days_since_visitor_last = time_difference.days

            days_since_home_last = None
            if home_team in team_last_played:
                time_difference = game_date - team_last_played[home_team]
                days_since_home_last = time_difference.days

            game_with_days = game.copy()
            game_with_days['DSLG (Visitor)'] = days_since_visitor_last
            game_with_days['DSLG (Home)'] = days_since_home_last
            enhanced_data_with_days.append(game_with_days)

            team_last_played[visitor_team] = game_date
            team_last_played[home_team] = game_date

        return enhanced_data_with_days

    def calculate_team_record(self, all_game_data):
        team_records = {}
        enhanced_data_with_records = []

        for game in all_game_data:
            game_date_str = game.get('Date')
            visitor_team = game.get('Visitor/Neutral')
            home_team = game.get('Home/Neutral')
            visitor_pts = game.get('Visitor_PTS')
            home_pts = game.get('Home_PTS')

            if not game_date_str or not visitor_team or not home_team or visitor_pts is None or home_pts is None:
                enhanced_data_with_records.append(game)
                continue

            try:
                game_date = datetime.strptime(game_date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    game_date = datetime.strptime(game_date_str, '%a %b %d %Y')
                except ValueError:
                    print(f"Warning: Could not parse date: {game_date_str}")
                    enhanced_data_with_records.append(game)
                    continue
            
            # Create a dictionary for both home and visitor records
            # Key will be the abbreviated team name, value will be another dict
            visitor_record = team_records.get(visitor_team, {'wins':0, 'losses':0}).copy()
            home_record = team_records.get(home_team, {'wins':0, 'losses':0}).copy()

            game_with_records = game.copy()
            game_with_records['Wins (Home)'] = home_record['wins']
            game_with_records['Losses (Home)'] = home_record['losses']
            game_with_records['Wins (Visitor)'] = visitor_record['wins']
            game_with_records['Losses (Visitor)'] = visitor_record['losses']
            enhanced_data_with_records.append(game_with_records)

            if visitor_pts > home_pts:
                team_records.setdefault(visitor_team, {'wins':0, 'losses':0})['wins'] += 1
                team_records.setdefault(home_team, {'wins':0, 'losses':0})['losses'] += 1
            else:
                team_records.setdefault(visitor_team, {'wins':0, 'losses':0})['losses'] += 1
                team_records.setdefault(home_team, {'wins':0, 'losses':0})['wins'] += 1

        return enhanced_data_with_records

def main():
        scraper = NBADataScraper()
        seasons = ['2022', '2023', '2024'] # Add the seasons you want
        months = ["october", "november", "december", "january", "february", "march", "april"]

        all_season_data = []

        for season in seasons:
            print(f"Starting to scrape NBA {int(season)-1}-{season} season data...")
            basic_data = scraper.scrape_full_season(season, months)

            if basic_data is not None and not basic_data.empty:
                print("Basic game data scraped successfully.")
                print("Enhancing data with recent performance and head-to-head records...")
                enhanced_df = scraper.enhance_game_data()

                if not enhanced_df.empty:
                    print("Calculating days since last match...")
                    enhanced_data_with_days = scraper.calculate_days_since_last_match(enhanced_df.to_dict('records'))
                    enhanced_df_with_days = pd.DataFrame(enhanced_data_with_days)

                    final_df = pd.merge(enhanced_df, enhanced_df_with_days[['Date', 'Home/Neutral', 'Visitor/Neutral', 'DSLG (Home)', 'DSLG (Visitor)']],
                                     on=['Date', 'Home/Neutral', 'Visitor/Neutral'], how='left')
                    all_season_data.append(final_df) 

                else:
                    print(f"Failed to enhance game data for {int(season)-1}-{season} season.")
            else:
                print(f"Failed to scrape basic game data for {int(season)-1}-{season} season.")

        if all_season_data:
            combined_df = pd.concat(all_season_data, ignore_index=True)
            os.makedirs("data", exist_ok=True)
            final_file = "data/nba_2021_2024_final_data.csv"
            combined_df.to_csv(final_file, index=False)
            print(f"Saved combined data for all seasons to {final_file}")

            print("\nSample of combined data:")
            display_cols = list(combined_df.columns)
            print(combined_df[display_cols].head())
        else:
            print("No data was scraped for any season")

if __name__ == "__main__":
    main()
