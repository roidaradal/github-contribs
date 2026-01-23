# Github Contributions 
# John Roy Daradal 

import calendar, os, sys
import requests
from datetime import date, datetime
from bs4 import BeautifulSoup

IntPair = tuple[int,int]

HTML_URL: str = 'https://github.com/users/%s/contributions?from=%s' # (username, start_date)

def main():
    '''Main function'''
    user_date, input_path = get_args()
    usernames = get_usernames(input_path)

    username = usernames[0]
    contribs = fetch_user_month_contributions(username, user_date)
    for date in sorted(contribs.keys()):
        print(date, contribs[date])

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

def fetch_user_month_contributions(username: str, d: date) -> dict[int, IntPair]:
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
    contribs: dict[int, IntPair] = {}
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

def new_date(date_string: str) -> date:
    '''Create new date from date_string, defaults to today if given date_string is invalid'''
    try:
        given_date = datetime.strptime(date_string, '%Y-%m-%d')
        return given_date.date()
    except:
        return date.today()

if __name__ == '__main__':
    main()
    