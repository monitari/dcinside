# Description: 글쓴이의 제목들을 요약하는 스크립트. 다만 허접한 결과. 수정 요망.
import json
import os
import requests
import google.generativeai as genai
from collections import Counter
import time
from google.api_core import exceptions

GEMINI_API_KEY = "" # 차피 api 증발함.

# JSON 파일 읽기
print("Reading JSON file...")
with open('posts.json', 'r', encoding='utf-8') as f:
    posts = json.load(f)
print("JSON file read successfully.")

# Google Generative AI 설정
print("Configuring Google Generative AI...")
genai.configure(api_key=GEMINI_API_KEY)
print("Google Generative AI configured successfully.")

generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-2.0-flash-thinking-exp-1219",
  generation_config=generation_config,
)

# AI를 사용해 글쓴이의 제목들을 요약하는 함수
def ai_summarize_titles(posts, model, batch_size=5, delay=1):
    summaries = {}
    total = len(posts)
    current = 0

    for writer, data in posts.items():
        current += 1
        print(f"Summarizing titles for {writer}... ({current}/{total})")
        
        try:
            titles = data['titles']
            prompt = "다음 제목들을 요약해 주세요: " + " ".join(titles)
            response = model.generate_content(prompt)
            summaries[writer] = response.text
            
            # 일정 수의 요청마다 대기
            if current % batch_size == 0:
                print(f"Waiting {delay} seconds to avoid rate limiting...")
                time.sleep(delay)
                
        except exceptions.ResourceExhausted:
            print(f"Rate limit reached. Waiting {delay * 2} seconds...")
            time.sleep(delay * 2)
            try:
                response = model.generate_content(prompt)
                summaries[writer] = response.text
            except Exception as e:
                print(f"Error processing {writer}: {e}")
                summaries[writer] = "요약 실패"
        except Exception as e:
            print(f"Error processing {writer}: {e}")
            summaries[writer] = "요약 실패"
            
    return summaries

# 요약 결과를 파일에 저장하는 함수
def save_summaries_to_file(summaries, filename='summaries.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=4)
    print(f"Summaries saved to {filename}")

# AI 요약 결과 출력
print("AI Summarizing titles...")
ai_summaries = ai_summarize_titles(posts, model)
for writer, summary in ai_summaries.items():
    print(f"Writer: {writer}, AI Summary: {summary}")
print("AI Summarization completed.")

# AI 요약 결과 저장
save_summaries_to_file(ai_summaries, filename='ai_summaries.json')
