import json
import requests
import bs4
import difflib

# Get page text at this url
def get_page(url):
    # Spoof user agent because its blocking normal one
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
    headers = {'User-Agent': user_agent}
    # Get page
    r = requests.get(url, headers=headers)

    return r.text

# Get tasks in a dictionary
def split_page(html):
    if html.find('404 Not Found') > -1:
        return {}

    # Skip to tasks
    html = html[html.find('<h1>') + 4:]
    html = html[html.find('<h1>') + 4:]

    out = {}

    while True:
        i = html.find('</h1>')

        naslov = html[:i].strip()

        html = html[i+4:]

        i = html.find('<h1>')
        if i != -1:
            vsebina = html[1:i].strip()
            vsebina = bs4.BeautifulSoup(vsebina, features='html.parser').get_text('\n').strip()
            vsebina = '\n'.join([v for v in vsebina.split('\n') if v])

            out[naslov] = vsebina

            html = html[i + 4:]
        else:
            vsebina = html[1:html.find('</div>')].strip()
            vsebina = bs4.BeautifulSoup(vsebina, features='html.parser').get_text('\n').strip()
            vsebina = '\n'.join([v for v in vsebina.split('\n') if v])

            out[naslov] = vsebina

            return out

# Get difference as dictionary
def get_diff(old_tasks, tasks):
    out = {}

    # Gremo cez vsak predmet
    for k in tasks.keys():
        case_a = old_tasks.get(k, '')
        case_b = tasks[k]

        differ = difflib.Differ()
        diff = '\n'.join([d for d in differ.compare(case_a.splitlines(), case_b.splitlines()) if d[:2] != '  ' ] )
        out[k] = diff

    return out

# Example   
if __name__ == "__main__":
    school_url = 'https://nova.vegova.si/'
    razred='r-4-b'
    url = f'{school_url}{razred}'
    tasks = split_page(get_page(url))
    print(tasks)


