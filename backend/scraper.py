# # scraper.py
# from NBADataScraper import NBADataScraper
# import os
# import pandas as pd

# def run_scraper(season_year="2024"):
#     scraper = NBADataScraper()
#     months = ["october", "november", "december", "january", "february", "march", "april"]
#     basic_data = scraper.scrape_full_season(season_year, months)

#     if basic_data is not None and not basic_data.empty:
#         enhanced_df = scraper.enhance_game_data()
#         enhanced_data_with_days = scraper.calculate_days_since_last_match(enhanced_df.to_dict('records'))
#         enhanced_df_with_days = pd.DataFrame(enhanced_data_with_days)

#         merged_df = pd.merge(
#             enhanced_df,
#             enhanced_df_with_days[['Date', 'Home/Neutral', 'Visitor/Neutral', 'DSLG (Home)', 'DSLG (Visitor)']],
#             on=['Date', 'Home/Neutral', 'Visitor/Neutral'],
#             how='left'
#         )

#         final_data_with_records = scraper.calculate_team_record(merged_df.to_dict('records'))
#         final_df_with_records = pd.DataFrame(final_data_with_records)

#         os.makedirs("data", exist_ok=True)
#         final_file = f"data/nba_{int(season_year)-1}_{season_year}_final_data.csv"
#         final_df_with_records.to_csv(final_file, index=False)
#         return final_file
#     else:
#         return None
import os
import pandas as pd
from NBADataScraper import NBADataScraper # Ensure this import path is correct

def run_scraper(season_year="2024"):
    print("🚀 Starting NBA data scraping process...")
    scraper = NBADataScraper()
    months = ["october", "november", "december", "january", "february", "march", "april"]

    print(f"🔍 Scraping full season data for {int(season_year)-1}-{season_year}...")
    basic_data_df_check = scraper.scrape_full_season(season_year, months)

    if basic_data_df_check is not None and not basic_data_df_check.empty and scraper.game_results:
        print("📊 Enhancing game data with recent performance and head-to-head statistics...")
        enhanced_df = scraper.enhance_game_data()

        if not enhanced_df.empty:
            print("📈 Calculating Days Since Last Game (DSLG)...")
            data_with_dslg_records = scraper.calculate_days_since_last_match(enhanced_df.to_dict('records'))
            df_with_dslg = pd.DataFrame(data_with_dslg_records)

            print("📋 Calculating final team records (Wins/Losses before each game)...")
            final_data_with_records_list = scraper.calculate_team_record(df_with_dslg.to_dict('records'))
            final_df_with_records = pd.DataFrame(final_data_with_records_list)

            os.makedirs("data", exist_ok=True)
            final_file = f"data/nba_{int(season_year)-1}_{season_year}_final_data.csv"
            
            final_df_with_records.to_csv(final_file, index=False)
            print(f"✅ Data scraping and enhancement complete! Data saved to: {final_file}")
            return final_file
        else:
            print("⚠️ No enhanced data was generated. This might indicate an issue within NBADataScraper.enhance_game_data().")
            return None
    else:
        print("❌ Failed to scrape basic game data. Please check the website layout or your internet connection.")
        return None

if __name__ == "__main__":
    run_scraper(season_year="2024")
