# 모델 : 게시판 크롤링
import requests
from bs4 import BeautifulSoup
import time
import json

BASE_URL = "https://gall.dcinside.com/mini/board/lists"

# 헤더 설정
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Whale/4.29.282.14 Safari/537.36'}

# 특정 날짜 설정
target_date = "2025-01-10"
print(f"{target_date} 게시물을 찾습니다.")

# 첫 번째 요청으로 페이지 끝 번호 추출
params = {'id': 'jingburger1', 'page': 1}
resp = requests.get(BASE_URL, params=params, headers=headers)

# 응답코드 확인
soup = BeautifulSoup(resp.content, 'html.parser')

# 페이지 끝 번호 추출
last_page_tag = soup.find('a', class_='sp_pagingicon page_end')
if last_page_tag: last_page = int(last_page_tag['href'].split('page=')[-1])
else: last_page = 1

# 게시물 정보를 저장할 딕셔너리
posts = {}
found_posts = False

# 몇 페이지부터 몇 페이지까지
for page in range(1, last_page + 1):
    # 파라미터 설정
    params = {'id': 'jingburger1', 'page': page}

    # 요청
    resp = requests.get(BASE_URL, params=params, headers=headers)
    print(resp, resp.url)

    # 응답코드 확인
    soup = BeautifulSoup(resp.content, 'html.parser')

    # 게시글 목록 추출
    contents = soup.find('tbody').find_all('tr')

    # 한 페이지에 있는 모든 게시물을 긁어오는 코드 
    for i, content in enumerate(contents):
        # 날짜 추출 
        date_tag = content.find('td', class_='gall_date')
        date_dict = date_tag.attrs

        if len(date_dict) == 2:
            post_date = date_dict['title']
        else:
            post_date = date_tag.text

        # 특정 날짜의 게시물만 처리
        if post_date.startswith(target_date):
            found_posts = True
            print('-'*15)
            
            # 제목 추출
            title_tag = content.find('a')
            title = title_tag.text.strip()
            print("제목: ", title)
            
            # 글쓴이 추출
            writer_tag = content.find('td', class_='gall_writer ub-writer').find('span', class_='nickname')
            if writer_tag is not None: # None 값이 있으므로 조건문을 통해 회피 
                writer = writer_tag.text
                print("글쓴이: ", writer)
                
            else:
                writer = "없음"
                print("글쓴이: ", writer)
            
            # 고닉이나 반고닉이 아닌 경우 ip 추출 / 고닉이나 반고닉인 경우 id 추출
            writer_info = content.find('td', class_='gall_writer ub-writer')
            ip_tag = writer_info.find('span', class_='ip')
            if ip_tag is not None:  # None 값이 있으므로 조건문을 통해 회피 
                key = ip_tag.text
                print("IP: ", key)
            else:
                key = writer_info['data-uid']
                print("ID: ", key)
            
            # 게시물 정보 저장
            if key not in posts:
                posts[key] = {'writer': writer, 'titles': []}
            posts[key]['titles'].append(title)
            
            # 요청 사이에 딜레이 추가
            if (i + 1) % 5 == 0:
                time.sleep(1)
        else:
            # 특정 날짜의 게시물이 아닌 경우
            if found_posts:
                continue

    # 특정 날짜의 게시물이 아닌 경우 루프 종료
    if found_posts and not any(post_date.startswith(target_date) for content in contents):
        break

# JSON 파일로 저장
with open('posts.json', 'w', encoding='utf-8') as f:
    json.dump(posts, f, ensure_ascii=False, indent=4)
