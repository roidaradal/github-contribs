# Github Contributions 
# John Roy Daradal 

import json, requests, webbrowser, os, sys
import matplotlib.pyplot as plt 
from datetime import date
from bs4 import BeautifulSoup

Date = tuple[int,int,int]
DateRange = tuple[Date,Date]
IntPair = tuple[int,int]

HTML_URL: str = 'https://github.com/users/%s/contributions?from=%s'
API_URL : str = 'https://api.github.com/users/%s/events/public'
OUT_DIR : str = 'out'

def fetch_weekly_contributions():
    '''Fetch weekly contributions of usernames found in devs.json'''
    start, end = get_week()

    usernames = get_devs()
    max_length = max(len(username) for username in usernames)
    template = '%%-%ds\t%%3d\t%%s' % max_length

    total: dict[str, int] = {}
    count_levels: dict[str, list[IntPair]] = {}
    for username in get_devs():
        contribs = fetch_contributions(username, (start, end))
        count_levels[username] = get_count_levels(contribs, (start, end))
        total[username] = sum(count for (count,_) in contribs.values())
        details = ' '.join('%5s' % ('%d|%d' % (count,level)) for count,level in count_levels[username])
        print(template % (username, total[username], details))

    title = 'GitHub Contributions from %s to %s' % (date_to_string(start), date_to_string(end))
    filename = create_filename((start, end))
    entries = sorted(total.items(), key=lambda x: x[1])
    names: list[str] = [x[0] for x in entries]
    counts: list[int] = [x[1] for x in entries]

    if not os.path.exists(OUT_DIR): os.mkdir(OUT_DIR)
    
    _, ax = plt.subplots()
    bars = plt.barh(names, counts)
    ax.bar_label(bars, label_type='edge', padding=5)
    plt.title(title)
    plt.xlabel('Contribs')
    plt.ylabel('Devs')
    path = '%s/%s.png' % (OUT_DIR, filename)
    plt.savefig(path, bbox_inches='tight')

    reps: dict[str, str] = {}
    reps['Title'] = title
    reps['Filename'] = filename
    tbl: list[str] = []
    for username in reversed(names):
        tbl.append('<tr>')
        tbl.append('<td>%s</td>' % username)
        for count, level in count_levels[username]:
            tbl.append('<th class="level%d">%d</th>' % (level, count))
        tbl.append('</tr>')
    reps['Table'] = ''.join(tbl)
    create_output(filename, reps)

def fetch_contributions(username: str, date_range: DateRange) -> dict[str, IntPair]:
    ''' Returns dict{username => (count, level)}'''
    # Start from January 1 of current year
    year_start = date_to_string((date_range[0][0], 1, 1))
    url = HTML_URL % (username, year_start)

    # Fetch HTML page and use BeautifulSoup
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')

    # Get contributions
    start_date, end_date = [date_to_string(d) for d in date_range]
    contribs: dict[str, IntPair] = {}
    cells = soup.select('td.ContributionCalendar-day')
    for cell in cells:
        cell_date = str(cell['data-date'])
        if not (start_date <= cell_date <= end_date): continue # skip if not within date range

        # Find the tooltip associated with td cell
        tooltip = soup.find('tool-tip', attrs={'for': cell['id']})

        # Extract the count from tooltip's inner text
        text = 'No'
        if tooltip: text = tooltip.get_text()

        count_text = text.strip().split()[0]
        count = 0 if count_text == 'No' else int(count_text)
        level = int(str(cell['data-level']))
        contribs[cell_date] = (count, level)
    return contribs

################### UTILITY FUNCTIONS #########################

def get_week() -> DateRange:
    '''Get week from week=yyyy-mm-dd argument. Defaults to current week.'''
    for arg in sys.argv[1:]:
        if arg.startswith('week='):
            p = [int(x, 10) for x in arg.split('=')[1].split('-')]
            return get_week_of(date(p[0], p[1], p[2]))
        
    # Default: Current week
    return get_week_of(date.today())

def get_week_of(d: date) -> DateRange:
    # For now, assumes same month 
    # TODO: fix for week that spans two months
    year, month, day = d.year, d.month, d.day 
    start_day = day - d.weekday() # start at Monday 
    end_day = start_day + 4 # end at Friday
    return (year, month, start_day), (year, month, end_day)

def date_from_string(d: str) -> Date:
    '''Converts yyyy-mm-dd string to (yy,mm,dd) date'''
    parts = [int(x) for x in d.split('-')]
    return (parts[0], parts[1], parts[2])

def date_to_string(d: Date, glue: str = '-') -> str:
    '''Converts (yy,mm,dd) to yyyy-mm-dd string. Can also pass in custom glue instead of `-`'''
    yy, mm, dd = d 
    return '%d%s%.2d%s%.2d' % (yy, glue, mm, glue, dd)

def get_devs() -> list[str]:
    '''Load list of usernames from devs.json'''
    path = 'devs.json'
    if not os.path.exists(path):
        print('Error: missing `devs.json` file')
        sys.exit(1)

    f = open(path, 'r')
    devs: list[str] = json.load(f)
    f.close()
    return devs

def get_count_levels(contribs: dict[str, IntPair], date_range: DateRange) -> list[IntPair]:
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
            count, level  = contribs[key]
        pairs.append((count, level))
    return pairs

def create_output(filename: str, reps: dict[str, str]):
    '''Create output HTML file, replace template placeholders, save HTML file and open in browser'''
    f = open('template.html', 'r')
    body = ''.join(line for line in f.readlines())
    f.close()

    for key, replacement in reps.items():
        key = '%%%s%%' % key 
        body = body.replace(key, replacement)

    path = '%s/%s.html' % (OUT_DIR, filename)
    f = open(path, 'w')
    f.write(body)
    f.close() 

    # Open html file 
    full_path = os.path.abspath(path)
    url = 'file://' + full_path 
    webbrowser.open_new_tab(url)

def create_filename(date_range: DateRange) -> str: 
    '''Create yyyymmdd_yyyymmdd filename from DateRange'''
    start, end = date_range 
    start_date = date_to_string(start, glue='')
    end_date   = date_to_string(end  , glue='')
    return '%s_%s' % (start_date, end_date)

if __name__ == '__main__':
    fetch_weekly_contributions()

'''
TODO
[ ] Fix range that spans two months (e.g. last week of Jan - first week of Feb)
    - get_count_levels
    - get_week_of
[ ] Detect current month automatically 
[ ] Generate monthly report
    - Separate into days (Mon-Fri) + weekends 
[ ] Use Github API for public events
[ ] Measure weight of activity (e.g. create repo = 1, commit with 2 lines of change vs 100 updates)
'''