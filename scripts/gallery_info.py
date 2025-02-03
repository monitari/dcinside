from bs4 import BeautifulSoup
import re
import requests
import os
import hashlib

def create_safe_filename(url, gallery_id):
    """안전한 파일 이름 생성"""
    # URL의 해시값을 이용해 고유한 파일 이름 생성
    hash_object = hashlib.md5(url.encode())
    file_hash = hash_object.hexdigest()[:10]
    return f"{gallery_id}_{file_hash}.jpg"

def download_image(url, gallery_id):
    try:
        # images 디렉토리가 없으면 생성
        if not os.path.exists('images'):
            os.makedirs('images')
            
        # 안전한 파일 이름 생성
        filename = create_safe_filename(url, gallery_id)
        save_path = os.path.join('images', filename)
        
        # 이미 다운로드된 파일이 있다면 그대로 반환
        if os.path.exists(save_path):
            return save_path
            
        response = requests.get(url, headers={
            'Referer': 'https://gall.dcinside.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return save_path
    except requests.RequestException as e:
        print(f"이미지 다운로드 실패: {e}")
        return ""
    except OSError as e:
        print(f"파일 저장 실패: {e}")
        return ""

def extract_gallery_info(soup, gallery_type):
    """
    주어진 BeautifulSoup 객체와 gallery_type에 따라 갤러리 정보를 추출합니다.
    gallery_type:
        "1" - 정갤, "2" - 마이너갤, "3" - 미갤, "4" - 인물갤, 그 외 - 기타
    반환: 이름, 커버, 소개, 매니저, 부매니저, 개설일, 순위 텍스트 및 번호를 포함한 딕셔너리
    """
    # 기본 갤러리 이름 추출 (내용 없으면 "Unknown")
    gallery_name = soup.select_one('h2 a').text.strip() if soup.select_one('h2 a') else "Unknown"
    
    # 기본 초기값 설정
    gallery_cover = ""
    gallery_intro = "-"
    gallery_manager = "없음"
    gallery_sub_manager = "없음"
    gallery_creation_date = "2000-01-01"
    rank_text = "몰랑"
    rank_num = ""
    
    if gallery_type == "1":  # 정갤
        # 정갤 관련 정보가 담긴 영역 선택
        gall_info_div = soup.find('div', class_='pop_content gall_info')
        if gall_info_div:
            inner_div = gall_info_div.find('div', class_='inner') or gall_info_div
            # 커버 이미지 추출: style 속성의 background-image URL 파싱
            imgbox = inner_div.find('div', class_='imgbox')
            if imgbox:
                cover_span = imgbox.find('span', class_='cover')
                if cover_span and 'style' in cover_span.attrs:
                    style_value = cover_span['style']
                    m = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style_value)
                    gallery_cover = m.group(1) if m else ""
            # 갤러리 순위 정보 추출 : 순위 텍스트와 순위 번호
            ranking_div = inner_div.find('div', class_='gall_ranking')
            if ranking_div:
                granking_img = ranking_div.find('div', class_=lambda x: x and x.startswith('granking_img'))
                rank_text = granking_img.get_text(strip=True) if granking_img else ""
                granking_num_div = ranking_div.find('div', class_='granking_num')
                if granking_num_div:
                    num_spans = granking_num_div.find_all('span', class_=lambda v: v and 'gnumimg' in v)
                    rank_num = "".join(span.get_text(strip=True) for span in num_spans) + "위" if num_spans else ""
            # 갤러리 개설일 및 카테고리(소개) 정보 추출
            gallinfo_box = inner_div.find('div', class_='gallinfo_box')
            if gallinfo_box:
                text = gallinfo_box.get_text(strip=True)
                # 개설일: "개설일" 뒤 10자리 (YYYY-MM-DD) 추출
                m_date = re.search(r'개설일(\d{4}-\d{2}-\d{2})', text)
                gallery_creation_date = m_date.group(1) if m_date else ""
                # 카테고리 정보 추출 (존재 시 gallery_intro 업데이트)
                m_cate = re.search(r'카테고리(.+)$', text)
                gallery_intro = '카테고리: ' + m_cate.group(1) if m_cate else ""
        # 정갤은 매니저/부매니저 정보가 없음.
    
    elif gallery_type == "2" or gallery_type == "3":
        # 갤러리 이름 재추출 (안전 처리)
        gallery_name = soup.select_one('h2 a').text.strip() if soup.select_one('h2 a') else "Unknown"
        if '갤러리' in gallery_name: gallery_name = gallery_name.replace('갤러리', '').strip() + ' 갤러리' # 갤러리 이름 보정
        
        # 커버 이미지 추출: .img_contbox 내 cover 스타일에서 URL 파싱
        cover_tag = soup.select_one('.img_contbox .cover')
        if cover_tag and 'style' in cover_tag.attrs:
            style_value = cover_tag['style']
            m = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style_value)
            gallery_cover = m.group(1) if m else ""
        else:
            gallery_cover = ""
        
        # 갤러리 소개 텍스트 추출
        gallery_intro = soup.select_one('.mintro_txt').text.strip() if soup.select_one('.mintro_txt') else ""
        
        # 매니저/부매니저 정보 추출
        manager_tag = soup.find('strong', string="매니저")
        sub_manager_tag = soup.find('strong', string="부매니저")
        if manager_tag and manager_tag.find_next('p'):
            gallery_manager = manager_tag.find_next('p').text.strip()
        else:
            gallery_manager = ""
        
        if sub_manager_tag and sub_manager_tag.find_next('p'):
            gallery_sub_manager = sub_manager_tag.find_next('p').text.strip()
        else:
            gallery_sub_manager = ""
        
        # 개설일 정보 추출
        creation_tag = soup.find('strong', string="개설일")
        if creation_tag and creation_tag.find_next('p'):
            gallery_creation_date = creation_tag.find_next('p').text.strip()
        else:
            gallery_creation_date = ""
        
        # 갤러리 순위 정보 추출 (타입에 따라 구조가 다름)
        if gallery_type == "2":   # 마이너갤 : 순위 정보가 ranking div 내부에 있음.
            ranking_div = soup.find('div', class_='ranking')
            if ranking_div:
                ranking_tit = ranking_div.find('div', class_='ranking_tit')
                rank_text = ranking_tit.get_text(strip=True) if ranking_tit else ""
                rank_img = ranking_div.find('div', class_='rank_img')
                if rank_img:
                    num_spans = rank_img.find_all('span', class_=lambda v: v and 'num_img' in v)
                    rank_num = "".join(span.get_text(strip=True) for span in num_spans) + "위" if num_spans else ""
                else:
                    rank_num = ""
            else:
                rank_text, rank_num = "", ""
        elif gallery_type == "3":   # 미갤 : 순위 정보가 별도 span 태그에 있음.
            rank_text = soup.select_one('.mini_ranktxt').text.strip() if soup.select_one('.mini_ranktxt') else ""
            rank_num = soup.select_one('.mini_ranknum').text.strip() if soup.select_one('.mini_ranknum') else ""
    
    elif gallery_type == "4":  # 인물 갤러리 처리
        # 갤러리 이름 추출 (없으면 "Unknown")
        gallery_name = soup.select_one('h2 a').text.strip() if soup.select_one('h2 a') else "Unknown"
        if '갤러리' in gallery_name: gallery_name = gallery_name.replace('갤러리', '').strip() + ' 갤러리' # 갤러리 이름 보정

        # 인물 갤러리는 부매니저 없음, 매니저는 <span class="mng_nick">에서 추출
        manager_span = soup.find('span', class_='mng_nick')
        gallery_manager = manager_span.text.strip() if manager_span else "없음"
        # 갤러리 커버: <div class="img_contbox"> 내 <span class="cover" id="profile_cover">의 style에서 URL 추출
        cover_tag = soup.select_one('div.img_contbox span.cover#profile_cover')
        if cover_tag and 'style' in cover_tag.attrs:
            style_value = cover_tag['style']
            m = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style_value)
            cover_url = m.group(1) if m else ""
            # 이미지 다운로드 및 로컬 경로 설정
            if cover_url:
                gallery_id = soup.select_one('input#gallery_id')['value'] if soup.select_one('input#gallery_id') else "unknown"
                gallery_cover = download_image(cover_url, gallery_id)
        else:
            gallery_cover = ""
        # 인물 갤러리는 개설일 정보가 없음
        gallery_creation_date = "정보 없음"
        # 순위 정보 추출: <div class="ranking"> 내부의 <span class="ranktxt">와 <span class="ranknum">
        ranking_div = soup.select_one('div.ranking')
        if ranking_div:
            rank_text_tag = ranking_div.find('span', class_='ranktxt')
            rank_num_tag = ranking_div.find('span', class_='ranknum')
            rank_text = rank_text_tag.text.strip() if rank_text_tag else ""
            rank_num = rank_num_tag.text.strip() if rank_num_tag else ""
        else:
            rank_text, rank_num = "", ""
        
        # 인물 갤러리 소개 정보 추출
        intro_info = []
        info_conts = soup.select('div.info_contbox div.info_cont')
        for info in info_conts:
            title = info.find('strong', class_='tit').text.strip()
            content = info.find('span', class_='cont_txt').text.strip()
            intro_info.append(f"{title}: {content}")
        gallery_intro = "<br>".join(intro_info)
    
    else:
        # 기타 갤러리 유형 처리 (예: 인물 갤러리)
        rank_text_tag = soup.select_one('.mini_ranktxt')
        rank_text = rank_text_tag.text.strip() if rank_text_tag else ""
        rank_num_tag = soup.select_one('.mini_ranknum')
        rank_num = rank_num_tag.text.strip() if rank_num_tag else ""
    
    # 최종 갤러리 정보 딕셔너리 구성 및 반환
    gallery_info = {
        "name": gallery_name,
        "cover": gallery_cover,
        "intro": gallery_intro,
        "manager": gallery_manager,
        "sub_manager": gallery_sub_manager,
        "creation_date": gallery_creation_date,
        "rank_text": rank_text,
        "rank_num": rank_num
    }
    
    return gallery_info
