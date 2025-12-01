#!/usr/bin/env python
"""
Debug script to inspect ESPN's HTML structure and test selectors.
This will help us understand why games aren't being found.
"""

import sys
from pathlib import Path

# Add src to path so we can import without installing
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from b1gpicks import Scraper
from datetime import datetime

def debug_schedule_page():
    """Debug the schedule page structure."""
    print("=" * 80)
    print("DEBUGGING SCHEDULE PAGE")
    print("=" * 80)
    
    # Test with tomorrow's date (Dec 2, 2025)
    test_date = datetime(2025, 12, 2)
    url = Scraper.get_schedule_url(test_date)
    
    print(f"\nURL: {url}")
    print("\nFetching page...")
    
    with Scraper() as scraper:
        try:
            soup = scraper.get_soup(url)
            print("✓ Page fetched successfully")
            
            # Save the full HTML for inspection
            with open('schedule_page_debug.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("✓ Saved full HTML to: schedule_page_debug.html")
            
            # Check for "No Data Available"
            no_data = soup.find('div', class_='Table__NoData')
            if no_data:
                print("\n⚠ Found 'No Data Available' message")
                print(f"  Content: {no_data.get_text(strip=True)}")
            else:
                print("\n✓ No 'No Data Available' message found")
            
            # Look for table body
            print("\n--- Checking for table body ---")
            table_body = soup.find('tbody', class_='Table__TBODY')
            if table_body:
                print("✓ Found <tbody class='Table__TBODY'>")
                rows = table_body.find_all('tr')
                print(f"  Found {len(rows)} rows")
            else:
                print("✗ Did not find <tbody class='Table__TBODY'>")
                
                # Try alternative selectors
                print("\n--- Trying alternative selectors ---")
                table_body = soup.find('tbody')
                if table_body:
                    print("✓ Found <tbody> (without specific class)")
                    rows = table_body.find_all('tr')
                    print(f"  Found {len(rows)} rows")
                else:
                    print("✗ No <tbody> found at all")
                    
                    # Look for any tables
                    tables = soup.find_all('table')
                    print(f"\nFound {len(tables)} <table> elements total")
                    
                    # Look for schedule container
                    schedule_divs = soup.find_all('div', class_=lambda x: x and 'schedule' in x.lower())
                    print(f"Found {len(schedule_divs)} divs with 'schedule' in class name")
            
            # Look for links that might be game links
            print("\n--- Looking for game links ---")
            all_links = soup.find_all('a', href=True)
            game_links = [link for link in all_links if '/game/' in link.get('href', '')]
            print(f"Found {len(game_links)} links containing '/game/'")
            
            if game_links:
                print("\nFirst 5 game links:")
                for i, link in enumerate(game_links[:5], 1):
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    print(f"  {i}. {href}")
                    print(f"     Text: {text}")
            
            # Look for team names
            print("\n--- Looking for team names ---")
            team_links = soup.find_all('a', class_=lambda x: x and 'team' in str(x).lower())
            print(f"Found {len(team_links)} links with 'team' in class name")
            
            if team_links:
                print("\nFirst 10 team links:")
                for i, link in enumerate(team_links[:10], 1):
                    text = link.get_text(strip=True)
                    classes = link.get('class', [])
                    print(f"  {i}. {text} (classes: {classes})")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


def debug_game_page():
    """Debug a specific game page structure."""
    print("\n" + "=" * 80)
    print("DEBUGGING GAME PAGE")
    print("=" * 80)
    
    # Test with the Campbell at Penn State game
    url = "https://www.espn.com/mens-college-basketball/game/_/gameId/401827278"
    
    print(f"\nURL: {url}")
    print("\nFetching page...")
    
    with Scraper() as scraper:
        try:
            soup = scraper.get_soup(url)
            print("✓ Page fetched successfully")
            
            # Save the full HTML for inspection
            with open('game_page_debug.html', 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
            print("✓ Saved full HTML to: game_page_debug.html")
            
            # Look for percentage values
            print("\n--- Looking for percentages ---")
            import re
            
            # Search in all text
            all_text = soup.get_text()
            percent_pattern = r'\d+\.?\d*%'
            percentages = re.findall(percent_pattern, all_text)
            print(f"Found {len(percentages)} percentage values in page text")
            
            if percentages:
                print("\nAll percentages found:")
                for i, pct in enumerate(percentages, 1):
                    print(f"  {i}. {pct}")
            
            # Look for specific predictor sections
            print("\n--- Looking for predictor sections ---")
            
            # Try various selectors
            selectors = [
                ('div', {'class': 'Gamestrip__Odds'}),
                ('section', {'class': 'GameInfo'}),
                ('div', {'class': lambda x: x and 'predictor' in str(x).lower()}),
                ('div', {'class': lambda x: x and 'matchup' in str(x).lower()}),
                ('div', {'class': lambda x: x and 'probability' in str(x).lower()}),
            ]
            
            for tag, attrs in selectors:
                elements = soup.find_all(tag, attrs)
                class_desc = str(attrs.get('class', 'with lambda'))
                print(f"  <{tag} class='{class_desc}'>: {len(elements)} found")
            
            # Look for team names
            print("\n--- Looking for team names ---")
            title = soup.find('title')
            if title:
                print(f"Page title: {title.get_text()}")
            
            h1_tags = soup.find_all('h1')
            print(f"\nFound {len(h1_tags)} <h1> tags:")
            for h1 in h1_tags[:3]:
                print(f"  {h1.get_text(strip=True)}")
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


def main():
    """Main debug function."""
    print("\n" + "=" * 80)
    print("ESPN SCRAPER DEBUG TOOL")
    print("=" * 80)
    print("\nThis script will:")
    print("1. Fetch the ESPN schedule page and analyze its structure")
    print("2. Fetch a game page and look for predictor data")
    print("3. Save HTML files for manual inspection")
    print("\n" + "=" * 80)
    
    success = True
    
    # Debug schedule page
    if not debug_schedule_page():
        success = False
    
    # Debug game page
    if not debug_game_page():
        success = False
    
    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)
    
    if success:
        print("\nHTML files saved:")
        print("  - schedule_page_debug.html")
        print("  - game_page_debug.html")
        print("\nOpen these files in a browser or text editor to inspect the structure.")
    else:
        print("\nSome errors occurred. Check the output above.")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

