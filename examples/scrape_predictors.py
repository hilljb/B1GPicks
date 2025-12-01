#!/usr/bin/env python
"""
Example script to scrape ESPN game predictors for Big Ten basketball games.

This script demonstrates how to use the B1GPicks scraper to collect
game predictor percentages for the next several days.
"""

from datetime import datetime
from b1gpicks import Scraper
import json


def main():
    """Main function to scrape and display game predictor data."""
    print("=" * 80)
    print("ESPN Big Ten Basketball Game Predictor Scraper")
    print("=" * 80)
    print()
    
    # Configuration
    num_days = 3
    start_date = datetime.now()
    
    print(f"Scraping game predictors for the next {num_days} days...")
    print(f"Starting from: {start_date.strftime('%Y-%m-%d')}")
    print()
    
    # Create scraper and collect data
    with Scraper() as scraper:
        results = scraper.scrape_games_by_date_range(
            start_date=start_date,
            num_days=num_days,
            delay_between_pages=1.5,  # Be respectful to ESPN's servers
            delay_between_games=1.0
        )
    
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    
    # Display results in a readable format
    total_games = 0
    games_with_predictors = 0
    
    for day_result in results:
        date = day_result['date']
        games = day_result['games']
        
        print(f"📅 {date}")
        print("-" * 80)
        
        if not games:
            print("  No games scheduled")
        else:
            for i, game in enumerate(games, 1):
                away = game['away_team']
                home = game['home_team']
                away_pct = game.get('away_win_pct')
                home_pct = game.get('home_win_pct')
                
                print(f"  {i}. {away} @ {home}")
                
                if away_pct is not None and home_pct is not None:
                    print(f"     Predictor: {away} {away_pct}% | {home} {home_pct}%")
                    games_with_predictors += 1
                else:
                    print(f"     Predictor: Not available")
                
                total_games += 1
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total games found: {total_games}")
    print(f"Games with predictors: {games_with_predictors}")
    
    if total_games > 0:
        print(f"Predictor availability: {games_with_predictors/total_games*100:.1f}%")
    
    print()
    
    # Optionally save to JSON file
    output_file = f"game_predictors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()

