# Test Results - December 1, 2025

## Test Run Summary

✅ **All tests passed successfully**

### Test Configuration
- Test date: December 1, 2025
- Target dates: Dec 1-3, 2025
- Conference: Big Ten (group 7)
- Scraper: Chrome on macOS user agent

### Results

#### December 1, 2025
- Games found: 0
- Status: ✅ Correct (no games scheduled)

#### December 2, 2025
- Games found: 5
- Predictors extracted: 5/5 (100%)
- Games:
  1. Campbell @ Penn State - 9.3% / 90.7% ✅
  2. Iowa @ Michigan State - 22.8% / 77.2% ✅
  3. Purdue @ Rutgers - 86.8% / 13.2% ✅
  4. Wagner @ Maryland - 2.1% / 97.9% ✅
  5. USC @ Oregon - 56.9% / 43.1% ✅

#### December 3, 2025
- Games found: 3
- Predictors extracted: 3/3 (100%)
- Games:
  1. Indiana @ Minnesota - 81.5% / 18.4% ✅
  2. Northwestern @ Wisconsin - 24.3% / 75.7% ✅
  3. UCLA @ Washington - 65.2% / 34.8% ✅

### Overall Statistics
- **Total games found:** 8
- **Predictor success rate:** 100% (8/8)
- **Average processing time:** ~1.5 seconds per game
- **No errors or exceptions**

### Verification

The Campbell @ Penn State game was manually verified:
- Expected: Campbell 9.3%, Penn State 90.7%
- Scraped: Campbell 9.3%, Penn State 90.7%
- **Match:** ✅

### Conclusion

The scraper is now fully functional and accurately extracting:
1. Game schedules from ESPN's JSON data structure
2. Team names in correct away/home order
3. Win probability percentages from SVG elements
4. Correct percentage-to-team assignments

All fixes have been tested and validated against live ESPN data.
