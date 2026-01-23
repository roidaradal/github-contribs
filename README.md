# github-contribs 

Python script for pulling public GitHub contribution count of GitHub users

## Usage 
Prepare a text file which contains the list of GitHub usernames (default: `devs.txt`)

Run:

```bash
python github.py (date=yyyy-mm-dd) (input=devs.txt) 
```

This will look at the users' GitHub pages, and generate a report of their contributions for the month.

## Options
* `date=yyyy-mm-dd` - used to generate a monthly report for a custom month (default: current month)
* `input=devs.txt` - used to set a different input file path (default: `devs.txt`)

## Dependencies
* [`requests`](https://pypi.org/project/requests/) - for making HTTP requests
* [`BeautifulSoup4`](https://pypi.org/project/beautifulsoup4/) - for traversing HTML DOM
* [`matplotlib`](https://pypi.org/project/matplotlib/) - for bar graph