import urllib.parse
import feedparser
import requests
import os
from dotenv import load_dotenv

# .env 파일이 있을 경우 환경 변수를 로드합니다.
# (로컬 개발 시 VS Code에서 사용)
load_dotenv()

# 환경 변수에서 키를 가져오되, 하드코딩된 기본값(Default)은 완전히 제거했습니다.
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

def get_google_news(query):
    """
    Google News RSS를 통해 미국 주식 관련 최신 뉴스를 가져옵니다.
    """
    try:
        encoded_query = urllib.parse.quote(f"{query} stock")
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url)
        
        if feed.entries:
            # 첫 번째 뉴스 항목의 제목과 링크 반환
            return feed.entries[0].title, feed.entries[0].link
    except Exception as e:
        print(f"⚠️ Google News Error ({query}): {e}")
        
    return "최신 뉴스를 찾을 수 없습니다.", ""

def get_naver_news(query):
    """
    Naver OpenAPI를 통해 한국 주식 관련 최신 뉴스를 가져옵니다.
    """
    # 보안 확인: API 키가 없을 경우 실행 중단
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("⚠️ Naver API 키가 설정되지 않았습니다. (.env 또는 GitHub Secrets 확인)")
        return "서비스 연결 정보가 부족합니다.", ""

    try:
        url = f"https://openapi.naver.com/v1/search/news.json?query={urllib.parse.quote(query)}&display=1&sort=sim"
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        
        res = requests.get(url, headers=headers)
        
        if res.status_code == 200:
            data = res.json()
            if 'items' in data and len(data['items']) > 0:
                item = data['items'][0]
                # HTML 태그 및 특수문자 제거
                title = item['title'].replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
                return title, item['link']
        else:
            print(f"⚠️ Naver API Response Error: {res.status_code}")
            
    except Exception as e:
        print(f"⚠️ Naver News Error ({query}): {e}")
        
    return "관련 뉴스가 없습니다.", ""