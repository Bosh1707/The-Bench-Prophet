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
from NBADataScraper import NBADataScraper
import os
import pandas as pd

def run_scraper(season_year="2024"):
    print("🚀 Starting scraper...")
    scraper = NBADataScraper()
    months = ["october", "november", "december", "january", "february", "march", "april"]

    print("🔍 Scraping full season...")
    basic_data = scraper.scrape_full_season(season_year, months)

    if basic_data is not None and not basic_data.empty:
        print("📊 Enhancing game data...")
        enhanced_df = scraper.enhance_game_data()

        print("📈 Calculating DSLG...")
        enhanced_data_with_days = scraper.calculate_days_since_last_match(enhanced_df.to_dict('records'))
        enhanced_df_with_days = pd.DataFrame(enhanced_data_with_days)

        print("🔗 Merging DSLG with base data...")
        merged_df = pd.merge(
            enhanced_df,
            enhanced_df_with_days[['Date', 'Home/Neutral', 'Visitor/Neutral', 'DSLG (Home)', 'DSLG (Visitor)']],
            on=['Date', 'Home/Neutral', 'Visitor/Neutral'],
            how='left'
        )

        print("📋 Calculating final team records...")
        final_data_with_records = scraper.calculate_team_record(merged_df.to_dict('records'))
        final_df_with_records = pd.DataFrame(final_data_with_records)

        os.makedirs("data", exist_ok=True)
        final_file = f"data/nba_{int(season_year)-1}_{season_year}_final_data.csv"
        final_df_with_records.to_csv(final_file, index=False)
        print(f"✅ Done! Data saved to {final_file}")
        return final_file
    else:
        print("⚠️ No data scraped. Please check if the site layout changed or internet is down.")
        return None

# Run the function if this script is executed directly
if __name__ == "__main__":
    run_scraper()