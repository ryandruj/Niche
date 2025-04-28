import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
import io
import random
from collections import Counter

TELEGRAM_BOT_TOKEN = '7569067862:AAF6ZqXP87SLktlTvLEN3-UsUQ9rUDqvUfc'

rpm_estimates = {
    "fitness": 5.0,
    "finance": 20.0,
    "tech": 12.0,
    "pets": 6.0,
    "travel": 4.0,
    "cooking": 7.0,
    "gaming": 3.0,
    "beauty": 8.0,
    "fashion": 6.0,
    "education": 10.0,
    "cryptocurrency": 22.0,
    "self improvement": 9.0,
    "cars": 7.0,
    "real estate": 18.0,
    "luxury": 15.0,
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('🚀 Send "next up" to see trending YouTube niches!')

def scrape_exploding_topics():
    url = 'https://explodingtopics.com/youtube'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    topics = soup.select('div.topic-title')
    growths = soup.select('div.topic-growth')

    data = []
    for topic, growth in zip(topics, growths):
        title = topic.get_text(strip=True)
        growth_text = growth.get_text(strip=True)
        if '%' in growth_text:
            growth_value = int(growth_text.strip('%').strip('+'))
            data.append((title, growth_value))
    return data

def scrape_google_trends():
    try:
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'xml')
        titles = [item.title.text for item in soup.find_all('item')]
        return titles
    except:
        return []

def scrape_glasp_trends():
    try:
        url = "https://glasp.co/youtube-trending"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        titles = [item.get_text(strip=True) for item in soup.select('div.css-1it2z2h')]
        return titles
    except:
        return []

def merge_trends():
    exploding_data = scrape_exploding_topics()
    google_data = scrape_google_trends()
    glasp_data = scrape_glasp_trends()

    exploded_titles = [title for title, growth in exploding_data]
    all_titles = exploded_titles + google_data + glasp_data
    all_titles = [title.lower().strip() for title in all_titles if title]
    counts = Counter(all_titles)

    topic_growth = {title.lower(): growth for title, growth in exploding_data}
    final_trends = []
    for topic, freq in counts.items():
        growth = topic_growth.get(topic, random.randint(10, 50))
        final_trends.append((topic.title(), growth))

    final_trends = sorted(final_trends, key=lambda x: x[1], reverse=True)
    return final_trends[:10]

def match_rpm(niche):
    niche_lower = niche.lower()
    for keyword, rpm in rpm_estimates.items():
        if keyword in niche_lower:
            return rpm
    return random.randint(3, 8)

def create_premium_card(title, growth, rpm_value):
    img = Image.new('RGB', (500, 270), color=(25, 25, 30))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
        font_growth = ImageFont.truetype("DejaVuSans.ttf", 22)
        font_rpm = ImageFont.truetype("DejaVuSans.ttf", 22)
        font_watermark = ImageFont.truetype("DejaVuSans.ttf", 18)
    except IOError:
        font_title = ImageFont.load_default()
        font_growth = ImageFont.load_default()
        font_rpm = ImageFont.load_default()
        font_watermark = ImageFont.load_default()

    draw.text((30, 40), title, font=font_title, fill=(255, 255, 255))
    draw.text((30, 110), f"Growth: +{growth}%", font=font_growth, fill=(80, 255, 80))
    draw.text((30, 150), f"Est. RPM: ~${rpm_value}", font=font_rpm, fill=(200, 200, 255))

    line_start_x = 30
    line_start_y = 200
    segment_length = 40
    points = [(line_start_x, line_start_y)]

    for i in range(1, 10):
        last_x, last_y = points[-1]
        new_x = last_x + segment_length
        new_y = last_y - random.randint(5, 15)
        points.append((new_x, new_y))

    draw.line(points, fill=(80, 255, 80), width=4)

    for point in points:
        draw.ellipse([point[0]-3, point[1]-3, point[0]+3, point[1]+3], fill=(80, 255, 80))

    watermark_text = "@ryandruj"
    text_width, text_height = draw.textsize(watermark_text, font=font_watermark)
    x_position = img.width - text_width - 10
    y_position = img.height - text_height - 10
    draw.text((x_position, y_position), watermark_text, font=font_watermark, fill=(150, 150, 150))

    bio = io.BytesIO()
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return  # Ignore non-text updates

    user_message = update.message.text.lower()

    if 'next up' in user_message:
        niches = merge_trends()
        for title, growth in niches:
            rpm_value = match_rpm(title)
            card = create_premium_card(title, growth, rpm_value)
            await update.message.reply_photo(photo=InputFile(card))
    else:
        await update.message.reply_text('❓ Send "next up" to get trending YouTube niches!')

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()


