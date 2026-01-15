# Github Contributions 
# John Roy Daradal 

import os, sys, json
import requests, webbrowser
import io, base64
import matplotlib.pyplot as plt 
from datetime import date, timedelta
from bs4 import BeautifulSoup

Date = tuple[int,int,int]
DateRange = tuple[Date,Date]
IntPair = tuple[int,int]

HTML_URL: str = 'https://github.com/users/%s/contributions?from=%s'
API_URL : str = 'https://api.github.com/users/%s/events/public'
OUT_DIR : str = 'out'

class Config:
    def __init__(self):
        self.date_range: DateRange = get_week_of(date.today())  # Default: Current week 
        self.input_path: str = 'devs.json'                      # Default: devs.json

def fetch_weekly_contributions():
    '''Fetch weekly contributions of usernames found in input_path'''
    cfg = get_config()
    start, end = cfg.date_range

    usernames = get_devs(cfg)
    max_length = max(len(username) for username in usernames)
    template = '%%-%ds\t%%3d\t%%s' % max_length

    total: dict[str, int] = {}
    count_levels: dict[str, list[IntPair]] = {}
    for username in usernames:
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
    
    _, ax = plt.subplots(figsize=(6,4))
    bars = plt.barh(names, counts)
    ax.bar_label(bars, label_type='edge', padding=5)
    plt.xlabel('Contribs')
    plt.ylabel('Devs')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()

    # Encode image data to base64 string
    buf.seek(0) # Rewind buffer back to start
    img_bytes = base64.b64encode(buf.getvalue())
    buf.close()
    img_string = img_bytes.decode('utf-8')

    reps: dict[str, str] = {}
    reps['Title'] = title
    reps['ImgData'] = img_string
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
    ''' Returns dict{date => (count, level)} contributions of username'''
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

def get_config() -> Config:
    '''Build Config object from command-line arguments and default values'''
    cfg = Config()
    for arg in sys.argv[1:]:
        if arg.startswith('week='):
            given_date = arg.split('=')[1]
            cfg.date_range = get_week_of(date(*date_from_string(given_date)))
        elif arg.startswith('input='):
            cfg.input_path = arg.split('=')[1]
    return cfg

def get_week_of(d: date) -> DateRange:
    '''Gets the Monday-Friday DateRange of the given date'''
    start = d - timedelta(days=d.weekday()) # Adjust from current date -> Monday
    end = start + timedelta(days=4)         # Add 4 days from Monday -> Friday
    return (start.year, start.month, start.day), (end.year, end.month, end.day)

def date_from_string(d: str) -> Date:
    '''Converts yyyy-mm-dd string to (yy,mm,dd) date'''
    parts = [int(x, 10) for x in d.split('-')]
    return (parts[0], parts[1], parts[2])

def date_to_string(d: Date, glue: str = '-') -> str:
    '''Converts (yy,mm,dd) to yyyy-mm-dd string. Can also pass in custom glue instead of `-`'''
    yy, mm, dd = d 
    return '%d%s%.2d%s%.2d' % (yy, glue, mm, glue, dd)

def get_devs(cfg: Config) -> list[str]:
    '''Load list of usernames from input_path (default: devs.json)'''
    path = cfg.input_path
    if not os.path.exists(path):
        print('Error: path `%s` does not exist' % path)
        sys.exit(1)

    f = open(path, 'r')
    devs: list[str] = json.load(f)
    f.close()
    return devs

def get_count_levels(contribs: dict[str, IntPair], date_range: DateRange) -> list[IntPair]:
    '''Get the (count,level) for each day in the date range'''
    pairs: list[IntPair] = []
    start, end = [date(*d) for d in date_range]
    curr = start 
    while curr <= end:
        key = str(curr)
        count, level = contribs.get(key, (0, 0))
        pairs.append((count, level))
        curr += timedelta(days=1)

    return pairs

def create_output(filename: str, reps: dict[str, str]):
    '''Create output HTML file, replace template placeholders, save HTML file and open in browser'''
    body = weekly_template[:]
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

weekly_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Contributions</title>
    <style>
        table {
            border-top: 1px solid black;
            border-left: 1px solid black;
            border-collapse: collapse;
            margin: 1em;
            float: left;
        }
        th, td {
            padding: 5px; 
            border-right: 1px solid black;
            border-bottom: 1px solid black;
        }
        th.level0 {
            color: white;
            background-color: #151b23;
        }
        th.level1 {
            color: white;
            background-color: #033a16;
        }
        th.level2 {
            background-color: #196c2e;   
        }
        th.level3 {
            background-color: #2ea043;
        }
        th.level4 {
            background-color: #56d364;
        }
        img {
            float: left;
        }
    </style>
</head>
<body>
<table>
    <thead>
        <tr>
            <th colspan="6">%Title%</th>
        </tr>
        <tr>
            <th>Dev</th>
            <th>Mon</th>
            <th>Tue</th>
            <th>Wed</th>
            <th>Thu</th>
            <th>Fri</th>
        </tr>
    </thead>
    <tbody>%Table%</tbody>
</table>
<img src="data:image/png;base64,%ImgData%" />
</body>
</html>
'''

if __name__ == '__main__':
    fetch_weekly_contributions()

'''
TODO
[ ] Save img as base64 and render directly (no saving of separate png file)
[ ] Detect current month automatically 
[ ] Generate monthly report
    - Separate into days (Mon-Fri) + weekends 
[ ] Use Github API for public events
[ ] Measure weight of activity (e.g. create repo = 1, commit with 2 lines of change vs 100 updates)
[ ] Convert to webapp
'''