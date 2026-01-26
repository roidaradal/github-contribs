# Github Contributions 
# John Roy Daradal 

import calendar, os, sys
import json, requests, webbrowser
from pathlib import Path, PurePath
from datetime import date, datetime
from bs4 import BeautifulSoup

LIMIT: int = 9
HTML_URL: str = 'https://github.com/users/%s/contributions?from=%s' # (username, start_date)
API_URL : str = 'https://api.github.com/users/%s/events/public'
OUT_DIR : str = '.contribs'

IntPair = tuple[int,int]
Contribs = dict[str, IntPair]

class Config:
    def __init__(self):
        self.date: date = date.today()
        self.path: str = 'devs.txt'
        self.cached: bool = False 
        self.weekends: bool = False

color_reset = '\033[0m'
green   = lambda text: '\033[32m%s%s' % (text, color_reset)
yellow  = lambda text: '\033[33m%s%s' % (text, color_reset)
cyan    = lambda text: '\033[36m%s%s' % (text, color_reset)

def main():
    '''Main function'''

    # Output dir = ~/.contribs
    outDir = Path.home().joinpath(OUT_DIR)
    if not outDir.exists(): os.mkdir(outDir)

    # Get config (user_date, input_path)
    cfg = get_config()
    filename = get_filename(cfg.date, cfg.path)
    month = cfg.date.strftime('%B %Y')
    weeks = get_month_weeks(cfg.date)
    week_index = get_week_of(cfg.date, weeks)

    # Setup paths 
    json_path = outDir.joinpath(f'{filename}.json')
    html_path = outDir.joinpath(f'{filename}.html')

    # Get contributions (from cache or by requesting)
    contribs: dict[str, Contribs] = {}
    if cfg.cached and json_path.exists():
        # Load from cache
        with open(json_path, 'r') as f:
            contribs = json.load(f)
    else:
        # Get usernames
        usernames = get_usernames(cfg.path)
        max_length = max(len(cyan(uname)) for uname in usernames)
        template = '• %%-%ds\t\t%%3d' % max_length

        # Fetch contributions
        print('Fetching %s GitHub contributions from %s...' % (green(month), yellow(f'`{cfg.path}`')))
        for username in usernames:
            contribs[username] = fetch_user_month_contributions(username, cfg.date)
            total = sum(count for (count,_) in contribs[username].values())
            print(template % (cyan(username), total))

        # Save contribs to JSON file (cache)
        with open(json_path, 'w') as f:
            json.dump(contribs, f)

    # Create output HTML
    body, selected = create_body(contribs, weeks, week_index, month, cfg.weekends)
    reps: dict[str, str] = {
        'Title'     : f'{month} GitHub Contributions',
        'Sidebar'   : create_sidebar(weeks, week_index),
        'Body'      : body,
        'Selected'  : selected,     
    }
    create_output(reps, html_path)

def get_config() -> Config:
    '''Returns the chosen date (default: today) and input_path (default: ./devs.txt)'''
    cfg = Config()
    for arg in sys.argv[1:]:
        arg = arg.lower()
        if arg.startswith('date='):
            value = arg.split('=')[1]
            cfg.date = new_date(value)
        elif arg.startswith('input='):
            cfg.path = arg.split('=')[1]
        elif arg.startswith('from='):
            cfg.cached = arg.split('=')[1] == 'cache'
        elif arg.startswith('with='):
            cfg.weekends = arg.split('=')[1] in ('weekend', 'weekends')
    return cfg

def get_filename(d: date, path: str) -> str:
    '''Create output filename'''
    name = PurePath(path).stem
    return '%d%.2d_%s' % (d.year, d.month, name)

def get_usernames(file_path: str) -> list[str]:
    '''Load list of usernames from path (default: devs.txt)'''
    path = Path(file_path)
    if not path.exists():
        print(f'Error: path `{path}` does not exist')
        sys.exit(1)
    
    try:
        with open(path, 'r') as f:
            usernames = [line.strip() for line in f.readlines() if line.strip() != '']
        count = len(usernames)
        if count > LIMIT:
            print(f'Error: Found {count} usernames, exceeds limit ({LIMIT})')
            sys.exit(1)  
        return usernames
    except Exception as err:
        print('Error: ', err)
        sys.exit(1)

def get_month_weeks(d: date) -> list[list[int]]:
    '''Return list of week dates for given month'''
    # Note: This can also be achieved by calendar.monthcalendar, 
    # but it doesn't provide a week0 row if day 1 starts on Monday
    weeks: list[list[int]] = []

    # Get first weekday and last date of month
    first_day, last_date = calendar.monthrange(d.year, d.month)
    month_limit = last_date + 1

    # Process week 0 = first incomplete week
    curr = 0
    week0 = [0] * 7
    if first_day == 0:
        # If first day is Monday, week 0 is all 0s
        curr = 1
    else:
        # Create week 0
        last_day = 7 - first_day
        week0[first_day:] = list(range(1, last_day+1))
        curr = last_day + 1
    weeks.append(week0)

    # Process month weeks (max = week5) 
    for _ in range(5): 
        limit = min(curr + 7, month_limit)
        week = list(range(curr, limit))
        week += [0] * (7 - len(week)) # fill with 0s at back to ensure 7 days
        weeks.append(week)
        if limit == month_limit: break
        curr = limit
    return weeks

def get_week_of(d: date, weeks: list[list[int]]) -> int:
    '''Get week index of given date'''
    for i, week in enumerate(weeks):
        if d.day in week: return i
    return -1

def new_date(date_string: str) -> date:
    '''Create new date from date_string, defaults to today if given date_string is invalid'''
    try:
        given_date = datetime.strptime(date_string, '%Y-%m-%d')
        return given_date.date()
    except:
        return date.today()
    
def fetch_user_month_contributions(username: str, d: date) -> Contribs:
    '''Return dict{day => (count, level)} contributions of username for given month'''
    # Start GitHub page from January 1 of given year 
    year_start = date(d.year, 1, 1)
    url = HTML_URL % (username, str(year_start))
    
    # Setup the month date range
    last_month_day = calendar.monthrange(d.year, d.month)[1]
    month_start = str(date(d.year, d.month, 1))
    month_end   = str(date(d.year, d.month, last_month_day))

    # Fetch HTML page and use BeautifulSoup 
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'lxml')

    # Get contributions data
    contribs: Contribs = {}
    for cell in soup.select('td.ContributionCalendar-day'):
        cell_date = str(cell['data-date'])
        if not (month_start <= cell_date <= month_end): continue # skip if not within month range
        day = int(cell_date.split('-')[2], 10)

        # Find tooltip associated with td cell 
        tooltip = soup.find('tool-tip', attrs={'for': cell['id']})

        # Extract count from tooltip's inner text 
        text = 'No' # default: No contributions 
        if tooltip: text = tooltip.get_text()

        count_text = text.strip().split()[0]
        count = 0 if count_text == 'No' else int(count_text)
        level = int(str(cell['data-level']))
        contribs[str(day)] = (count, level)
    return contribs

def create_sidebar(weeks: list[list[int]], selected: int) -> str:
    '''Create sidebar content'''
    sidebar: list[str] = [
        '<div class="tab" id="tab-all" onclick="changeTab(\'all\')">Summary</div>'
    ]
    for week, days in enumerate(weeks):
        if week == 0 and sum(days) == 0: continue # skip if no week0

        active = "active" if selected == week else ""
        sidebar.append(f'<div class="tab {active}" id="tab-{week}" onclick="changeTab(\'{week}\')">Week {week}</div>')
    
    return '\n'.join(sidebar)

def create_body(contribs: dict[str, Contribs], weeks: list[list[int]], selected: int, month: str, weekends: bool) -> tuple[str, str]:
    '''Create body content'''
    body: list[str] = []

    # Create summary tab 
    body.append(create_summary(contribs, weeks))

    selected_week = ''
    for week, days in enumerate(weeks):
        if week == 0 and sum(days) == 0: continue # skip if no week0
        week_start = min([d for d in days if d > 0])
        week_end = max(days)
        title = '%.2d - %.2d %s' % (week_start, week_end, month)
        name = str(week)
        class_name = 'hidden' if selected != week else ''
        tbl = create_table(contribs, days, weekends)
        
        reps: dict[str, str] = {
            'Class'     : class_name,
            'Title'     : title,
            'Table'     : tbl,
            'Name'      : name,
            'Span'      : '10' if weekends else '8',
            'Weekend'   : '<th>Sat</th><th>Sun</th>' if weekends else '',
        }
        table = table_template.format(**reps)
        body.append(table)
        if selected == week: selected_week = name
    return '\n'.join(body), selected_week

def create_summary(contribs: dict[str, Contribs], weeks: list[list[int]]) -> str:
    summary: list[str] = []
    summary.append('<div id="tbl-all" class="hidden" style="max-width:950px;">')
    entries = [(k, sum(p[0] for p in v.values())) for k,v in contribs.items()]
    for username, total_count in sorted(entries, key=lambda x: (-x[1], x[0])):
        summary.append('<div class="grid-cell">')
        summary.append(f'<label>{username}</label>')
        summary.append(f'<p class="month-count">{total_count}</p>')
        summary.append('</div>')
    summary.append('</div>')
    return '\n'.join(summary)

def create_table(contribs: dict[str, Contribs], days: list[int], weekends: bool) -> str:
    '''Create table body for one week'''
    limit = 7 if weekends else 5
    total: dict[str, int] = {}
    count_levels: dict[str, list[IntPair]] = {}
    for username, user_contribs in contribs.items():
        row: list[IntPair] = [user_contribs.get(str(day), (0,-1)) for day in days[:limit]]
        total[username] = sum(count for (count,_) in row)
        count_levels[username] = row
    
    entries= sorted(total.items(), key=lambda x: x[1])

    tbl: list[str] = []
    max_count = max(count for _, count in entries)
    bar_class = 'bar' if max_count > 0 else ''
    for username, total_count in reversed(entries):
        tbl.append('<tr>')
        tbl.append(f'<td class="left">{username}</td>')
        for count, level in count_levels[username]:
            if level == -1:
                tbl.append('<td>&nbsp;</td>')
            else:
                tbl.append(f'<td class="bold center level{level}">{count}</td>')
        tbl.append(f'<td class="bold right">{total_count}</td>')
        width = '0'
        if max_count > 0:
            width = '%.2f' % ((total_count * 100.0) / max_count)
        bar = f'<div style="width:{width}%">&nbsp;</div>' if max_count > 0 else ''
        tbl.append(f'<td class="{bar_class}">{bar}</td>')
        tbl.append('</tr>')
    return '\n'.join(tbl)

def create_output(reps: dict[str, str], path: Path):
    '''Create output HTML file, replace template placeholders, save HTML file and open in browser'''
    body = html_body.format(**reps)
    html = html_head + body + html_tail
    
    # Write html to file
    with open(path, 'w') as f:
        f.write(html)
    
    # Open html in browser
    url = path.absolute().as_uri()
    webbrowser.open_new_tab(url)

html_head = '''
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
        td.level0 { background-color: #151b23; color: #151b23; }
        td.level1 { background-color: #033a16; color: white;   }
        td.level2 { background-color: #196c2e; }
        td.level3 { background-color: #2ea043; }
        td.level4 { background-color: #56d364; }
        td.left { text-align: left; }
        td.right { text-align: right; }
        td.center { text-align: center; }
        td.bold { font-weight: bold; }
        td.bar { 
            min-width: 300px;
        }
        td.bar div {
            background-color: navy;
            height: 100%;
        }
        div { margin: 0; padding: 0 }
        #sidebar {
            position: absolute;
            top: 0%; left: 0%;
            width: 15%; height: 100%;
            border-right: 1px solid black;
        }
        #main {
            position: absolute;
            top: 0%; left: 15%;
            width: 82%; height: 100%;
            padding-left: 3%;
        }
        div.tab {
            position: relative;
            border: 1px solid black;
            width: 80%;
            padding: 5px;
            margin: 1em auto;
            margin-top: 3em;
            text-align: center;
        }
        div.tab:hover {
            cursor: pointer;
        }
        div.tab.active {
            background-color: chartreuse;
            font-weight: bold;
        }
        .hidden {
            display: none !important;
        }
        div.grid-cell {
            border: 1px solid black;
            text-align: center;
            float: left; 
            width: 300px;
            max-width: 30%;
            margin: 5px;
        }
        div.grid-cell label {
            margin-left: 1em;
        }
        p.month-count {
            font-weight: bold;
            font-size: 2em;
            margin: 5px;
        }
    </style>
</head>
''' 

html_body = '''
<body>
<div id="sidebar">{Sidebar}</div>
<div id="main">
    <h1>{Title}</h1>
    {Body}
</div>
<script>
    var current = '{Selected}';
'''

html_tail = '''
    function changeTab(newTab) {
        document.getElementById('tab-'+current).classList.remove('active');
        document.getElementById('tab-'+newTab).classList.add('active');

        document.getElementById('tbl-'+current).classList.add('hidden');
        document.getElementById('tbl-'+newTab).classList.remove('hidden');

        current = newTab;
    }
</script>
</body>
</html>
'''

table_template = '''
<table class="{Class}" id="tbl-{Name}">
    <thead>
        <tr>
            <th colspan="{Span}">{Title}</th>
        </tr>
        <tr>
            <th>Dev</th><th>Mon</th><th>Tue</th>
            <th>Wed</th><th>Thu</th><th>Fri</th>
            {Weekend}<th colspan="2">Total</th>
        </tr>
    </thead>
    <tbody>{Table}</tbody>
</table>
'''

if __name__ == '__main__':
    main()

'''
TODO:
[ ] Summary Tab  
    - Display weekly totals
    - Display weekly rankings below totals

    - Add pace for month (Avg Commits Per Day, On Pace for X at end of month)
    - Summary subtabs
    - Display Github month calendar per user 
    - Line graph of Daily contributions for month
    - Line graph of Weekly contributions for month
[ ] Year Scope
    - Add monthly reports (similar to monthly summary)
    - Add monthly contribs calendar
    - Add pace for year 
[ ] Improve metrics:
    - Use Github API for public events 
    - Check if using API key improves results (e.g. organizations)
    - Measure activity weight (create repo=1, commit with 2 line updates vs 100 updates)
[ ] Convert to webapp
'''