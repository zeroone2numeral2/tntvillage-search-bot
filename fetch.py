import requests

from bs4 import BeautifulSoup


REQUEST = True


# total_pages = 6219
total_pages = 2


if REQUEST:
    print('REQUEST')
    result = requests.post(
        "http://www.tntvillage.scambioetico.org/src/releaselist.php",
        data={"cat": "0", "page": str(0), "srcrel": ""},
    )

    html_text = result.text
    print(html_text)
    with open('result.html', 'w+') as f:
        f.write(html_text)
else:
    print('FILE')
    with open('result.html', 'r') as f:
        html_text = f.read()


soup = BeautifulSoup(html_text, features='html.parser')
# print(soup.prettify())

for a in soup.find_all('a', href=True):
    print("Found the URL:")
    print('\ttext:', a.text)
    print('\turl:', a['href'])

for tr in soup.find_all('tr'):
    print()
    # print(tr)
    for td in tr.find_all('td'):
        # print('TD:', td)
        if td.find('a'):
            for a in td.find_all('a', href=True):
                # print('A:', a)
                if a['href'].startswith('magnet:?'):
                    print('magnet:', a['href'])
                elif a['href'].startswith('http://forum.tntvillage.scambioetico.org/index.php?showtopic='):
                    print('title:', a.text)
            if td.text:
                print('desc:', td.text)


for li in soup.find_all('li', {'class': 'active'}):
    if li.text.lower() == 'ultima':
        print('tot:', li['p'])
