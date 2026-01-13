# github-contribs 

Python tool for pulling GitHub contribution count of GitHub users

## Usage 
Prepare a `devs.json` file which contains the list of GitHub usernames. 

Run `python main.py` to pull the users' GitHub pages, and generate a report of their contributions for the week.

## Dependencies
* `requests` - for making HTTP requests
* `BeautifulSoup4` - for traversing HTML DOM
* `matplotlib` - for bar graph