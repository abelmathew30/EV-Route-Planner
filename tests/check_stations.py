import urllib.request
req = urllib.request.urlopen('http://127.0.0.1:5000/stations')
html = req.read().decode()
print('Status:', req.status)
if 'Kochi EV Hub' in html:
    print('OK: Station names found in HTML')
if 'stationsData' in html:
    print('OK: stationsData script tag found')
    idx = html.find('"application/json">')
    snippet = html[idx+19:idx+200].strip()
    print('JSON start:', snippet[:100])
else:
    print('ERROR: stationsData missing')
