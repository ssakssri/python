import sys
import time
import textwrap
from datetime import datetime

# -------------------------------------------------------------------------
# [설정] 검색어 및 표시 개수
SEARCH_QUERY = "Google Gemini AI"  # 검색어 (필요시 수정 가능)
LIMIT = 10                         # 출력할 뉴스 기사 수
# -------------------------------------------------------------------------

# 색상 코드를 위한 클래스 (터미널 출력용)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def fetch_news_feedparser(url):
    """
    feedparser 라이브러리를 사용하여 뉴스 피드를 가져옵니다.
    설치 방법: pip install feedparser
    """
    import feedparser
    feed = feedparser.parse(url)
    news_items = []
    
    if feed.entries:
        for entry in feed.entries[:LIMIT]:
            news_items.append({
                'title': entry.title,
                'link': entry.link,
                'published': entry.published,
                'source': entry.source.title if 'source' in entry else 'Google News'
            })
    return news_items

def fetch_news_std_lib(url):
    """
    외부 라이브러리 없이 Python 표준 라이브러리(urllib, xml)만 사용합니다.
    SSL 인증서 에러 방지를 위해 보안 컨텍스트를 무시하도록 설정합니다.
    """
    import xml.etree.ElementTree as ET
    from urllib.request import Request, urlopen
    import ssl  # SSL 모듈 추가

    # Google News는 User-Agent 헤더가 없으면 403 에러를 반환할 수 있습니다.
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    # SSL 인증서 검증 무시 설정 (CERTIFICATE_VERIFY_FAILED 에러 방지)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        # urlopen에 context 파라미터 추가
        with urlopen(req, context=ctx) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            news_items = []
            # RSS 2.0의 channel > item 구조 파싱
            count = 0
            for item in root.findall('./channel/item'):
                if count >= LIMIT:
                    break
                
                title = item.find('title').text
                link = item.find('link').text
                pubDate = item.find('pubDate').text
                source_elem = item.find('source')
                source = source_elem.text if source_elem is not None else "Google News"
                
                news_items.append({
                    'title': title,
                    'link': link,
                    'published': pubDate,
                    'source': source
                })
                count += 1
            return news_items
            
    except Exception as e:
        print(f"{Colors.FAIL}Error fetching news: {e}{Colors.ENDC}")
        return []

def print_news(news_list):
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== Latest News for '{SEARCH_QUERY}' ==={Colors.ENDC}\n")
    
    if not news_list:
        print(f"{Colors.WARNING}No news found or connection failed.{Colors.ENDC}")
        return

    for idx, item in enumerate(news_list, 1):
        # 날짜 포맷 정리 (가능한 경우)
        date_str = item['published']
        
        print(f"{Colors.GREEN}[{idx}] {item['title']}{Colors.ENDC}")
        print(f"    {Colors.CYAN}Source: {item['source']} | Date: {date_str}{Colors.ENDC}")
        print(f"    {Colors.BLUE}{item['link']}{Colors.ENDC}")
        print("-" * 60)

def main():
    # Google News RSS URL 생성 (언어: 영어/미국 기준, 필요시 hl=ko, gl=KR 등으로 변경 가능)
    # 쿼리는 URL 인코딩 필요 (간단히 공백을 +로 치환)
    encoded_query = SEARCH_QUERY.replace(" ", "+")
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    print(f"Fetching news from: {rss_url}...")

    # feedparser 설치 여부 확인 후 분기 처리
    try:
        news_items = fetch_news_feedparser(rss_url)
        print(f"(Using 'feedparser' library)")
    except ImportError:
        print(f"(Using standard library - 'feedparser' not found)")
        news_items = fetch_news_std_lib(rss_url)

    print_news(news_items)

if __name__ == "__main__":
    main()