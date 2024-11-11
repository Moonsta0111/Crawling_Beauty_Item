import os
import csv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from colorthief import ColorThief

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # 브라우저 창을 띄우지 않음 (백그라운드 실행)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 웹드라이버 설정 (ChromeDriverManager로 드라이버 자동 설치 및 서비스 설정)
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# 올리브영 립메이크업 카테고리 URL
category_url = 'https://www.oliveyoung.co.kr/store/display/getMCategoryList.do?dispCatNo=100000100020006'

# 이미지 저장 폴더 설정 (전체 기본 경로)
output_folder = r'C:\Users\john7\Desktop\crowling_beauty_item\beauty_item_img'

# CSV 파일 설정
csv_file_path = os.path.join(output_folder, "colors.csv")

# 폴더가 존재하지 않을 경우 생성
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# CSV 파일 생성 및 헤더 작성
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["색상명", "제품명", "RGB 값"])

# 페이지 로드
driver.get(category_url)

try:
    # 페이지가 완전히 로드될 때까지 대기
    wait = WebDriverWait(driver, 20)  # 대기 시간을 20초로 늘림
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.cate_prd_list.gtm_cate_list')))

    # 첫 번째, 두 번째, 세 번째 제품 링크 추출
    product_links = []
    for index in range(3):  # 첫 번째, 두 번째, 세 번째 제품 가져오기
        try:
            product = driver.find_element(By.CSS_SELECTOR, f'ul.cate_prd_list.gtm_cate_list li[data-index="{index}"] a.prd_thumb')
            product_link = product.get_attribute('href')
            product_links.append(product_link)
        except NoSuchElementException:
            print(f"제품 링크를 찾을 수 없습니다: data-index={index}")

    # 각 제품의 상세 페이지로 이동하여 색상별 이미지와 제품명 추출 및 저장
    for product_link in product_links:
        driver.get(product_link)

        # 제품명 추출
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'p.prd_name')))
            product_name_element = driver.find_element(By.CSS_SELECTOR, 'p.prd_name')
            product_name = product_name_element.text.strip()

            # 제품명을 안전한 파일 및 폴더 이름으로 변경
            safe_product_name = "".join([c for c in product_name if c.isalnum() or c == " "]).rstrip()
            product_folder_path = os.path.join(output_folder, safe_product_name)

            # 제품명 폴더 생성 (존재하지 않을 경우)
            if not os.path.exists(product_folder_path):
                os.makedirs(product_folder_path)

            # 색상별 이미지와 색상명 추출
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.thumb-color')))
            color_elements = driver.find_elements(By.CSS_SELECTOR, 'div.thumb-color')

            for color_element in color_elements:
                try:
                    # 이미지 URL 추출
                    img_tag = color_element.find_element(By.CSS_SELECTOR, 'img')
                    img_url = img_tag.get_attribute('src')

                    # 색상명 추출
                    color_name_input = color_element.find_element(By.CSS_SELECTOR, 'input[name^="colrCmprItemNm_"]')
                    color_name = color_name_input.get_attribute('value')

                    # 색상명을 파일 이름으로 안전하게 변환
                    safe_color_name = "".join([c for c in color_name if c.isalnum() or c == " "]).rstrip()
                    file_name = f"{safe_color_name}.jpg"
                    file_path = os.path.join(product_folder_path, file_name)

                    # 이미지 다운로드 및 저장
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        # 이미지 파일로 저장
                        with open(file_path, 'wb') as file:
                            file.write(response.content)
                        print(f'이미지 저장됨: {file_path}')
                        
                        # ColorThief를 사용하여 Dominant color 추출
                        color_thief = ColorThief(file_path)
                        dominant_color = color_thief.get_color(quality=1)

                        # CSV 파일에 색상명, 제품명, RGB 값 추가
                        with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerow([color_name, product_name, dominant_color])
                        print(f"색상명: {color_name}, 제품명: {product_name}, RGB 값: {dominant_color}")
                    else:
                        print(f'이미지 다운로드 실패: {img_url}')
                except NoSuchElementException:
                    print("색상 정보 또는 이미지 정보를 찾을 수 없습니다.")

        except (NoSuchElementException, TimeoutException):
            print(f"제품명 또는 색상 정보를 찾을 수 없습니다: {product_link}")

except Exception as e:
    # 오류 발생 시 오류 메시지를 출력
    print(f"오류가 발생했습니다: {e}")

finally:
    # 작업이 완료되면 웹드라이버 종료
    driver.quit()
