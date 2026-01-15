# github-contribs 

Python tool for pulling GitHub contribution count of GitHub users

## Usage 
Prepare a JSON file which contains the list of GitHub usernames (default: `devs.json`)

Run `python main.py (week=yyyy-mm-dd) (input=devs.json)` 

This will pull the users' GitHub pages, and generate a report of their contributions for the week.

## Options
* `week=yyyy-mm-dd` - used to generate a weekly report for a custom week (default: current week)
* `input=devs.json` - used to set a different input file path (default: `devs.json`)

## Dependencies
* `requests` - for making HTTP requests
* `BeautifulSoup4` - for traversing HTML DOM
* `matplotlib` - for bar graph