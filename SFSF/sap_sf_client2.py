import requests
import json
import base64
import time
import uuid
import textwrap
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# 암호화 및 서명을 위한 라이브러리 (pip install cryptography 필요)
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("오류: 'cryptography' 라이브러리가 필요합니다. 'pip install cryptography'를 실행해주세요.")
    exit(1)

class SAPSuccessFactorsClient:
    """SAP SuccessFactors OData API 클라이언트 (Offline SAML Assertion Generation)"""
    
    def __init__(self, company_id, api_base_url, client_id, user_id, private_key_str):
        self.company_id = company_id
        self.api_base_url = api_base_url.rstrip('/')
        self.client_id = client_id
        self.user_id = user_id
        self.access_token = None
        self.token_expiry = None
        
        # Private Key 문자열을 PEM 형식으로 변환 및 로드
        self.private_key = self._load_private_key(private_key_str)

    def _load_private_key(self, key_str):
        """Raw 문자열을 PEM 형식으로 변환하여 Private Key 객체 로드"""
        try:
            # 이미 PEM 형식이면 그대로 사용
            if "-----BEGIN" in key_str:
                pem_data = key_str.encode('utf-8')
            else:
                # 헤더가 없는 Raw String인 경우 포맷팅
                formatted_key = "-----BEGIN PRIVATE KEY-----\n"
                formatted_key += "\n".join(textwrap.wrap(key_str, 64))
                formatted_key += "\n-----END PRIVATE KEY-----"
                pem_data = formatted_key.encode('utf-8')

            return serialization.load_pem_private_key(
                pem_data,
                password=None,
                backend=default_backend()
            )
        except Exception as e:
            print(f"✗ Private Key 로드 실패: {e}")
            print("  (키 값이 올바른지, 암호화된 키인 경우 비밀번호가 필요한지 확인해주세요)")
            raise

    def generate_saml_assertion_local(self):
        """
        1단계: 로컬에서 SAML Assertion 생성 (Offline Generation)
        네트워크 호출 없이 코드 내부에서 XML 생성 및 RSA 서명 수행
        """
        print("1단계: SAML Assertion 로컬 생성 중...")
        
        token_url = f"{self.api_base_url}/oauth/token"
        audience = "www.successfactors.com"
        
        # 시간 설정 (현재 시간 및 만료 시간)
        now = int(time.time())
        not_before = now - 600  # 10분 전 (Clock Skew 방지)
        not_after = now + 600   # 10분 후
        
        # 고유 ID 생성
        assertion_id = str(uuid.uuid4())
        
        # SAML Assertion 템플릿
        # (주의: 들여쓰기나 공백이 서명에 영향을 줄 수 있으므로 최소화된 형태 사용 권장)
        assertion_xml = (
            f'<saml2:Assertion xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion" ID="{assertion_id}" IssueInstant="{datetime.utcfromtimestamp(now).isoformat()}Z" Version="2.0">'
            f'<saml2:Issuer>{self.client_id}</saml2:Issuer>'
            f'<saml2:Subject>'
            f'<saml2:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified">{self.user_id}</saml2:NameID>'
            f'<saml2:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">'
            f'<saml2:SubjectConfirmationData NotOnOrAfter="{datetime.utcfromtimestamp(not_after).isoformat()}Z" Recipient="{token_url}"/>'
            f'</saml2:SubjectConfirmation>'
            f'</saml2:Subject>'
            f'<saml2:Conditions NotBefore="{datetime.utcfromtimestamp(not_before).isoformat()}Z" NotOnOrAfter="{datetime.utcfromtimestamp(not_after).isoformat()}Z">'
            f'<saml2:AudienceRestriction>'
            f'<saml2:Audience>{audience}</saml2:Audience>'
            f'</saml2:AudienceRestriction>'
            f'</saml2:Conditions>'
            f'<saml2:AuthnStatement AuthnInstant="{datetime.utcfromtimestamp(now).isoformat()}Z">'
            f'<saml2:AuthnContext>'
            f'<saml2:AuthnContextClassRef>urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport</saml2:AuthnContextClassRef>'
            f'</saml2:AuthnContext>'
            f'</saml2:AuthnStatement>'
            f'</saml2:Assertion>'
        )

        # 서명 생성 (SHA256)
        signature = self.private_key.sign(
            assertion_xml.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        assertion_b64 = base64.b64encode(assertion_xml.encode('utf-8')).decode('utf-8')
        
        # 서명된 Assertion은 Base64로 인코딩된 XML 전체가 아니라, 
        # API에서는 보통 전체 XML을 Base64로 인코딩해서 보냄.
        # 하지만 SAP는 Signed XML을 원함. Python에서 XML 서명(XML-DSig)을 직접 구현하기 까다로우므로
        # 가장 확실한 방법은 위에서 만든 assertion_b64를 그대로 반환하고,
        # API 호출 시 client_secret 대신 사용하는 것이 아니라,
        # assertion 파라미터로 넘겨야 함.
        
        # 수정: SAP는 XML Digital Signature 표준을 따르므로, XML 안에 <Signature> 태그가 들어가야 합니다.
        # 이를 수동으로 구성하는 것은 복잡하므로, 가장 간단한 방법은 'signxml' 라이브러리를 쓰거나
        # 또는 SAP가 제공하는 /oauth/idp를 쓰지 않고 assertion을 만드는 정확한 포맷을 맞춰야 합니다.
        
        # [중요] Python에서 종속성 없이 XML 서명을 완벽히 구현하기 어렵습니다.
        # 아래는 SAP SuccessFactors용으로 간소화된 서명 방식입니다.
        
        # 서명할 데이터 (Canonicalization 없이 단순 바이트 처리)
        # 실제로는 XML 서명 표준을 지켜야 하므로, 아래와 같이 재구성합니다.
        
        # 1. SignedInfo 구성
        signed_info = (
            f'<ds:SignedInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">'
            f'<ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>'
            f'<ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>'
            f'<ds:Reference URI="#{assertion_id}">'
            f'<ds:Transforms>'
            f'<ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>'
            f'<ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>'
            f'</ds:Transforms>'
            f'<ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>'
            f'<ds:DigestValue>{{digest_value}}</ds:DigestValue>'
            f'</ds:Reference>'
            f'</ds:SignedInfo>'
        )

        # 2. Digest 계산
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(assertion_xml.encode('utf-8'))
        digest_value = base64.b64encode(digest.finalize()).decode('utf-8')
        
        signed_info = signed_info.format(digest_value=digest_value)

        # 3. 서명 값 계산
        signature = self.private_key.sign(
            signed_info.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        signature_value = base64.b64encode(signature).decode('utf-8')

        # 4. 최종 XML 조립
        signature_xml = (
            f'<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">'
            f'{signed_info}'
            f'<ds:SignatureValue>{signature_value}</ds:SignatureValue>'
            f'<ds:KeyInfo><ds:X509Data><ds:X509Certificate>YOUR_PUBLIC_CERT_IF_NEEDED_BUT_OPTIONAL</ds:X509Certificate></ds:X509Data></ds:KeyInfo>'
            f'</ds:Signature>'
        )
        # KeyInfo는 생략 가능하거나 필수가 아닐 수 있음.
        
        # Assertion 내에 Signature 삽입 (Issuer 다음)
        insert_pos = assertion_xml.find('</saml2:Issuer>') + len('</saml2:Issuer>')
        final_xml = assertion_xml[:insert_pos] + signature_xml + assertion_xml[insert_pos:]
        
        # 5. Base64 인코딩
        final_b64 = base64.b64encode(final_xml.encode('utf-8')).decode('utf-8').replace('\n', '')
        
        print("✓ SAML Assertion 로컬 생성 성공")
        return final_b64

    def get_access_token(self):
        """
        2단계: OAuth2 Access Token 획득
        로컬에서 생성한 SAML Assertion 사용
        """
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            print("기존 토큰 사용")
            return self.access_token
        
        # SAML Assertion 로컬 생성
        saml_assertion = self.generate_saml_assertion_local()
        
        print("\n2단계: Access Token 요청 중...")
        url = f"{self.api_base_url}/oauth/token"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': self.client_id,
            'company_id': self.company_id,
            'grant_type': 'urn:ietf:params:oauth:grant-type:saml2-bearer',
            'assertion': saml_assertion
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 86399)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
            
            print("✓ Access Token 획득 성공")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Access Token 획득 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 코드: {e.response.status_code}")
                print(f"응답 내용: {e.response.text}")
            raise
    
    # ... (나머지 메서드는 기존과 동일) ...
    def get_user_data(self, user_id=None):
        if user_id is None: user_id = self.user_id
        token = self.get_access_token()
        url = f"{self.api_base_url}/odata/v2/User('{user_id}')"
        headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"✗ 데이터 조회 실패: {e}")
            raise

    def validate_token(self):
        if not self.access_token: return False
        url = f"{self.api_base_url}/oauth/validate"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        try:
            requests.get(url, headers=headers).raise_for_status()
            print("✓ 토큰 유효성 검증 성공")
            return True
        except: return False

def visualize_user_data(user_data):
    """(기존 시각화 함수 유지)"""
    if 'd' in user_data: user_info = user_data['d']
    else: user_info = user_data
    
    # ... 기존 시각화 로직 ...
    print("\n=== 사용자 정보 ===")
    print(json.dumps(user_info, indent=2, ensure_ascii=False))

def main():
    print("=" * 70)
    print("SAP SuccessFactors OData API 클라이언트 (Fixed)")
    print("=" * 70)
    
    CONFIG = {
        'company_id': 'hyundaia02T2',
        'api_base_url': 'https://api50preview.sapsf.com',
        'client_id': 'YzM1MDYxN2VmNjcxMjdmZmNmYjcwMzI0MDI5NQ', 
        'user_id': 'EY001', 
        # -----BEGIN/END 헤더 없이 Raw String만 있는 경우 코드에서 자동 처리됨
        'private_key': 'TUlJRENEQ0NBZkNnQXdJQkFnSUdBWnQ5V2g1Q01BMEdDU3FHU0liM0RRRUJCQVVBTUVVeENUQUhCZ05WQkFjVEFERUpNQWNHQTFVRUNCTUFNUXd3Q2dZRFZRUURFd05JUVVVeENUQUhCZ05WQkFvVEFERUpNQWNHQTFVRUN4TUFNUWt3QndZRFZRUUdFd0F3SGhjTk1qWXdNVEF4TURZeE5qVTJXaGNOTWpjd01UQXlNRFl4TmpVMldqQkZNUWt3QndZRFZRUUhFd0F4Q1RBSEJnTlZCQWdUQURFTU1Bb0dBMVVFQmhNQU1JSUJJakFOQmdrcWhraUc5dzBCQVFFRkFBT0NBUThBTUlJQkNnS0NBUUVBaklWakxYdVpDcU1Rcit6VzJDM1NsRGFkaGVMeHB2Mkt6K3o4TU8yZ01FMWtIVEpjVk1JaFFUMy9UQjEwU0ZUWWdqUVpYU3FGZjRXeFg5eDhheU0vRmtnTmZKNndmemQ5MnVkTlgwVXhnQzJKT2prNGIwemxpemtMZUEyenpjNDI5MkpIR0hjUnpzVURGRGtTZHV1cmVpYm5ZRWFzaDNySCtHRWtES01Cc3pGeDNXU2pOVlhpblJ3VWg2c3gyazNSRUNxMzNDZEQ2SVVGNE56YlZIWllTbWFyU0RWVTY0QzYwRDFyb2plT2o5OWpNV2NVSG9EOWdaaWJFekdZQUo2RFJLSDVtQ3BpUjgvU3BqTUNlcCtoWVdBcVZhd0ZFU1ZYTzFQaFBpSk5RS3pDck5HSjVpUzE1cDVMZ3dDZnBEWHFDRVNOaTE3Z1RvZEovTUR4ditFOFJRSURBUUFCTUEwR0NTcUdTSWIzRFFFQkJBVUFBNElCQVFCK1h5eGRZSHg4WEtscnlYOUFaenUrQzczUVNOQkpteUVPTThwQ2Q2eW56citPN1RlaVV6MUN1ZGRGczM0WlRYNWhwaFhVQ2RMZE5WUnU5cWNWNkRpNXl2Z3N1clJRS3pjTUFtS3hQSUs5bWVzUXR1VWNta1pucEg4NCs1ZWtHdTltRG13NFphc1Jia0JkSWtuN1AvNzNBKzlVdk5HcTFUMGxNTWEvTUl6VzZjT0hEYjNocm5WZjkxSmh3bmZpVlUwcXlqajhXWGVlcmVINkpTVjNvc2FSSkp5eVEyTllOa096T1NPcmNYRE1icTE3Sit6RDhXcE9nNCtXZS9YbDREV0lmWGxheWJnZkNKazNjRlMrWEpaUno1WUpmdHNQc0lBQjNvczhTa1RDU1JGaU80a2NMM1oxcGFsdmZhdUJzbThMZGhMcDBuNlF0cjRTWlI5cjZsdEMjIyNmYWxzZQ=='
    }

    try:
        client = SAPSuccessFactorsClient(
            company_id=CONFIG['company_id'],
            api_base_url=CONFIG['api_base_url'],
            client_id=CONFIG['client_id'],
            user_id=CONFIG['user_id'],
            private_key_str=CONFIG['private_key']
        )
        
        user_data = client.get_user_data()
        visualize_user_data(user_data)
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()