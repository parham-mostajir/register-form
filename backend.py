from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)  # حل مشکل CORS

# مسیر فایل CSV از گیت‌هاب (لینک خام)
file_path = "https://raw.githubusercontent.com/parham-mostajir/register-form/main/DATA122.csv"

try:
    df = pd.read_csv(file_path, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()  # حذف فاصله‌های اضافی
    df.drop_duplicates(inplace=True)  # حذف ردیف‌های تکراری
    df.dropna(subset=['روزهای حضور', 'رشته', 'ساعات حضور'], inplace=True)  # حذف ردیف‌های نامعتبر

    # پاکسازی و تبدیل ستون "روزهای حضور" به لیست
    df['روزهای حضور'] = df['روزهای حضور'].apply(lambda x: [day.strip() for day in x.split(',')] if isinstance(x, str) else [])
except Exception as e:
    print(f"خطا در بارگذاری داده‌ها: {e}")
    df = pd.DataFrame(columns=['نام', 'رشته', 'روزهای حضور', 'ساعات حضور'])

# نگاشت روزها به اعداد
day_mapping = {
    "شنبه": 0, "یکشنبه": 1, "دوشنبه": 2, 
    "سه‌شنبه": 3, "چهارشنبه": 4, "پنج‌شنبه": 5, "جمعه": 6
}

# تابع برگرداندن نام فارسی روز بر اساس عدد
def get_farsi_day(day_number):
    for day, num in day_mapping.items():
        if num == day_number:
            return day
    return None

# تبدیل ساعت (مثلاً "10:00 - 12:00") به لیست عددی برای مقایسه
def extract_time_ranges(time_str):
    try:
        start, end = time_str.split('-')
        return int(start.replace(':', '')), int(end.replace(':', ''))
    except:
        return None, None

@app.route('/find_schedule', methods=['GET'])
def find_schedule():
    day_number = request.args.get('day')
    user_major = request.args.get('major', '').strip()
    advisor_time = request.args.get('advisorTime', '').strip()
    consultant_time = request.args.get('consultantTime', '').strip()

    if not day_number or not user_major or not advisor_time:
        return jsonify({"error": "لطفاً یک روز، رشته و ساعت حضور استاد راهنما را وارد کنید"}), 400

    try:
        day_number = int(day_number)
    except ValueError:
        return jsonify({"error": "فرمت روز نامعتبر است"}), 400

    selected_day = get_farsi_day(day_number)
    if not selected_day:
        return jsonify({"error": "روز نامعتبر است"}), 400

    # تبدیل ساعت‌های استاد راهنما و مشاور
    advisor_start, advisor_end = extract_time_ranges(advisor_time)
    consultant_start, consultant_end = extract_time_ranges(consultant_time) if consultant_time else (None, None)

    if not advisor_start or not advisor_end:
        return jsonify({"error": "فرمت ساعت استاد راهنما نامعتبر است"}), 400

    # فیلتر بر اساس روز و رشته
    available_professors = df[
        df['روزهای حضور'].apply(lambda x: selected_day in x) & 
        (df['رشته'].str.strip() == user_major)
    ]

    # فیلتر بر اساس ساعت حضور استاد راهنما و مشاور
    matched_professors = []
    for _, row in available_professors.iterrows():
        prof_start, prof_end = extract_time_ranges(row['ساعات حضور'])
        if not prof_start or not prof_end:
            continue  # پرش از ردیف‌های نامعتبر
        
        # بررسی تطابق ساعت حضور با استاد راهنما یا استاد مشاور
        if (advisor_start <= prof_end and advisor_end >= prof_start) or \
           (consultant_start and consultant_end and consultant_start <= prof_end and consultant_end >= prof_start):
            matched_professors.append(row.to_dict())

    return jsonify({"day": selected_day, "professors": matched_professors})

if __name__ == '__main__':
    app.run(debug=True)
