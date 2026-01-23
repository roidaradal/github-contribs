# Github Contributions 
# John Roy Daradal 

import calendar, os, sys
import requests, webbrowser
from datetime import date, datetime
from bs4 import BeautifulSoup

HTML_URL: str = 'https://github.com/users/%s/contributions?from=%s' # (username, start_date)
API_URL : str = 'https://api.github.com/users/%s/events/public'
OUT_DIR : str = '.contribs'

IntPair = tuple[int,int]
Contribs = dict[int, IntPair]

color_reset = '\033[0m'
green   = lambda text: '\033[32m%s%s' % (text, color_reset)
yellow  = lambda text: '\033[33m%s%s' % (text, color_reset)
cyan    = lambda text: '\033[36m%s%s' % (text, color_reset)

def main():
    '''Main function'''
    user_date, input_path = get_args()
    month = user_date.strftime('%B %Y')
    weeks = get_month_weeks(user_date)
    week_index = get_week_of(user_date, weeks)

    reps: dict[str, str] = {
        'Title':    f'{month} GitHub Contributions',
        'Sidebar':  create_sidebar(weeks, week_index),
        'Body':     create_body(weeks, week_index, month),
    }
    create_output(reps)

    # usernames = get_usernames(input_path)
    # max_length = max(len(uname) for uname in usernames)
    # template = '• %%-%ds\t\t%%3d' % max_length

    # print('Fetching %s GitHub contributions from %s...' % (green(month), yellow(f'`{input_path}`')))

    # contribs: dict[str, Contribs] = {}
    # for username in usernames:
    #     contribs[username] = fetch_user_month_contributions(username, user_date)
    #     total = sum(count for (count,_) in contribs[username].values())
    #     print(template % (cyan(username), total))

def get_args() -> tuple[date, str]:
    '''Returns the chosen date (default: today) and input_path (default: ./devs.txt)'''
    user_date = date.today()
    input_path = 'devs.txt' 
    for arg in sys.argv[1:]:
        if arg.startswith('date='):
            value = arg.split('=')[1]
            user_date = new_date(value)
        elif arg.startswith('input='):
            input_path = arg.split('=')[1]
    return user_date, input_path

def get_usernames(path: str) -> list[str]:
    '''Load list of usernames from path (default: devs.txt)'''
    if not os.path.exists(path):
        print(f'Error: path `{path}` does not exist')
        sys.exit(1)
    
    try:
        with open(path, 'r') as f:
            return [line.strip() for line in f.readlines() if line.strip() != '']
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
        contribs[day] = (count, level)
    return contribs

def create_sidebar(weeks: list[list[int]], selected: int) -> str:
    '''Create sidebar content'''
    sidebar: list[str] = []
    for week, days in enumerate(weeks):
        if week == 0 and sum(days) == 0: continue # skip if no week0

        active = "active" if selected == week else ""
        sidebar.append(f'<div class="tab {active}" id="tab-week{week}">Week {week}</div>')
    
    return '\n'.join(sidebar)

def create_body(weeks: list[list[int]], selected: int, month: str) -> str:
    '''Create body content'''
    body: list[str] = []
    for week, days in enumerate(weeks):
        if week == 0 and sum(days) == 0: continue # skip if no week0

        title = '%.2d - %.2d %s' % (min([d for d in days if d > 0]), max(days), month)
        reps: dict[str, str] = {
            'Class' : 'hidden' if selected != week else '',
            'Title' : title,
            'Table' : '',
        }
        table = table_template.format(**reps)
        body.append(table)
    return '\n'.join(body)

def create_output(reps: dict[str, str]):
    '''Create output HTML file, replace template placeholders, save HTML file and open in browser'''
    body = html_body.format(**reps)
    html = html_head + body
    
    # Write html to file
    path = 'out.html' # Temporary while testing, TODO: replace path 
    with open(path, 'w') as f:
        f.write(html)
    
    # Open html in browser
    url = 'file://' + os.path.abspath(path)
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
</body>
</html>
'''

table_template = '''
<table class="{Class}">
    <thead>
        <tr>
            <th colspan="7">{Title}</th>
        </tr>
        <tr>
            <th>Dev</th><th>Mon</th><th>Tue</th>
            <th>Wed</th><th>Thu</th><th>Fri</th>
            th>Total</th>
        </tr>
    </thead>
    <tbody>{Table}</tbody>
</table>
'''

if __name__ == '__main__':
    main()
    