import json
from selenium import webdriver
from time import sleep
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re
from bs4 import BeautifulSoup
# 1. khai báo browser
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-notifications")
options.add_argument("--disable-extensions")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--mute-audio")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Không load images → nhanh gấp 5 lần
options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2
})

browser = webdriver.Chrome(options=options)
browser.set_page_load_timeout(300)
browser.set_script_timeout(300)

browser.get('http://facebook.com')

# điền thông tin vào ô user và pass
txtUser = browser.find_element(By.ID, 'email')
txtUser.send_keys('abc@gmail.com') # điền thông tin

txtPass = browser.find_element(By.ID, 'pass')
txtPass.send_keys('password') # điền thông tin

# submit form
txtPass.send_keys(Keys.ENTER)

sleep(30)

browser.get("https://www.facebook.com/me/friends")
sleep(5)

# Cuộn để tải thêm bạn bè
last_height = browser.execute_script("return document.body.scrollHeight")
while True:
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(3)  # Đợi tải
    new_height = browser.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height



# load hết trang friends
soup = BeautifulSoup(browser.page_source, 'html.parser')
friends_containers = soup.find_all('div', class_='x6s0dn4 x1obq294 x5a5i1n xde0f50 x15x8krk x1olyfxc x9f619 x78zum5 x1e56ztr xyamay9 xv54qhq x1l90r2v xf7dkkf x1gefphp')

friends_list = []
name_pattern = re.compile(r'^(.+?)(\d+) bạn chung$')  # Giữ nguyên để lấy tên và số (fallback nếu cần)

for container in friends_containers:
    # Lấy href từ <a> đầu tiên (profile URL)
    a_tag = container.find('a', href=True)
    profile_url = a_tag['href'] if a_tag else ''
    
    # Lấy full text của container và strip
    full_text = container.get_text(strip=True)
    
    # Parse tên từ text (fallback số nếu cần)
    match = name_pattern.match(full_text)
    if match:
        name = match.group(1).strip()  # Tên (ví dụ: "Hà Vi")
        fallback_mutual_count = int(match.group(2))  # Số bạn chung (nếu parse crawl fail)
    else:
        # Nếu không match pattern, thử lấy tên đơn giản
        name = full_text.split()[0].strip() if full_text else ''
        fallback_mutual_count = 0
    
    mutual_names = []  # List tên bạn chung thực tế
    
    if profile_url and name:
        # Crawl trang friends của profile này
        friends_page_url = profile_url + '/friends'
        print(f"Đang crawl bạn bè của {name} từ {friends_page_url}...")
        
        browser.get(friends_page_url)
        sleep(3)  # Delay load
        
        # Scroll load hết danh sách bạn bè của họ
        last_height = browser.execute_script("return document.body.scrollHeight") 
        scroll_attempts = 0 
        while scroll_attempts < 10: # Limit scroll 
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);") 
            sleep(2) 
            new_height = browser.execute_script("return document.body.scrollHeight") 
            if new_height == last_height: 
                break 
            last_height = new_height 
            scroll_attempts += 1
        
        # Parse HTML của trang friends của họ bằng BeautifulSoup
        their_soup = BeautifulSoup(browser.page_source, 'html.parser')
        their_containers = their_soup.find_all('div', class_='x6s0dn4 x1obq294 x5a5i1n xde0f50 x15x8krk x1olyfxc x9f619 x78zum5 x1e56ztr xyamay9 xv54qhq x1l90r2v xf7dkkf x1gefphp')
        
        their_friends_names = set()  # Set tên bạn bè của họ
        their_name_pattern = re.compile(r'^(.+?)(?:\d+ bạn chung)?$')  # Parse tên từ text của họ
        
        for their_container in their_containers:
            their_full_text = their_container.get_text(strip=True)
            their_match = their_name_pattern.match(their_full_text)
            if their_match:
                their_name = their_match.group(1).strip()
                if their_name and len(their_name) > 1:
                    their_friends_names.add(their_name)
        
        # Tìm intersection: bạn chung là những tên trong all_user_friends_names
        mutual_names = sorted(list(their_friends_names))
        print(f"  → Tìm thấy {len(mutual_names)} bạn chung cho {name}: {mutual_names[:5]}...")  # In 5 tên đầu
        
        # Quay lại trang gốc nếu cần (optional, để tránh ảnh hưởng loop sau)
        browser.get("https://www.facebook.com/me/friends")
        sleep(5)
    
    # Append vào list với mutual_names thay vì số
    friends_list.append({
        'name': name,
        'mutual_names': mutual_names,  # List tên bạn chung thực tế
        'mutual_count': len(mutual_names),  # Số lượng (từ crawl, fallback nếu fail)
        'profile_url': profile_url
    })

# Sau loop, lưu hoặc dùng friends_list
print(f"Đã build {len(friends_list)} entries với tên bạn chung thực tế.")

# Lưu vào JSON
data = {'friends': friends_list}
with open('parsed_friends1.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("\nĐã lưu vào 'parsed_friends1.json'")


browser.close()