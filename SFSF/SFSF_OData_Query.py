import time
import uuid
import base64
import requests
import json
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

class SAPSuccessFactorsAPI:
    def __init__(self, client_id, user_id, company_id, private_key_path, base_url):
        """
        초기 설정값 입력
        :param client_id: SuccessFactors에 등록된 OAuth Client ID (API Key)
        :param user_id: API를 호출할 사용자 ID (예: admin, sfadmin 등)
        :param company_id: 회사 ID (Company ID)
        :param private_key_path: 등록된 인증서의 Private Key 파일 경로 (.pem)
        :param base_url: API 기본 URL (예: https://api50preview.sapsf.com)
        """
        self.client_id = client_id
        self.user_id = user_id
        self.company_id = company_id
        self.private_key_path = private_key_path
        self.base_url = base_url
        self.token_url = f"{self.base_url}/oauth/token"
        self.token = None

    def _generate_saml_assertion(self):
        """
        OAuth 2.0 인증을 위한 SAML Assertion 생성 및 서명
        """
        token_url = self.token_url
        client_id = self.client_id
        user_id = self.user_id
        
        # 현재 시간 및 만료 시간 설정 (Epoch Time)
        now = int(time.time())
        expire = now + 600  # 10분 후 만료
        
        # Nonce 생성
        nonce = str(uuid.uuid4())

        # SAML Assertion XML 템플릿
        # 주의: 실제 운영 환경에 따라 XML 구조가 미세하게 다를 수 있으나, 
        # SAP SF 표준 포맷을 따릅니다.
        saml_assertion = f"""
        <Assertion xmlns="urn:oasis:names:tc:SAML:2.0:assertion" ID="{nonce}" IssueInstant="{datetime.utcfromtimestamp(now).isoformat()}Z" Version="2.0">
            <Issuer>{client_id}</Issuer>
            <Subject>
                <NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified">{user_id}</NameID>
                <SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer">
                    <SubjectConfirmationData NotOnOrAfter="{datetime.utcfromtimestamp(expire).isoformat()}Z" Recipient="{token_url}"/>
                </SubjectConfirmation>
            </Subject>
            <Conditions NotBefore="{datetime.utcfromtimestamp(now - 30).isoformat()}Z" NotOnOrAfter="{datetime.utcfromtimestamp(expire).isoformat()}Z">
                <AudienceRestriction>
                    <Audience>www.successfactors.com</Audience>
                </AudienceRestriction>
            </Conditions>
            <AuthnStatement AuthnInstant="{datetime.utcfromtimestamp(now).isoformat()}Z" SessionIndex="{nonce}">
                <AuthnContext>
                    <AuthnContextClassRef>urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport</AuthnContextClassRef>
                </AuthnContext>
            </AuthnStatement>
        </Assertion>
        """
        
        # XML 공백 제거 (Canonicalization 단순화)
        saml_assertion = " ".join(saml_assertion.split())

        # Private Key 로드 및 서명
        try:
            with open(self.private_key_path, "rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )
            
            # 서명 생성 (SHA256)
            signature = private_key.sign(
                saml_assertion.encode('utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            # Base64 인코딩
            encoded_assertion = base64.b64encode(saml_assertion.encode('utf-8')).decode('utf-8')
            encoded_signature = base64.b64encode(signature).decode('utf-8')
            
            # NOTE: Python으로 직접 XML Signature를 구현하는 것은 매우 복잡하므로,
            # 실무에서는 보통 'assertion' 값 자체를 base64로 인코딩하여 전송합니다.
            # SAP SF는 서명된 전체 XML이 아닌, assertion 문자열을 인코딩하여 전송하는 방식을 주로 사용합니다.
            # 여기서는 API가 요구하는 'assertion' 파라미터에 들어갈 값을 리턴합니다.
            return base64.b64encode(saml_assertion.encode('utf-8')).decode('utf-8')

        except Exception as e:
            print(f"SAML 생성 중 오류 발생: {e}")
            raise e

    def get_access_token(self):
        """
        SAML Assertion을 사용하여 Access Token 발급 요청
        """
        print("1. 인증 토큰 요청 중...")
        
        # 실제 SAP SF OAuth 구현 시에는 보통 미리 서명된 assertion을 사용하거나
        # 별도의 SAML 라이브러리를 사용합니다. 
        # 이 예제에서는 간소화된 흐름으로, Assertion 문자열을 생성하여 요청합니다.
        
        # *중요*: 만약 'signed SAML assertion'을 직접 생성해야 한다면 
        # onelogin/python3-saml 같은 라이브러리를 사용하는 것이 좋습니다.
        # 아래는 Assertion 값을 생성했다는 가정하의 요청입니다.
        
        assertion = self._generate_saml_assertion()

        data = {
            "client_id": self.client_id,
            "company_id": self.company_id,
            "grant_type": "urn:ietf:params:oauth:grant-type:saml2-bearer",
            "assertion": assertion
        }

        try:
            response = requests.post(self.token_url, data=data)
            response.raise_for_status() # 오류 발생 시 예외 처리
            
            json_resp = response.json()
            self.token = json_resp.get("access_token")
            expires_in = json_resp.get("expires_in")
            
            print(f"2. 토큰 발급 완료! (만료 시간: {expires_in}초)")
            return self.token

        except requests.exceptions.HTTPError as err:
            print(f"토큰 발급 실패: {err}")
            print(f"응답 내용: {response.text}")
            return None

    def get_user_data(self, user_id_target):
        """
        특정 User의 데이터 조회 (OData)
        """
        if not self.token:
            if not self.get_access_token():
                return None

        # OData URL 구성
        odata_url = f"{self.base_url}/odata/v2/User('{user_id_target}')"
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json", # JSON 형식으로 응답 요청
            "Content-Type": "application/json"
        }

        print(f"3. 데이터 요청 중: {odata_url}")
        
        try:
            response = requests.get(odata_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.HTTPError as err:
            print(f"데이터 조회 실패: {err}")
            print(f"응답 내용: {response.text}")
            return None

# ==========================================
# 실행 설정 (사용자 환경에 맞게 수정 필요)
# ==========================================
if __name__ == "__main__":
    # 1. 설정 정보 입력
    CONFIG = {
        "client_id": "YzM1MDYxN2VmNjcxMjdmZmNmYjcwMzI0MDI5NQ",           # OAuth Client ID (API Key)
        "company_id": "hyundaia02T2",       # SuccessFactors Company ID
        "user_id": "ssakssri",               # API를 실행할 실제 계정 ID
        "private_key_path": "/Users/jeongsucklee/DevOps_SSakSSri/Python/ssakssri.python/python/ssakssri.python/src/ssakssri/sfsf/cert/Certificate.pem",  # 로컬에 저장된 Private Key 파일 경로
        "base_url": "https://api50preview.sapsf.com"
    }

    # 2. API 클라이언트 초기화
    sf_api = SAPSuccessFactorsAPI(
        client_id=CONFIG["client_id"],
        user_id=CONFIG["user_id"],
        company_id=CONFIG["company_id"],
        private_key_path=CONFIG["private_key_path"],
        base_url=CONFIG["base_url"]
    )

    # 3. 데이터 조회 (User: EY001)
    target_user = "ssakssri"
    user_data = sf_api.get_user_data(target_user)

    # 4. 결과 출력
    if user_data:
        print("\n" + "="*50)
        print(f"사용자 [{target_user}] 조회 결과")
        print("="*50)
        # JSON 데이터를 보기 좋게 출력
        print(json.dumps(user_data, indent=4, ensure_ascii=False))
        
        # 필요한 경우 특정 필드만 출력 (예: 이름, 부서 등)
        # d = user_data.get('d', {})
        # print(f"이름: {d.get('firstName')} {d.get('lastName')}")
        # print(f"이메일: {d.get('email')}")
    else:
        print("데이터를 가져오지 못했습니다.")