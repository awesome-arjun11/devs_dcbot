import requests, json, pypandoc
from bs4 import BeautifulSoup as bs
import re

p = re.compile('[^\S\n ]')

def cnc_htm2md(htm):
    """:returns cleaned md for discord"""
    htm = htm.replace('<pre>', '<pre> ')
    conv_md = bs(pypandoc.convert_text(htm, 'gfm', format='html', extra_args=['--wrap=preserve']), features="lxml").text
    conv_md = p.sub(' ', conv_md)
    return conv_md.replace('$$$', '***').strip()

def handle_lc(qdata):
    """ uses title to generate slug and get html content from leetcode
    """
    s = requests.session()
    s.get("https://leetcode.com")
    slug = "-".join(qdata['title'].lower().split())
    s.headers.update({
                         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36',
                         'Connection': 'keep-alive', 'content-type': 'application/json', 'Accept': '*/*',
                         'Accept-Encoding': 'gzip,deflate,sdch', 'Cache-Control': 'no-cache',
                         'Origin': 'https://leetcode.com', 'Referer': f'https://leetcode.com/problems/{slug}/',
                         'Accept-Language': 'en-IE,en-US;q=0.9,en;q=0.8,hi;q=0.7',
                         'x-csrftoken': s.cookies.get('csrftoken'), 'x-newrelic-id': 'UAQDVFVRGwEAXVlbBAg='})
    payload = {
        'operationName': "questionData",
        'query': "query questionData($titleSlug: String!) {\n  question(titleSlug: $titleSlug) {\n   content\n   }\n}\n",
        'variables': {'titleSlug': slug}
    }
    return cnc_htm2md(
        s.post("https://leetcode.com/graphql", data=json.dumps(payload)).json()['data']['question']['content'])


def handle_cf(qdata):
    url = f"https://codeforces.com/problemset/problem/{qdata['id'][:-1]}/{qdata['id'][-1]}"
    ques_html = bs(requests.get(url).content, features="lxml").find('div', class_="problem-statement")
    header_html = ques_html.find('div', class_="header")
    header = {}
    for i in header_html.find_all('div', class_="property-title"):
        header[i.text] = i.parent.contents[2]
    qcontent = cnc_htm2md(str(ques_html.contents[3]))
    input = cnc_htm2md(str(ques_html.find('div', class_='input-specification').p))
    output = cnc_htm2md(str(ques_html.find('div', class_='output-specification').p))
    qcontent = f"{qcontent}\n**Input:**\n{input}\n**Output:**\n{output}\n**TestCases:**"
    testcases = []
    for test_case in zip(ques_html.find_all('div', class_="input"), ques_html.find_all('div', class_="output")):
        testcases.append({
            'input': cnc_htm2md(str(test_case[0].pre)),
            'output': cnc_htm2md(str(test_case[1].pre))
        })
    data = {
         'header': header,
         'description': qcontent,
         'testcases': testcases
    }
    return data




















