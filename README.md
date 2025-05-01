MapPhone Extractor - Free Google Maps Phone Scraper
MapPhone Extractor is a free phone number scraper designed to extract business names, website URLs, and phone numbers from Google Maps. Perfect for lead generation, this business phone extractor targets industries like dental clinics or restaurants in any location (e.g., "dental clinics in London"). With a modern web interface, visible Chrome browser automation, and user-controlled scraping, it maximizes Google Maps pages to collect up to 150 businesses, pausing every 30 for user permission. Available as a standalone executable for non-technical users! Clone from GitHub for efficient business phone scraping!
Why Choose MapPhone Extractor?
MapPhone Extractor is a powerful Google Maps phone extractor with:

Free Phone Scraper: Open-source and standalone executable.
Google Maps Integration: Scrapes 150+ business names, URLs, and phone numbers.
Lead Generation Tool: Targets 100+ phone numbers per search.
Visible Automation: Chrome browser shows live scraping.
User-Controlled: Pauses every 30 businesses for permission.
Modern UI: Sleek design with animated progress bar and modals.
No Setup for Users: Executable runs without Python installation.

Key Features

Free Business Phone Finder: Collects 100+ phone numbers with business names.
Google Maps Scraper: Maximizes pages in ~300 seconds.
CSV Output: Saves websites.csv (names, URLs) and phones.csv (names, URLs, phones).
Ctrl+C Support: Stops scraping gracefully with progress saved.
Batch Processing: Pauses after every 30 businesses for confirmation.
Improved UI: Animated, responsive design with Tailwind CSS.
Standalone Executable: Runs on Windows, macOS, or Linux without setup.

Project Structure
mapphone/
├── scrape_maps_phones.py       # Scrapes business names, URLs, phone numbers
├── app.py                     # Flask API with batch processing
├── launch.py                  # Launches Flask and browser for executable
├── templates/
│   └── index.html            # Modern UI with modals
├── static/
│   ├── css/
│   │   └── styles.css       # Custom styles
│   └── js/
│       └── script.js        # Frontend logic
├── requirements.txt           # Dependencies
├── Dockerfile                # For cloud deployment
├── .gitignore                # Excludes temporary files
├── websites.csv              # CSV with names, URLs
├── phones.csv                # CSV with names, URLs, phone numbers
├── README.md                 # Documentation
└── README.txt                # User instructions for executable

Requirements for Development
For developers building the executable:

Python: 3.6+
Dependencies:
flask
selenium
webdriver-manager
gunicorn
pyinstaller


Browser: Google Chrome
System: Linux (tested on Ubuntu), macOS, or Windows

Requirements for End Users
For non-technical users running the executable:

Browser: Google Chrome (pre-installed)
System: Windows, macOS, or Linux
No Python or dependencies required

Setup Instructions for Developers

Clone Repository:
git clone https://github.com/sheryarkayani/MapPhone-Extractor.git
cd MapPhone-Extractor


Install Dependencies:
pip install --upgrade -r requirements.txt
pip install pyinstaller

Verify:
pip list


Install Google Chrome:Check:
google-chrome --version

Install (Ubuntu):
sudo apt update
sudo apt install google-chrome-stable


Set Permissions:
chmod u+w .


Create Directories:
mkdir -p templates static/css static/js


Test Locally:
python3 app.py

Open http://localhost:5000.

Create Executable:
pyinstaller --name MapPhoneExtractor \
    --add-data "templates;templates" \
    --add-data "static;static" \
    --add-data "scrape_maps_phones.py;." \
    --add-data "app.py;." \
    --hidden-import flask \
    --hidden-import selenium \
    --hidden-import webdriver_manager \
    --collect-all webdriver_manager \
    --onefile launch.py


Create Zip:
mkdir MapPhoneExtractor
cp dist/MapPhoneExtractor README.txt MapPhoneExtractor/
zip -r MapPhoneExtractor_[OS].zip MapPhoneExtractor/

Replace [OS] with Windows, macOS, or Linux.

Test Executable:Unzip and double-click MapPhoneExtractor (or run ./MapPhoneExtractor on macOS/Linux).


Instructions for Non-Technical Users

Download Zip:Get MapPhoneExtractor_[OS].zip for your system (Windows, macOS, or Linux).

Unzip:Extract to a folder (e.g., Desktop/MapPhoneExtractor).

Install Google Chrome:If not installed, download from https://www.google.com/chrome/.

Run:Double-click MapPhoneExtractor (or MapPhoneExtractor.exe on Windows).

Use:

Browser opens to http://localhost:5000.
Enter a search term (e.g., dental clinics in London).
Click “Start Scraping” and confirm in the pop-up.
Confirm every 30 businesses to continue.
View results in the table and download CSVs.
Stop by pressing Ctrl+C in the terminal or closing the window.



How to Use MapPhone Extractor
Web Interface

Open: Double-click the executable; browser opens to http://localhost:5000.
Enter Search Term: e.g., dental clinics in London.
Start Scraping: Click "Start Scraping", confirm in modal.
Batch Permission:
Modal prompts every 30 businesses (5 pauses for 150 businesses).
Click "Proceed" or "Cancel".


Watch Chrome:
Searches Google Maps, paginates, collects ~150 businesses.
Extracts phone numbers directly from Maps.


Monitor Progress:
Console: “Visiting: {url}”, “Found phone: {phone}”.
UI: Animated progress bar, messages like “Processing batch 2...”.


View Results: Table shows business names, websites, phone numbers.
Download CSVs: Get websites.csv and phones.csv.
Stop Scraping: Press Ctrl+C in terminal.

Example Output

Enter: dental clinics in London
Chrome:
Searches Google Maps, paginates all pages.
Visits ~150 businesses, extracts details.


UI:
Modal: “Start Scraping?”, “Continue Batch 2?”
Table: Notting Hill Dental, https://..., +442012345678


CSVs:
websites.csv: ~150 businesses
phones.csv: 100+ phone numbers



CSV File Formats
websites.csv
Business Name,Website
Notting Hill Dental,https://www.nottinghilldentalclinic.com/
Chelsea Dental,https://www.chelseadentalclinic.co.uk/
...

phones.csv
Business Name,Website,Phone
Notting Hill Dental,https://www.nottinghilldentalclinic.com/,+442012345678
Chelsea Dental,https://www.chelseadentalclinic.co.uk/,+442098765432
...

Troubleshooting
Chrome Not Opening

Install Chrome: https://www.google.com/chrome/.
Restart the executable.

No Businesses Found

Try dentists in London.
Check internet connection.

Fewer Phone Numbers

Check websites.csv for 150+ entries.
Test search term manually on Google Maps.
Contact support.

UI Issues

Refresh http://localhost:5000.
Close and restart the executable.

Executable Fails

Ensure Chrome is installed.
Check disk space.
Contact: https://github.com/sheryarkayani/MapPhone-Extractor/issues.

SEO-Optimized Keywords

Free phone number scraper
Google Maps phone extractor
Business phone finder
Dental clinics phone scraper
Free Google Maps scraper
Lead generation tool
Business phone extractor
Phone number scraper
Phone finder for marketing
Visible browser automation
User-controlled scraping
Standalone phone scraper

Contributing

Fork: https://github.com/sheryarkayani/MapPhone-Extractor.
Branch:git checkout -b feature/new-feature


Commit:git commit -m 'Add new feature'


Push:git push origin feature/new-feature


Open Pull Request.

License
MIT License. See LICENSE.
Contact
Issues? Open an issue on GitHub or contact @sheryarkayani.

Free Google Maps phone scraper for lead generation. Features visible browser automation, user-controlled batch processing, standalone executable, and modern UI. Last updated: May 2, 2025
