import requests
from bs4 import BeautifulSoup
import time
import json
import stats
from datetime import datetime
import re
from gallery_info import extract_gallery_info  # 갤러리 정보 추출 함수 추가
import msvcrt  # 키 입력 감지를 위한 모듈 추가

# HTTP 요청시 사용할 헤더 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
}

# 갤러리 유형 URL 설정 (사용자 선택에 따라 결정)
gallery_types = {
    "1": "https://gall.dcinside.com/board/lists",
    "2": "https://gall.dcinside.com/mgallery/board/lists",
    "3": "https://gall.dcinside.com/mini/board/lists",
    "4": "https://gall.dcinside.com/person/board/lists"
}

# 갤러리 유형 선택 안내 출력
print("갤러리 유형을 선택하세요:")
print("1. 정갤\t2. 마갤\t3. 미갤\t4. 인물갤")

while True:
    gallery_choice = input("선택 (1-4): ")
    if gallery_choice in gallery_types:
        BASE_URL = gallery_types[gallery_choice]
        break
    else:
        print("잘못된 선택입니다. 다시 선택하세요.")

# 갤러리 ID 입력 및 게시물 유효성 검사
while True:
    gallery_id = input("갤러리 ID를 입력하세요: ")
    params = {'id': gallery_id, 'page': 1}
    try:
        resp = requests.get(BASE_URL, params=params, headers=headers)
        # 404 응답: 유효하지 않은 갤러리 ID 처리
        if resp.status_code == 404:
            print("유효하지 않은 갤러리 ID입니다. 다시 입력하세요.")
            continue
        soup = BeautifulSoup(resp.content, 'html.parser')
        tbody = soup.find('tbody')
        if not tbody:
            print("게시물 정보를 찾을 수 없습니다. 갤러리 ID 혹은 갤러리 유형을 확인하세요.")
            continue
        contents = tbody.find_all('tr')
        if contents: break
        else: print("게시물이 없는 갤러리입니다. 다시 입력하세요.")
    except requests.RequestException: print("네트워크 오류가 발생했습니다. 다시 시도하세요.")

# 현재 페이지의 BeautifulSoup 객체 생성
soup = BeautifulSoup(resp.content, 'html.parser')

# 갤러리 정보 추출 (추가된 함수 사용)
gallery_info = extract_gallery_info(soup, gallery_choice)

# 특정 날짜 입력 및 날짜 유효성 체크
while True:
    target_date = input("특정 날짜를 입력하세요 (YYYY-MM-DD): ")
    try:
        target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
        if target_datetime > datetime.now():
            print("미래 날짜는 입력할 수 없습니다. 다시 입력하세요.")
            continue
        break
    except ValueError:
        print("날짜 형식이 잘못되었습니다. 다시 입력하세요.")
print(f"{target_date} 게시물을 찾습니다.")

# 첫 번째 요청으로 마지막 페이지 번호 추출 (페이지 네비게이션 처리)
resp = requests.get(BASE_URL, params=params, headers=headers)
soup = BeautifulSoup(resp.content, 'html.parser')
last_page_tag = soup.find('a', class_='sp_pagingicon page_end')
if last_page_tag:
    last_page = int(last_page_tag['href'].split('page=')[-1])
else:
    last_page = 1

# 게시물 정보를 저장할 딕셔너리 초기화
posts = {}
found_posts = False
stop_collection = False  # 수집 종료 플래그

# 각 페이지별로 게시물 정보 추출 시작
for page in range(1, last_page + 1):
    # 키 입력 시 수집 중지 검사 (페이지 시작 시)
    if msvcrt.kbhit():
        print("키 입력 감지됨. 게시글 수집을 중지합니다.")
        break

    # 페이지별 파라미터 재설정
    params = {'id': gallery_id, 'page': page}
    resp = requests.get(BASE_URL, params=params, headers=headers)
    print(resp, resp.url)

    soup = BeautifulSoup(resp.content, 'html.parser')
    tbody = soup.find('tbody')
    if not tbody:
        print(f"게시물 정보를 찾을 수 없습니다. 페이지: {page}")
        continue

    # 현재 페이지의 게시글 목록 추출
    contents = tbody.find_all('tr')

    for i, content in enumerate(contents):
        # 키 입력 시 'esc'키가 눌린 경우 수집 중지 검사 (각 게시물 처리 시)
        if msvcrt.kbhit():
            key = msvcrt.getch()
            if key == b'\x1b':  # ESC 키의 ASCII 코드
                print("종료 키 ('esc') 감지됨. 게시글 수집을 중지합니다.")
                stop_collection = True
                break

        # 공지 게시글은 건너뛰기
        subject_tag = content.find('td', class_='gall_subject')
        if subject_tag and subject_tag.find('b') and subject_tag.find('b').text.strip() == "공지": continue

        # 게시물 날짜 추출 및 처리 (title 속성 또는 텍스트)
        date_tag = content.find('td', class_='gall_date')
        date_dict = date_tag.attrs
        post_date = date_dict.get('title', date_tag.text)

        # 특정 날짜의 게시물만 처리
        if post_date.startswith(target_date):
            found_posts = True
            print('-'*15)
            
            # 게시물 제목 추출 및 출력
            title_tag = content.find('a')
            title = title_tag.text.strip()
            print("제목: ", title)
            
            # 작성자 추출 및 검증 (nickname이 없을 경우 대비)
            writer_span = content.find('td', class_='gall_writer ub-writer').find('span', class_='nickname')
            writer = writer_span.text if writer_span is not None else "없음"
            print("글쓴이: ", writer)
            
            # 작성자 정보: 고닉/반고닉 여부에 따라 IP 또는 사용자 ID 추출
            writer_info = content.find('td', class_='gall_writer ub-writer')
            ip_tag = writer_info.find('span', class_='ip')
            key = ip_tag.text if ip_tag is not None else writer_info.get('data-uid', "없음")
            if ip_tag: print("IP: ", key)
            else: print("ID: ", key)
            
            # 조회수 및 추천 수 추출 (없을 경우 기본값 "0")
            view_count = content.find('td', class_='gall_count').text if content.find('td', class_='gall_count') else "0"
            recommend_count = content.find('td', class_='gall_recommend').text if content.find('td', class_='gall_recommend') else "0"
            # 댓글 수 추출: <a class="reply_numbox"><span class="reply_num">[숫자]</span></a>
            reply_tag = content.find('a', class_='reply_numbox')
            if reply_tag:
                reply_span = reply_tag.find('span', class_='reply_num')
                if reply_span:
                    import re  # 필요한 경우 모듈 import
                    comment_count = re.sub(r'\D', '', reply_span.text) or "0"
                else: comment_count = "0"
            else: comment_count = "0"
            
            # 전체 작성일 정보
            post_date_full = date_dict.get('title', post_date)
            
            # 게시물 정보 저장 (중복 키 확인)
            if key not in posts: posts[key] = {'writer': writer, 'titles': []}
            posts[key]['titles'].append(f"{title} | {view_count} | {recommend_count} | {comment_count} | {post_date_full}")
            
            # 요청 사이 딜레이 (20건마다 1초 휴식)
            if (i + 1) % 20 == 0: time.sleep(1)
        else: # 특정 날짜의 게시물이 아니면 건너뜁니다.
            if found_posts: continue
    if stop_collection: break # 수집 중지 플래그 확인

# 게시물 정보를 기반으로 통계 계산 및 HTML 파일 생성
stats.calculate_and_generate_html(posts, target_date, gallery_info)
