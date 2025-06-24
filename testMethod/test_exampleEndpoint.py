import requests

# URL cơ bản và endpoint
url = "https://petstore.swagger.io/v2/pet/findByStatus"

# Tham số truy vấn (tìm thú cưng theo trạng thái)
params = {
    "status": ["available", "pending"]  # Có thể dùng ["sold"] hoặc bất kỳ kết hợp nào
}

# Gửi yêu cầu GET
response = requests.get(url, params=params)

# Kiểm tra mã trạng thái phản hồi
if response.status_code == 200:
    pets = response.json()
    print(f"Đã tìm thấy {len(pets)} thú cưng:")
    for pet in pets[:5]:  # In thử 5 kết quả đầu
        print(f"- ID: {pet.get('id')}, Name: {pet.get('name')}, Status: {pet.get('status')}")
else:
    print(f"Lỗi {response.status_code}: {response.text}")
