# Github Contributions 
# John Roy Daradal 

import requests
from datetime import date

HTML_URL: str = 'https://github.com/users/%s/contributions?from=%s'
API_URL : str = 'https://api.github.com/users/%s/events/public'

def fetch_contributions(username: str):
    start = '%d-01-01' % date.today().year
    url = HTML_URL % (username, start)
    resp = requests.get(url)
    print(resp.text)

if __name__ == '__main__':
    username = 'roidaradal'
    fetch_contributions(username)