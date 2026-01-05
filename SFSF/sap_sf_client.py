import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import base64

class SAPSuccessFactorsClient:
    """SAP SuccessFactors OData API 클라이언트 (OAuth2 SAML Bearer Assertion Flow)"""
    
    def __init__(self, company_id, api_base_url, client_id, user_id, private_key):
        """
        초기화
        
        Args:
            company_id: SAP SF 회사 ID
            api_base_url: API 기본 URL (예: https://api50preview.sapsf.com)
            client_id: OAuth2 클라이언트 ID (API Key)
            user_id: API 호출할 사용자 ID
            private_key: X.509 인증서의 Private Key (PEM 형식)
        """
        self.company_id = company_id
        self.api_base_url = api_base_url.rstrip('/')
        self.client_id = client_id
        self.user_id = user_id
        self.private_key = private_key
        self.access_token = None
        self.token_expiry = None
    
    def generate_saml_assertion(self):
        """
        1단계: SAML Assertion 생성
        /oauth/idp 엔드포인트를 호출하여 SAML assertion 획득
        """
        url = f"{self.api_base_url}/oauth/idp"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # SAML assertion 요청 데이터
        data = {
            'client_id': self.client_id,
            'user_id': self.user_id,
            'token_url': f"{self.api_base_url}/oauth/token",
            'private_key': self.private_key
        }
        
        print("1단계: SAML Assertion 생성 중...")
        print(f"URL: {url}")
        print(f"User ID: {self.user_id}")
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            # 응답은 base64로 인코딩된 SAML assertion
            saml_assertion = response.text
            print("✓ SAML Assertion 생성 성공")
            
            # SAML assertion 디코딩하여 확인 (선택사항)
            try:
                decoded = base64.b64decode(saml_assertion)
                print(f"SAML Assertion 길이: {len(saml_assertion)} bytes")
            except:
                pass
            
            return saml_assertion
            
        except requests.exceptions.RequestException as e:
            print(f"✗ SAML Assertion 생성 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 코드: {e.response.status_code}")
                print(f"응답 내용: {e.response.text}")
            raise
    
    def get_access_token(self):
        """
        2단계: OAuth2 Access Token 획득
        SAML Bearer Assertion을 사용하여 access token 획득
        """
        # 토큰이 유효하면 재사용
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            print("기존 토큰 사용")
            return self.access_token
        
        # 1단계: SAML Assertion 생성
        saml_assertion = self.generate_saml_assertion()
        
        # 2단계: Access Token 요청
        print("\n2단계: Access Token 요청 중...")
        url = f"{self.api_base_url}/oauth/token"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # OAuth2 SAML Bearer Assertion Grant Type
        data = {
            'company_id': self.company_id,
            'client_id': self.client_id,
            'grant_type': 'urn:ietf:params:oauth:grant-type:saml2-bearer',
            'assertion': saml_assertion
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # 토큰 만료 시간 설정
            expires_in = token_data.get('expires_in', 86399)  # 기본 24시간
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)  # 5분 여유
            
            print("✓ Access Token 획득 성공")
            print(f"Token Type: {token_data.get('token_type', 'Bearer')}")
            print(f"만료 시간: {expires_in}초 ({expires_in/3600:.1f}시간)")
            
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Access Token 획득 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 코드: {e.response.status_code}")
                print(f"응답 내용: {e.response.text}")
            raise
    
    def validate_token(self):
        """
        토큰 유효성 검증 (선택사항)
        """
        if not self.access_token:
            print("토큰이 없습니다.")
            return False
        
        url = f"{self.api_base_url}/oauth/validate"
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            validation_data = response.json()
            print("✓ 토큰 유효성 검증 성공")
            print(json.dumps(validation_data, indent=2))
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"✗ 토큰 검증 실패: {e}")
            return False
    
    def get_user_data(self, user_id=None):
        """특정 사용자 정보 조회"""
        
        if user_id is None:
            user_id = self.user_id
        
        # Access Token 획득
        token = self.get_access_token()
        
        # API 호출
        url = f"{self.api_base_url}/odata/v2/User('{user_id}')"
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        print(f"\n사용자 데이터 조회 중: {user_id}")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            print("✓ 사용자 데이터 조회 성공")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"✗ 데이터 조회 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 코드: {e.response.status_code}")
                print(f"응답 내용: {e.response.text}")
            raise
    
    def get_all_users(self, top=100, filter_query=None):
        """모든 사용자 목록 조회"""
        
        token = self.get_access_token()
        
        url = f"{self.api_base_url}/odata/v2/User"
        params = {
            '$top': top,
            '$format': 'json'
        }
        
        if filter_query:
            params['$filter'] = filter_query
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json'
        }
        
        print(f"\n사용자 목록 조회 중 (최대 {top}명)...")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('d', {}).get('results', [])
            print(f"✓ {len(results)}명의 사용자 조회 성공")
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"✗ 데이터 조회 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 코드: {e.response.status_code}")
                print(f"응답 내용: {e.response.text}")
            raise


def load_private_key_from_file(filepath):
    """
    PEM 파일에서 Private Key 읽기
    
    Args:
        filepath: 인증서 파일 경로
        
    Returns:
        Private Key 문자열
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Private Key 부분만 추출
        if 'BEGIN' in content and 'PRIVATE KEY' in content:
            # 이미 올바른 형식
            return content
        else:
            print("⚠ 경고: Private Key를 찾을 수 없습니다. 파일 내용 확인이 필요합니다.")
            return content
            
    except Exception as e:
        print(f"✗ Private Key 파일 읽기 실패: {e}")
        raise


def visualize_user_data(user_data):
    """사용자 데이터 시각화"""
    
    # OData 응답에서 실제 데이터 추출
    if 'd' in user_data:
        user_info = user_data['d']
    else:
        user_info = user_data
    
    print("\n=== 사용자 정보 ===")
    print(json.dumps(user_info, indent=2, ensure_ascii=False))
    
    # 주요 정보 추출 및 출력
    key_fields = {
        'userId': '사용자 ID',
        'username': '사용자명',
        'firstName': '이름',
        'lastName': '성',
        'email': '이메일',
        'department': '부서',
        'division': '사업부',
        'location': '위치',
        'title': '직급',
        'status': '상태',
        'hireDate': '입사일',
        'custom01': '커스텀 필드 1',
        'custom02': '커스텀 필드 2',
    }
    
    print("\n=== 주요 정보 요약 ===")
    extracted_data = {}
    for field, label in key_fields.items():
        value = user_info.get(field, None)
        if value is not None and value != '':
            print(f"{label}: {value}")
            extracted_data[label] = value
    
    # 데이터 시각화
    if extracted_data:
        # 한글 폰트 설정
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
        fig, ax = plt.subplots(figsize=(14, max(8, len(extracted_data) * 0.5)))
        fig.suptitle('SAP SuccessFactors User Information', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        ax.axis('tight')
        ax.axis('off')
        
        table_data = [[k, str(v)] for k, v in extracted_data.items()]
        table = ax.table(cellText=table_data, 
                        colLabels=['Field', 'Value'],
                        cellLoc='left',
                        loc='center',
                        colWidths=[0.3, 0.7])
        
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.5)
        
        # 헤더 스타일
        for i in range(2):
            table[(0, i)].set_facecolor('#0070C0')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 교대로 행 색상
        for i in range(1, len(table_data) + 1):
            for j in range(2):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#F2F2F2')
                else:
                    table[(i, j)].set_facecolor('#FFFFFF')
        
        plt.tight_layout()
        plt.savefig('sap_sf_user_info.png', dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        print("\n✓ 시각화 이미지 저장 완료: sap_sf_user_info.png")
        plt.show()
    else:
        print("\n⚠ 시각화할 데이터가 없습니다.")


def main():
    """메인 실행 함수"""
    
    print("=" * 70)
    print("SAP SuccessFactors OData API 클라이언트")
    print("OAuth2 SAML Bearer Assertion Flow")
    print("=" * 70)
    
    # ===== 설정 (실제 값으로 변경 필요) =====
    CONFIG = {
        'company_id': 'hyundaia02T2',
        'api_base_url': 'https://api50preview.sapsf.com',
        'client_id': 'YzM1MDYxN2VmNjcxMjdmZmNmYjcwMzI0MDI5NQ',  # Manage OAuth2 Client Applications에서 생성된 API Key
        'user_id': 'EY001',  # API를 호출할 사용자 ID
        'private_key': 'TUlJRENEQ0NBZkNnQXdJQkFnSUdBWnQ5V2g1Q01BMEdDU3FHU0liM0RRRUJCQVVBTUVVeENUQUhCZ05WQkFjVEFERUpNQWNHQTFVRUNCTUFNUXd3Q2dZRFZRUURFd05JUVVVeENUQUhCZ05WQkFvVEFERUpNQWNHQTFVRUN4TUFNUWt3QndZRFZRUUdFd0F3SGhjTk1qWXdNVEF4TURZeE5qVTJXaGNOTWpjd01UQXlNRFl4TmpVMldqQkZNUWt3QndZRFZRUUhFd0F4Q1RBSEJnTlZCQWdUQURFTU1Bb0dBMVVFQXhNRFNFRkZNUWt3QndZRFZRUUtFd0F4Q1RBSEJnTlZCQXNUQURFSk1BY0dBMVVFQmhNQU1JSUJJakFOQmdrcWhraUc5dzBCQVFFRkFBT0NBUThBTUlJQkNnS0NBUUVBaklWakxYdVpDcU1Rcit6VzJDM1NsRGFkaGVMeHB2Mkt6K3o4TU8yZ01FMWtIVEpjVk1JaFFUMy9UQjEwU0ZUWWdqUVpYU3FGZjRXeFg5eDhheU0vRmtnTmZKNndmemQ5MnVkTlgwVXhnQzJKT2prNGIwemxpemtMZUEyenpjNDI5MkpIR0hjUnpzVURGRGtTZHV1cmVpYm5ZRWFzaDNySCtHRWtES01Cc3pGeDNXU2pOVlhpblJ3VWg2c3gyazNSRUNxMzNDZEQ2SVVGNE56YlZIWllTbWFyU0RWVTY0QzYwRDFyb2plT2o5OWpNV2NVSG9EOWdaaWJFekdZQUo2RFJLSDVtQ3BpUjgvU3BqTUNlcCtoWVdBcVZhd0ZFU1ZYTzFQaFBpSk5RS3pDck5HSjVpUzE1cDVMZ3dDZnBEWHFDRVNOaTE3Z1RvZEovTUR4ditFOFJRSURBUUFCTUEwR0NTcUdTSWIzRFFFQkJBVUFBNElCQVFCK1h5eGRZSHg4WEtscnlYOUFaenUrQzczUVNOQkpteUVPTThwQ2Q2eW56citPN1RlaVV6MUN1ZGRGczM0WlRYNWhwaFhVQ2RMZE5WUnU5cWNWNkRpNXl2Z3N1clJRS3pjTUFtS3hQSUs5bWVzUXR1VWNta1pucEg4NCs1ZWtHdTltRG13NFphc1Jia0JkSWtuN1AvNzNBKzlVdk5HcTFUMGxNTWEvTUl6VzZjT0hEYjNocm5WZjkxSmh3bmZpVlUwcXlqajhXWGVlcmVINkpTVjNvc2FSSkp5eVEyTllOa096T1NPcmNYRE1icTE3Sit6RDhXcE9nNCtXZS9YbDREV0lmWGxheWJnZkNKazNjRlMrWEpaUno1WUpmdHNQc0lBQjNvczhTa1RDU1JGaU80a2NMM1oxcGFsdmZhdUJzbThMZGhMcDBuNlF0cjRTWlI5cjZsdEMjIyNmYWxzZQ=='  # 다운로드한 인증서 파일 경로
    }
    
    # 설정 확인
    if 'YOUR_' in str(CONFIG.values()):
        print("\n⚠ 경고: 설정값을 실제 값으로 변경해주세요!")
        print("\n필수 설정 항목:")
        print("  1. company_id: SAP SuccessFactors 회사 ID")
        print("  2. api_base_url: API 기본 URL (예: https://api50preview.sapsf.com)")
        print("  3. client_id: Manage OAuth2 Client Applications에서 생성된 API Key")
        print("  4. user_id: API를 호출할 사용자 ID")
        print("  5. private_key_file: X.509 인증서 파일 경로 (PEM 형식)")
        print("\n인증서 파일에서 Private Key 추출 방법:")
        print("  - 텍스트 에디터로 certificate.pem 파일을 엽니다")
        print("  - '-----BEGIN ENCRYPTED PRIVATE KEY-----'와")
        print("    '-----END ENCRYPTED PRIVATE KEY-----' 사이의 내용이 Private Key입니다")
        print("\n테스트 모드로 실행합니다 (실제 API 호출 없음)\n")
        
        # 샘플 데이터로 시각화 테스트
        sample_data = {
            'd': {
                'userId': 'EY001',
                'username': 'john.doe',
                'firstName': 'John',
                'lastName': 'Doe',
                'email': 'john.doe@example.com',
                'department': 'IT Department',
                'division': 'Technology Division',
                'location': 'Seoul Office',
                'title': 'Senior Developer',
                'status': 'Active',
                'hireDate': '/Date(1609459200000)/'
            }
        }
        print("샘플 데이터로 시각화를 테스트합니다...\n")
        visualize_user_data(sample_data)
        return
    
    try:
        # Private Key 파일 읽기
        print(f"\nPrivate Key 파일 읽기: {CONFIG['private_key']}")
        # private_key = load_private_key_from_file(CONFIG['private_key_file'])
        # private_key = CONFIG['private_key']
        
        # 클라이언트 생성
        client = SAPSuccessFactorsClient(
            company_id=CONFIG['company_id'],
            api_base_url=CONFIG['api_base_url'],
            client_id=CONFIG['client_id'],
            user_id=CONFIG['user_id'],
            private_key=CONFIG['private_key']
        )
        
        # 사용자 데이터 조회
        user_data = client.get_user_data()
        
        # 데이터 시각화
        visualize_user_data(user_data)
        
        # 선택사항: 토큰 검증
        print("\n토큰 유효성 검증 중...")
        client.validate_token()
        
        print("\n✓ 프로그램 실행 완료!")
        
    except FileNotFoundError:
        print(f"\n✗ Private Key 파일을 찾을 수 없습니다: {CONFIG['private_key_file']}")
        print("파일 경로를 확인해주세요.")
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()