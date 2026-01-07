#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google AI 뉴스 크롤러
Google AI 관련 최신 뉴스를 RSS 피드에서 가져오는 프로그램
"""

import ssl
import certifi
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional
import json


def _fetch_rss_feed(url: str) -> bytes:
    """
    RSS 피드를 가져오는 함수
    
    Args:
        url: RSS 피드 URL
        
    Returns:
        RSS 피드 XML 데이터 (bytes)
        
    Raises:
        urllib.error.URLError: URL 접근 실패 시
        urllib.error.HTTPError: HTTP 에러 발생 시
    """
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    )
    
    # certifi의 인증서를 사용하여 SSL 컨텍스트 생성
    context = ssl.create_default_context(cafile=certifi.where())
    
    try:
        with urllib.request.urlopen(request, timeout=10, context=context) as response:
            return response.read()
    except Exception as e:
        print(f"RSS 피드 가져오기 실패: {url}")
        print(f"에러: {str(e)}")
        raise


def _parse_rss_feed(xml_content: bytes) -> List[Dict[str, str]]:
    """
    RSS 피드 XML을 파싱하여 뉴스 항목 리스트로 변환
    
    Args:
        xml_content: RSS 피드 XML 데이터
        
    Returns:
        뉴스 항목 리스트 (제목, 링크, 발행일, 설명 포함)
    """
    news_items = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # RSS 2.0 형식 파싱
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            link_elem = item.find('link')
            pub_date_elem = item.find('pubDate')
            description_elem = item.find('description')
            
            news_item = {
                'title': title_elem.text if title_elem is not None else 'No Title',
                'link': link_elem.text if link_elem is not None else '',
                'pub_date': pub_date_elem.text if pub_date_elem is not None else '',
                'description': description_elem.text if description_elem is not None else ''
            }
            
            news_items.append(news_item)
            
    except ET.ParseError as e:
        print(f"XML 파싱 에러: {str(e)}")
        raise
    
    return news_items


def fetch_latest_google_ai_news(max_items: int = 10) -> List[Dict[str, str]]:
    """
    Google AI 관련 최신 뉴스를 가져오는 메인 함수
    
    Args:
        max_items: 가져올 최대 뉴스 개수
        
    Returns:
        뉴스 항목 리스트
    """
    # Google News RSS 피드 URL (Google AI 관련 검색)
    url = 'https://news.google.com/rss/search?q=Google+AI&hl=en-US&gl=US&ceid=US:en'
    
    print(f"RSS 피드 가져오는 중: {url}")
    rss_xml = _fetch_rss_feed(url)
    
    print("RSS 피드 파싱 중...")
    news_items = _parse_rss_feed(rss_xml)
    
    # 최대 개수만큼만 반환
    return news_items[:max_items]


def display_news(news_items: List[Dict[str, str]]) -> None:
    """
    뉴스 항목을 보기 좋게 출력하는 함수
    
    Args:
        news_items: 뉴스 항목 리스트
    """
    print(f"\n{'='*80}")
    print(f"Google AI 최신 뉴스 ({len(news_items)}개)")
    print(f"{'='*80}\n")
    
    for idx, item in enumerate(news_items, 1):
        print(f"[{idx}] {item['title']}")
        print(f"    발행일: {item['pub_date']}")
        print(f"    링크: {item['link']}")
        if item['description']:
            # HTML 태그 제거 (간단한 방법)
            desc = item['description'].replace('<br>', ' ').replace('&nbsp;', ' ')
            print(f"    설명: {desc[:100]}..." if len(desc) > 100 else f"    설명: {desc}")
        print()


def save_to_json(news_items: List[Dict[str, str]], filename: str = 'google_ai_news.json') -> None:
    """
    뉴스 항목을 JSON 파일로 저장하는 함수
    
    Args:
        news_items: 뉴스 항목 리스트
        filename: 저장할 파일명
    """
    data = {
        'fetch_time': datetime.now().isoformat(),
        'count': len(news_items),
        'news': news_items
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"뉴스 데이터가 '{filename}' 파일로 저장되었습니다.")


if __name__ == '__main__':
    try:
        # 최신 뉴스 가져오기
        news_items = fetch_latest_google_ai_news(max_items=10)
        
        # 콘솔에 출력
        display_news(news_items)
        
        # JSON 파일로 저장
        save_to_json(news_items)
        
        print(f"\n총 {len(news_items)}개의 뉴스를 성공적으로 가져왔습니다.")
        
    except Exception as e:
        print(f"\n에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()