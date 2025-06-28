import os
import pandas as pd
from NBADataScraper import NBADataScraper

def run_scraper(start_year=2021, end_year=2025):
    """
    Scrapes NBA data for each season separately and saves to individual CSV files.
    """
    print(f"🚀 Starting NBA data scraping from {start_year-1}-{start_year} to {end_year-1}-{end_year}...")
    
    for season_year in range(start_year, end_year + 1):
        year_str = str(season_year)
        print(f"\n=== Processing {int(year_str)-1}-{year_str} season ===")
        
        # Create a new scraper instance for each season
        scraper = NBADataScraper()
        months = ["october", "november", "december", "january", "february", "march", "april"]
        
        try:
            # Scrape only the current season
            print(f"🔍 Scraping {int(year_str)-1}-{year_str} season data...")
            basic_data = scraper.scrape_full_season(year_str, months)
            
            if basic_data is None or basic_data.empty:
                print(f"❌ No data found for {int(year_str)-1}-{year_str}")
                continue

            # Enhance data for this season only
            print("📊 Enhancing game data...")
            enhanced_df = scraper.enhance_game_data()
            
            if enhanced_df.empty:
                print(f"⚠️ Enhancement failed for {int(year_str)-1}-{year_str}")
                continue

            # Calculate DSLG and records for this season
            print("📈 Calculating advanced metrics...")
            data_with_dslg = scraper.calculate_days_since_last_match(enhanced_df.to_dict('records'))
            final_data = scraper.calculate_team_record(data_with_dslg)
            final_df = pd.DataFrame(final_data)

            # Save to season-specific CSV
            os.makedirs("data", exist_ok=True)
            output_file = f"data/nba_{int(year_str)-1}_{year_str}.csv"
            final_df.to_csv(output_file, index=False)
            print(f"✅ Successfully saved {output_file}")

        except Exception as e:
            print(f"🔥 Error processing {int(year_str)-1}-{year_str}: {str(e)}")
            continue

    print("\n🎉 All seasons processed!")

if __name__ == "__main__":
    run_scraper(start_year=2021, end_year=2025)