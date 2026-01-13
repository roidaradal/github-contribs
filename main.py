# Github Contributions 
# John Roy Daradal 

import json, requests, webbrowser, os
import matplotlib.pyplot as plt 
from datetime import date
from bs4 import BeautifulSoup

Date = tuple[int,int,int]
DateRange = tuple[Date,Date]
IntPair = tuple[int,int]

HTML_URL: str = 'https://github.com/users/%s/contributions?from=%s'
API_URL : str = 'https://api.github.com/users/%s/events/public'

class Contrib:
    def __init__(self):
        self.count: int = 0 
        self.level: int = 0
    
    def __repr__(self) -> str:
        return str(self.count)

def fetch_dev_contributions():
    start, end = get_current_week()
    count: dict[str, int] = {}
    levels: dict[str, list[IntPair]] = {}
    for username in get_devs():
        contribs = fetch_contributions(username, (start, end))
        levels[username] = get_count_levels(contribs, (start, end))
        count[username] = sum([x.count for x in contribs.values()])
        print(username, count[username], levels[username])

    title = 'GitHub Contributions from %s to %s' % (date_to_string(start), date_to_string(end))
    entries = sorted(count.items(), key=lambda x: x[1])
    names: list[str] = [x[0] for x in entries]
    counts: list[int] = [x[1] for x in entries]
    
    _, ax = plt.subplots()
    bars = plt.barh(names, counts)
    ax.bar_label(bars, label_type='edge', padding=5)
    plt.title(title)
    plt.xlabel('Contribs')
    plt.ylabel('Devs')
    plt.savefig('out.png', bbox_inches='tight')

    reps: dict[str, str] = {}
    reps['Title'] = title
    tbl: list[str] = []
    for username in reversed(names):
        tbl.append('<tr>')
        tbl.append('<td>%s</td>' % username)
        for num, level in levels[username]:
            tbl.append('<th class="level%d">%d</th>' % (level, num))
        tbl.append('</tr>')
    reps['Table'] = ''.join(tbl)
    create_grid_file(reps)

def fetch_contributions(username: str, date_range: DateRange) -> dict[str, Contrib]:
    # Start from January 1 of current year
    year_start = '%d-01-01' % date.today().year
    url = HTML_URL % (username, year_start)

    # Fetch HTML page and use BeautifulSoup
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')

    # Get contributions
    start, end = date_range
    start_date = date_to_string(start)
    end_date = date_to_string(end)
    contribs: dict[str, Contrib] = {}
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
        contrib = Contrib()
        contrib.count = 0 if count == 'No' else int(count)
        contrib.level = int(str(cell['data-level']))
        contribs[cell_date] = contrib
    return contribs

################### UTILITY FUNCTIONS #########################

def get_current_week() -> DateRange:
    # For now, assumes same month 
    # TODO: fix for week that spans two months
    today = date.today()
    year, month, day = today.year, today.month, today.day 
    start_day = day - today.weekday() # start at Monday
    end_day = start_day + 4
    return (year, month, start_day), (year, month, end_day)

def date_to_string(d: Date) -> str:
    yy, mm, dd = d 
    return '%d-%.2d-%.2d' % (yy, mm, dd)

def get_devs() -> list[str]:
    f = open('devs.json', 'r')
    devs: list[str] = json.load(f)
    f.close()
    return devs

def get_count_levels(contribs: dict[str, Contrib], date_range: DateRange) -> list[IntPair]:
    pairs: list[IntPair] = []
    # For now, assumes same month
    # TODO: fix date range that spans two months

    start, end = date_range
    year, month = start[0:2]
    start_day = start[2]
    last_day = end[2]
    for day in range(start_day, last_day+1):
        key = date_to_string((year, month, day))
        count, level = 0, 0
        if key in contribs:
            count = contribs[key].count
            level = contribs[key].level
        pairs.append((count, level))
    return pairs

def create_grid_file(reps: dict[str, str]):
    f = open('template.html', 'r')
    body = ''.join(line for line in f.readlines())
    f.close()

    for key, replacement in reps.items():
        key = '%%%s%%' % key 
        body = body.replace(key, replacement)

    path = 'out.html'
    f = open(path, 'w')
    f.write(body)
    f.close() 

    # Open html file 
    full_path = os.path.abspath(path)
    url = 'file://' + full_path 
    webbrowser.open_new_tab(url)

if __name__ == '__main__':
    fetch_dev_contributions()

'''
TODO
[ ] Fix range that spans two months (e.g. last week of Jan - first week of Feb)
    - get_count_levels
    - get_current_week
[ ] Detect current month automatically 
[ ] Generate monthly report
    - Separate into days (Mon-Fri) + weekends 
[ ] Use Github API for public events
'''