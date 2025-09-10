# HUS Sotkanet Health Dashboard

A web-based dashboard for visualizing health and social indicators for the Hospital District of Helsinki and Uusimaa (HUS) region using data from the Sotkanet API.

## Features

- **Multi-language Support**: Available in Finnish, Swedish, and English
- **Interactive Visualizations**: Line and bar charts for indicator trends
- **Real-time Data**: Fetches latest data from Sotkanet REST API
- **Responsive Design**: Works on desktop and mobile devices
- **Data Export**: Download all displayed data as CSV
- **Caching**: Smart caching to reduce API calls and improve performance
- **Gender Filtering**: View data by total, male, or female populations

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. **Extract the ZIP file**
   ```bash
   # Extract the provided hus-sotkanet-dashboard.zip file to your desired location
   # For example on Windows: right-click and "Extract All..."
   # On macOS/Linux: unzip hus-sotkanet-dashboard.zip
   
   # Navigate to the extracted directory
   cd hus-sotkanet-dashboard
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment** (optional)
   
   The application comes with a `.env` file with default settings. You can modify it if needed:
   ```env
   APP_ENV=production  # Options: development, production, testing
   CACHE_ENABLED=true
   CACHE_TTL=3600
   LOG_LEVEL=INFO
   ```

## Usage

### Running the Dashboard

1. **Start the application**
   ```bash
   python app.py
   ```
   
   Or with custom settings:
   ```bash
   python app.py --port 8050 --host 127.0.0.1 --debug
   ```

2. **Open in browser**
   
   Navigate to `http://127.0.0.1:8050` in your web browser

### Using the Dashboard

- **Select Years**: Use the range slider to choose the time period
- **Chart Type**: Toggle between line and bar charts
- **Gender Filter**: View data for total population, males, or females
- **Language**: Switch between Finnish, Swedish, and English
- **Info Button (ℹ)**: Click to see metadata for each indicator
- **Refresh Data**: Click to fetch latest data from Sotkanet
- **Download Data**: Export all displayed data as CSV

## Project Structure

```
hus-sotkanet-dashboard/
├── api/                 # Sotkanet API client
├── assets/             # CSS styles
├── config/             # Configuration and settings
├── dashboard/          # Dashboard layout and callbacks
├── data/               # Data fetching and processing
├── logs/               # Application logs
├── scripts/            # Utility scripts
├── utils/              # Logging and utilities
├── app.py              # Main application
├── requirements.txt    # Python dependencies
└── .env               # Environment configuration
```

## Scripts

### Fetch Metadata
Update indicator metadata from Sotkanet:
```bash
python scripts/fetch_metadata.py

# With validation
python scripts/fetch_metadata.py --validate
```

## Configuration

### Indicators
The dashboard displays different sets of indicators based on the environment:
- **Development**: 3 core indicators
- **Production**: 6 comprehensive indicators  
- **Testing**: 1 indicator for unit tests

Modify `config/settings.py` to customize indicator sets.

### Region
Default region is HUS (ID: 629). This can be changed in `config/settings.py`.

## Data Source

**Tietolähde: Sotkanet / THL (Creative Commons Attribution 4.0, http://www.sotkanet.fi/)**

All health and social indicator data is sourced from [Sotkanet](http://www.sotkanet.fi/), provided by THL (Finnish Institute for Health and Welfare) under Creative Commons Attribution 4.0 license.

The application fetches data in real-time from the Sotkanet REST API and displays it with proper attribution in the dashboard footer.

## Troubleshooting

- **No data displayed**: Check logs in `logs/app.log` for API errors
- **Slow performance**: Ensure caching is enabled in `.env`
- **Connection errors**: Verify internet connection and Sotkanet API availability

## Development

### Environment Setup
```bash
# Set development environment
export APP_ENV=development  # Linux/macOS
set APP_ENV=development     # Windows
```

### Clear Cache
```python
from data.fetcher import SotkanetDataFetcher
fetcher = SotkanetDataFetcher()
fetcher.clear_cache()
```

## License

TBD

## Contact

matti.manninen@gwlnetworks.com