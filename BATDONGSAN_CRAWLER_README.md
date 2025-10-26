# BatDongSan.com.vn Crawler

Script để crawl dữ liệu bất động sản từ batdongsan.com.vn bằng Crawl4AI.

## Tính năng

- ✅ Crawl danh sách tin rao bất động sản
- ✅ Trích xuất thông tin chi tiết (tiêu đề, giá, diện tích, địa chỉ, số phòng ngủ, v.v.)
- ✅ Hỗ trợ phân trang (crawl nhiều trang)
- ✅ Xuất dữ liệu ra file JSON
- ✅ Xử lý nội dung động (JavaScript)
- ✅ Cấu hình linh hoạt

## Cài đặt

1. Đảm bảo bạn đã cài đặt Crawl4AI:
```bash
pip install crawl4ai
```

2. Cài đặt các dependencies cần thiết:
```bash
crawl4ai-setup
```

## Sử dụng

### Cách 1: Chạy script mẫu

Chạy trực tiếp script với ví dụ có sẵn:

```bash
python crawl_batdongsan.py
```

Script sẽ crawl danh sách căn hộ bán tại TP.HCM và lưu vào thư mục `crawled_data/`.

### Cách 2: Sử dụng trong code của bạn

```python
import asyncio
from crawl_batdongsan import BatDongSanCrawler

async def main():
    # Khởi tạo crawler
    crawler = BatDongSanCrawler(headless=True)

    # URL cần crawl
    url = "https://batdongsan.com.vn/ban-can-ho-chung-cu-tp-hcm"

    # Crawl 5 trang
    properties = await crawler.crawl_multiple_pages(url, num_pages=5)

    # Lưu kết quả
    crawler.save_to_json(properties, "my_properties.json")

    # In thống kê
    print(f"Đã crawl {len(properties)} bất động sản")

if __name__ == "__main__":
    asyncio.run(main())
```

### Cách 3: Crawl từ URL tùy chỉnh

```python
import asyncio
from crawl_batdongsan import BatDongSanCrawler

async def crawl_custom():
    crawler = BatDongSanCrawler(headless=True)

    # Thay đổi URL theo nhu cầu của bạn
    urls = [
        "https://batdongsan.com.vn/ban-nha-rieng-ha-noi",
        "https://batdongsan.com.vn/cho-thue-van-phong-tp-hcm",
        "https://batdongsan.com.vn/ban-dat-nen-binh-duong"
    ]

    all_data = []
    for url in urls:
        properties = await crawler.crawl_multiple_pages(url, num_pages=3)
        all_data.extend(properties)

    crawler.save_to_json(all_data, "all_properties.json")

asyncio.run(crawl_custom())
```

## Cấu trúc dữ liệu

Mỗi bất động sản được trích xuất sẽ có các trường sau:

```json
{
  "title": "Tiêu đề tin đăng",
  "link": "URL chi tiết",
  "price": "Giá bán/cho thuê",
  "area": "Diện tích",
  "location": "Địa chỉ",
  "bedrooms": "Số phòng ngủ",
  "toilets": "Số toilet",
  "description": "Mô tả ngắn",
  "image": "URL hình ảnh",
  "publish_date": "Ngày đăng"
}
```

## Tùy chỉnh CSS Selectors

Nếu cấu trúc website thay đổi, bạn có thể cập nhật CSS selectors trong method `get_listing_schema()`:

```python
def get_listing_schema(self):
    schema = {
        "name": "BatDongSan Property Listings",
        "baseSelector": "div.re__card-full",  # Container chính
        "fields": [
            {
                "name": "title",
                "selector": "a.pr-title",  # Cập nhật selector
                "type": "text",
            },
            # Thêm hoặc sửa các trường khác...
        ]
    }
    return schema
```

## Các ví dụ trong script

Script có sẵn 3 ví dụ:

1. **example_crawl_ban_can_ho()**: Crawl căn hộ bán tại TP.HCM
2. **example_crawl_cho_thue_nha()**: Crawl nhà cho thuê tại Hà Nội
3. **example_custom_url()**: Crawl từ URL tùy chỉnh với thống kê

Để chạy các ví dụ khác, uncomment trong hàm `main()`.

## Lưu ý quan trọng

⚠️ **Tuân thủ robots.txt và Terms of Service**
- Kiểm tra `robots.txt` của batdongsan.com.vn
- Tôn trọng giới hạn crawl rate
- Sử dụng dữ liệu hợp pháp và có đạo đức

⚠️ **CSS Selectors có thể thay đổi**
- Website có thể cập nhật cấu trúc HTML
- Nếu không crawl được dữ liệu, cần kiểm tra và cập nhật selectors
- Sử dụng DevTools của browser để inspect elements

⚠️ **Performance**
- Script có delay giữa các requests để tránh overload server
- Có thể điều chỉnh `delay_before_return_html` và `asyncio.sleep()` nếu cần

## Khắc phục sự cố

### Không crawl được dữ liệu

1. Kiểm tra URL có đúng không
2. Thử chạy với `headless=False` để xem browser
3. Kiểm tra CSS selectors có còn đúng không
4. Tăng `delay_before_return_html` nếu trang load chậm

### Lỗi timeout

```python
crawler_config = CrawlerRunConfig(
    # ... other config ...
    page_timeout=60000,  # Tăng timeout lên 60 giây
)
```

### Crawl chậm

- Giảm số lượng trang crawl
- Sử dụng caching
- Chạy song song nhiều URLs

## Mở rộng

### Crawl chi tiết từng bất động sản

```python
async def crawl_property_detail(self, url: str):
    """Crawl chi tiết một bất động sản"""
    # Define schema cho trang chi tiết
    detail_schema = {
        "baseSelector": "div.re__pr-specs-content",
        "fields": [
            {"name": "full_description", "selector": ".re__detail-content", "type": "text"},
            {"name": "contact_name", "selector": ".re__contact-name", "type": "text"},
            # ... thêm fields khác
        ]
    }
    # Implement crawl logic...
```

### Lưu vào Database

```python
import sqlite3

def save_to_database(properties):
    conn = sqlite3.connect('batdongsan.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY,
            title TEXT,
            price TEXT,
            area TEXT,
            location TEXT,
            link TEXT UNIQUE
        )
    ''')

    for prop in properties:
        cursor.execute('''
            INSERT OR IGNORE INTO properties (title, price, area, location, link)
            VALUES (?, ?, ?, ?, ?)
        ''', (prop['title'], prop['price'], prop['area'], prop['location'], prop['link']))

    conn.commit()
    conn.close()
```

## License

MIT License - Sử dụng tự do với trách nhiệm cá nhân.

## Đóng góp

Mọi đóng góp và cải tiến đều được chào đón!
