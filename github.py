# Github Contributions 
# John Roy Daradal 

import os, sys
import calendar
from datetime import date, datetime

def main():
    '''Main function'''
    user_date, input_path = get_args()
    print(user_date)
    usernames = get_usernames(input_path)
    print('Users:', len(usernames))
    for username in usernames:
        print(f'  • {username}')

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

def new_date(date_string: str) -> date:
    '''Create new date from date_string, defaults to today if given date_string is invalid'''
    try:
        given_date = datetime.strptime(date_string, '%Y-%m-%d')
        return given_date.date()
    except:
        return date.today()

if __name__ == '__main__':
    # main()
    for month in range(1, 13):
        user_date = date(2026, month, 1)
        print('\n'+ str(user_date))
        for week in get_month_weeks(user_date):
            row = ['%2d' % day for day in week]
            print(' '.join(row))
    