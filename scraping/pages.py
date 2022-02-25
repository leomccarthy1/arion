import requests
from bs4 import BeautifulSoup
from typing import List, Callable
import json

URL = "https://www.racingpost.com/results/393/lingfield-aw/2022-02-19/803339"
page = requests.get(URL)

def courses(code='gb'):
    with open('_courses', 'r') as courses:
        for course in json.load(courses)[code]:
            yield course.split('-')[0].strip(), ' '.join(course.split('-')[1::]).strip()


def courses(code='gb'):
    courses = json.load(open('scraping/_courses', 'r').read())
    for id, course in courses[code].items():
        yield id,course


def clean_strings(string:str):

    return string.strip().replace("'","").replace(")","").replace("(","").title().replace(".","")

def extract_text(html:List,skip:bool = False, dtype:Callable = str) -> list:
    if skip:
        return [dtype(clean_strings(i.get_text())) for i in html][::2]
    else:
        return [dtype(clean_strings(i.get_text())) for i in html]

def get_weights():
    st = extract_text(soup.find_all("span", {"data-test-selector":"horse-weight-st"}), dtype = int)
    lbs = extract_text(soup.find_all("span", {"data-test-selector":"horse-weight-lb"}), dtype = int)

    st = [i*14 for i in st]
    
    return [i + j for i,j in zip(st,lbs)]



# peds =  extract_text(soup.find_all("tr",{"data-test-selector":"block-pedigreeInfoFullResults"}))
# dam = [i.split()[5] if len(i) > 4 else '' for i in peds]


def x_y():
    from base64 import b64decode
    return b64decode(
        'aHR0cHM6Ly93d3cucmFjaW5ncG9zdC5jb206NDQzL3Byb2ZpbGUvY291cnNlL2ZpbHRlci9yZXN1bHRz'
    ).decode('utf-8'), b64decode('aHR0cHM6Ly93d3cucmFjaW5ncG9zdC5jb20vcmVzdWx0cw==').decode('utf-8')


def course_name(code):
    if code.isalpha():
        return code
    for course in courses():
        if course[0] == code:
            return course[1].replace('()', '').replace(' ', '-')

tracks = [course[0] for course in courses('gb')] 
names = [course_name(track) for track in tracks] 

def get_races(tracks, names, years, code, xy):
    races = []
    for track, name in zip(tracks, names):
        for year in years:
            r = requests.get(f'{xy[0]}/{track}/{year}/{code}/all-races', headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200:
                try:
                    results = r.json()
                    if results['data']['principleRaceResults'] == None:
                        print(f'No {code} race data for {course_name(track)} in {year}.')
                    else:
                        for result in results['data']['principleRaceResults']:
                            races.append(f'{xy[1]}/{track}/{name}/{result["raceDatetime"][:10]}/{result["raceInstanceUid"]}')
                except:
                    pass
            else:
                print(f'Unable to access races from {course_name(track)} in {year}')
    return races


def scrape_race(URL : str) -> None:
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")
    #going = extract_text(soup.find_all( "span" , {"class":"rp-raceTimeCourseName_condition"}))
    #horse_names = extract_text(soup.find_all("a", {"data-test-selector":"link-horseName"}))
    #jockey_names = extract_text(soup.find_all("a", {"data-test-selector":"link-jockeyName"}), skip = True)
    #trainer_name = extract_text(soup.find_all("a", {"data-test-selector":"link-trainerName"}),skip = True)
    #rpr = extract_text(soup.find_all("td", {"data-test-selector":"full-result-rpr"}))
    #ts = extract_text(soup.find_all("td", {"data-test-selector":"full-result-topspeed"}))
    #ratings = extract_text(soup.find_all("td", {"data-ending":"OR"}))
    #age = extract_text(soup.find_all("td", {"data-test-selector":"horse-age"}))
    #pos = extract_text(soup.find_all("span",{"data-test-selector":'text-horsePosition'}))
    #date = soup.find_all("main",{"data-test-selector":"results-items-container"})
    #lengths = get_lengths()
    #dist = get_distance()
    #main = soup.find_all('main')[0]
    #id = main.get("data-analytics-race-id")
    #date = main.get("data-analytics-race-date")
    #time=main.get("data-analytics-race-time")
    #course = main.get("data-analytics-coursename")
    race_class = extract_text(soup.find_all("span",{"class":"rp-raceTimeCourseName_class"}))[0].split()[1]
    draw = extract_text(soup.find_all("sup",{"class":'rp-horseTable__pos__draw'}), dtype=int)
    num = extract_text(soup.find_all("span",{"class":"rp-horseTable__saddleClothNo"}), dtype=int)
    #ran = extract_text(soup.find_all("span",{"class":"rp-raceInfo__value rp-raceInfo__value_black"}))[0].split()[0]
    #prize = get_prize()


    with open('data/test/1.csv', 'w', encoding='utf-8') as csv:

        csv.write(
                'date,age,prize\n'
            )

        for a,p in zip(age,prize):
            csv.write((
                    f'{date},{a},{p}\n'
                    ))

