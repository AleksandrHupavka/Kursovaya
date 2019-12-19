from bs4 import BeautifulSoup
import re
import json
import requests

headers={'accept': "*/*",
         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}

BASE_URL="https://www.toramp.com/schedule.php"

genres_ids_dict={}
author_ids_dict={}
actors_ids_dict={}
serials_ids_dict={}
status_ids_dict={}
channel_ids_dict={}
seasons_ids_dict={}
episodes_ids_dict={}

serials_array=[]
seasons_array=[]
episodes_array=[]

season_id=1

def get_html(url):
    try: 
        request=requests.get(url,headers=headers)
        return(request.content)
    except requests.exceptions.RequestException:
            print("error")
            return() 
        
def parse_catalogue(html):
    soup=BeautifulSoup(html)
    table=soup.find('table', attrs= {"id":"schedule-list"})
    rows=table.find_all('tr')
    for row in rows:
        object_url=row.find('a',class_="title")
        object_url = ("https://www.toramp.com/"+str(object_url.get('href')))
        print(object_url)
        parse_page(get_html(object_url))
        
def parse_more_data(html):
    soup=BeautifulSoup(html)
    authors_actors=soup.find_all("div", class_="block_list")[1:]
    
    authors=re.split(r'[\n,\r]\s', authors_actors[0].text.strip())
    actors=re.split(r'[\n,\r]\s', authors_actors[1].text.strip())
    description=soup.find("div",class_="article").text
   
    return(authors,actors,description)

def write_json(person_dict,name):
    file_way="C:\\Users\\Admin\\PythonProjects\\json\\ARRAY.json"
    try:
        data=json.load(open(file_way,encoding='utf-8'))
    except:
        data={}
    data[name]=person_dict
    with open(file_way,"w",encoding='utf-8') as file:
        json.dump(data,file,indent=2,ensure_ascii=False)

def add_ids(dictionary,objects_for_add):
    returned_ids=[]
    
    if type(objects_for_add)==str:
        objects_for_add=[objects_for_add]
        
    for object_ in objects_for_add:
        if object_ not in dictionary.values():
            dictionary[str(len(dictionary)+1)]=object_
        returned_ids.append((list(dictionary.keys())[list(dictionary.values()).index(object_)]))
        
    if len(returned_ids)==1:
        return(returned_ids[0])
    return(returned_ids)
    
def get_page_count(html):
    soup=BeautifulSoup(html)
    paggination= soup.find(class_='schedule-ddd')
    paggination=int(paggination.find_all("a")[-1].text)
    return(paggination)
    
def seasons_filling(seasons,serial_id):
    global seasons_array
    global season_id
    for i in range(-1,-len(seasons)-1,-1):
        name=seasons[i].find("h2").text
        dict_helper={
            "id": season_id,
            "serial_id": serial_id,
            "title": name,
        }
        seasons_array.append(dict_helper)
        episodes_filling(seasons[i],season_id)
        season_id+=1

def episodes_filling(episode,season_id):
    global episodes_array
    rows=episode.find_all("tr")
    for j in range(len(rows)):
        title=rows[j].find(class_="title-of-episodes")

        try:
            original=title.find("span").text
        except:
            original="---"

        air_date=rows[j].find(class_="air-date").text
        episode_id=add_ids(episodes_ids_dict,title.find("b").text)
        
        dict_helper={
            "id": episode_id,
            "season_id": season_id,
            "number": int(rows[j].find("span").text),
            "title": title.find("b").text,
            "original": original,
            "published_at": air_date
        }
        episodes_array.append(dict_helper)

def serials_filling(serials,genres_ids,authors_ids,actors_ids,description,status_id,channel_id):
    global serials_array
    
    title= serials.find("span").text
    serial_id=add_ids(serials_ids_dict,title)
    
    dict_helper={
        "id": serial_id,
        "title": title,
        "original": serials.find(class_="title-original").text,
        "genres_ids": genres_ids,
        "author_id": authors_ids,
        "actors_ids": actors_ids,
        "shortDescription": serials.find(class_="body_large summary").text,
        "description": re.sub("\n"," ",description).strip(),
        "thumb": serials.find("img").get("title"),
        "thumb_url": serials.find("img").get("src"),
        "timing": " ".join((serials.find("div",class_="second-part-info").text.strip().split())[-2:]),
        "rating": serials.find(itemprop="ratingValue").get("content"),
        "status_id": status_id,
        "channel_id": channel_id
    }
    serials_array.append(dict_helper)
    return(serial_id)
    
def parse_page(html):
    soup=BeautifulSoup(html)
    main_inf=soup.find('div', class_="article headline-overview")
    extra_inf=soup.find("div", class_="content-widget-1")

    #авторы и актеры и описание
    if extra_inf.find('a') is not None:
        more_data= "https://www.toramp.com/"+ extra_inf.find('a')["href"]
        authors,actors,description=parse_more_data(get_html(more_data))
        
        authors_ids=add_ids(author_ids_dict,authors)
        actors_ids=add_ids(actors_ids_dict,actors)
    else:
        more_data=None
        authors_ids=None
        actors_ids=None
        description=''
        
    #статус и канал
    status_channel=extra_inf.find_all("div",class_="block_list")[0:2] 
    status_channel=list(map(lambda x: x.text,status_channel))
    status_id=add_ids(status_ids_dict,status_channel[0:1])
    channel_id=add_ids(channel_ids_dict,status_channel[1:2])

    #жанры
    genres_all= main_inf.find_all("a")
    genres=list(map(lambda x: x.text,genres_all))
    genres_ids=add_ids(genres_ids_dict,genres)

    #сериал
    serial_id=serials_filling(main_inf,genres_ids,authors_ids,actors_ids,description,status_id,channel_id)
    
    #сезоны и эпизоды
    seasons_all=soup.find_all("div",attrs= {"id":"full-season"})
    seasons_filling(seasons_all,serial_id) 
    
def main():
    page_count=get_page_count(get_html(BASE_URL))
    
    for page in range(0,2):
        parse_catalogue(get_html(BASE_URL+"?page=%d" % page))
        
    write_json(genres_ids_dict,"genres")
    write_json(author_ids_dict,"authors")
    write_json(actors_ids_dict,"actors")
    write_json(status_ids_dict,"statuses")
    write_json(channel_ids_dict,"channels")
    write_json(serials_array,"serials")
    write_json(seasons_array,"seasons")
    write_json(episodes_array,"episodes")
    
if __name__ =="__main__":
    main()