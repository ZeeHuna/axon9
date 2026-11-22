"""AXON-9 Pro news robot - runs on GitHub every 30 min, writes news.json for the app (no API key, no cost).
Pulls Google News RSS for the big market movers and tags which of Zola's markets each story touches."""
import json, re, time, urllib.parse, urllib.request, email.utils, xml.etree.ElementTree as ET

QUERIES = ['Federal Reserve interest rates', 'Bank of Japan yen', 'ECB rates euro', 'Bank of England pound',
           'gold price', 'bitcoin price', 'Nvidia', 'stock market Wall Street', 'Dow Jones', 'Nasdaq', 'DAX Germany stocks',
           'US inflation CPI', 'jobs report payrolls', 'tariffs trade war', 'oil prices OPEC', 'war Middle East markets',
           'Russia Ukraine markets', 'China economy markets', 'crypto regulation SEC']
MARKETS = {
    'GOLD':   r'\bgold\b|bullion|safe.haven|fed\b|federal reserve|inflation|cpi\b|war|geopolit',
    'BTC':    r'bitcoin|\bbtc\b|crypto|sec\b.*crypto|etf.*bitcoin',
    'US30':   r'dow\b|dow jones|wall street|s&p|stocks?\b|fed\b|federal reserve|tariff|payroll|jobs report|inflation',
    'NAS100': r'nasdaq|nvidia|apple|microsoft|meta\b|tesla|amazon|alphabet|google|chip|semiconductor|\bai\b|tech stocks|fed\b|federal reserve',
    'GER40':  r'\bdax\b|german|germany|ecb\b|europe(an)? stocks|euro ?zone',
    'USDJPY': r'\byen\b|bank of japan|\bboj\b|japan|fed\b|federal reserve|dollar|treasury yields?',
    'GBPJPY': r'pound|sterling|bank of england|\bboe\b|\buk\b|britain|\byen\b|bank of japan|\bboj\b',
    'EURJPY': r'\beuro\b|ecb\b|euro ?zone|\byen\b|bank of japan|\bboj\b',
}
BIG = r'fed\b|federal reserve|rate (cut|hike)|interest rate|bank of japan|\bboj\b|ecb\b|inflation|cpi\b|payroll|jobs report|war\b|attack|sanction|tariff|crash|plunge|surge|soar|record|scandal|probe|investigation|default|recession|nvidia|opec'
STRONG = (r'plunge|plunges|crash|tumble|slump|sink|soar|surge|record high|all.time high|scandal|probe|investigation|rate cut|rate hike|war\b|attack|sanction|tariff|default')

def fetch(q):
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': q + ' when:2d', 'hl': 'en-US', 'gl': 'US', 'ceid': 'US:en'})
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 AXON9-news'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def parse(xml):
    out = []
    root = ET.fromstring(xml)
    for it in root.iter('item'):
        title = (it.findtext('title') or '').strip()
        link = (it.findtext('link') or '').strip()
        src = it.find('source')
        source = (src.text or '').strip() if src is not None else ''
        if source and title.endswith(' - ' + source): title = title[: -len(' - ' + source)]
        try: ts = email.utils.parsedate_to_datetime(it.findtext('pubDate')).timestamp()
        except Exception: ts = time.time()
        out.append({'title': title, 'url': link, 'source': source, 't': int(ts)})
    return out

def main():
    now, seen, items = time.time(), set(), []
    for q in QUERIES:
        try: arr = parse(fetch(q))
        except Exception as e: print('skip', q, e); continue
        for a in arr[:12]:
            k = re.sub(r'\W+', ' ', a['title'].lower())[:70]
            if not a['title'] or k in seen or now - a['t'] > 48 * 3600: continue
            seen.add(k)
            low = a['title'].lower()
            a['m'] = [m for m, rx in MARKETS.items() if re.search(rx, low)]
            if not a['m']: continue
            score = len(a['m']) + (4 if re.search(BIG, low) else 0) + (3 if re.search(STRONG, low) else 0) - (now - a['t']) / 21600
            a['big'] = bool(re.search(BIG, low) and re.search(STRONG, low))
            a['s'] = round(score, 2)
            items.append(a)
    items.sort(key=lambda x: -x['s'])
    json.dump({'t': int(now), 'items': items[:24]}, open('news.json', 'w'), ensure_ascii=False)
    print('news items', len(items[:24]))

if __name__ == '__main__':
    main()
