import unicodedata

def remove_vietnamese_tones(text):
    # Chuẩn hóa về dạng decomposed
    text = unicodedata.normalize('NFD', text)
    # Loại bỏ các dấu (các ký tự có category là 'Mn')
    text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
    # Chuyển đ → d, Đ → D
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text

# Ví dụ sử dụng

if __name__ == "__main__":
    # Test the function
    text_with_tone = "đại học bách khoa"
    text_with_tone = "mặt trời"
    text_with_tone = "Trên trời"
    text_with_tone = "đại"
    
    text_no_tone = remove_vietnamese_tones(text_with_tone)
    print(text_no_tone)  # Output: dai hoc bach khoa
