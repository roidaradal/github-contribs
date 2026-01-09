# Github Contributions 
# John Roy Daradal 

import json, requests
import matplotlib.pyplot as plt 
import numpy as np
from datetime import date
from bs4 import BeautifulSoup

Date = tuple[int,int,int]

HTML_URL: str = 'https://github.com/users/%s/contributions?from=%s'
API_URL : str = 'https://api.github.com/users/%s/events/public'

START_DATE: Date = (2026,1,5)
END_DATE  : Date = (2026,1,9)

def fetch_contributions(username: str) -> dict[str,int]:
    # Start from January 1 of current year
    start = '%d-01-01' % date.today().year
    url = HTML_URL % (username, start)

    # Fetch HTML page and use BeautifulSoup
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')

    # Get contributions
    start_date = date_to_string(START_DATE)
    end_date = date_to_string(END_DATE)
    contribs: dict[str, int] = {}
    cells = soup.select('td.ContributionCalendar-day')
    for cell in cells:
        cell_date = str(cell['data-date'])
        if not (start_date <= cell_date <= end_date): continue # skip if not within date range

        # Find the tooltip associated with td cell
        tooltip = soup.find('tool-tip', attrs={'for': cell['id']})

        # Extract the count from tooltip's inner text
        text = 'No'
        if tooltip: text = tooltip.get_text()

        count = text.strip().split()[0]
        contribs[cell_date] = 0 if count == 'No' else int(count)

    return contribs

def fetch_dev_contributions():
    f = open('devs.json', 'r')
    devs: list[str] = json.load(f)
    f.close()

    count: dict[str, int] = {}
    for username in devs:
        contribs = fetch_contributions(username)
        count[username] = sum(contribs.values())
        print(username, count[username])

    entries = sorted(count.items(), key=lambda x: x[1])
    names: list[str] = [x[0] for x in entries]
    counts: list[int] = [x[1] for x in entries]

    _, ax = plt.subplots()
    bars = plt.barh(names, counts)
    ax.bar_label(bars, label_type='edge', padding=5)
    plt.title('GitHub Contributions from %s to %s' % (date_to_string(START_DATE), date_to_string(END_DATE)))
    plt.xlabel('Contribs')
    plt.ylabel('Devs')

    plt.show()

def date_to_string(d: Date) -> str:
    yy, mm, dd = d 
    return '%d-%.2d-%.2d' % (yy, mm, dd)

if __name__ == '__main__':
    fetch_dev_contributions()

'''
TODO:
[ ] Detect current week (Mon-Fri) automatically
[ ] Detect current month automatically 
[ ] Separate into days (Mon-Fri) + weekends 
[ ] Colored graphs similar to Github's contribs grid
[ ] Use Github API for public events
'''