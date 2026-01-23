# Github Contributions 
# John Roy Daradal 

import os, sys
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
        try:
            if arg.startswith('date='):
                value = arg.split('=')[1]
                given_date = datetime.strptime(value, '%Y-%m-%d')
                user_date = given_date.date()
            elif arg.startswith('input='):
                value = arg.split('=')[1]
                input_path = value
        except:
            continue
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

if __name__ == '__main__':
    main()
