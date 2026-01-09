# Github Contributions 
# John Roy Daradal 

import requests
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
    start_date = date_to_string(START_DATE)
    end_date = date_to_string(END_DATE)

    # Fetch HTML page and use BeautifulSoup
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')

    # Get contributions
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
        if count != 'No':
            contribs[cell_date] = int(count)

    return contribs


def date_to_string(d: Date) -> str:
    yy, mm, dd = d 
    return '%d-%.2d-%.2d' % (yy, mm, dd)

if __name__ == '__main__':
    username = 'roidaradal'
    contribs = fetch_contributions(username)
    print(username, sum(contribs.values()))
    for k, v in sorted(contribs.items()):
        print(k, v)