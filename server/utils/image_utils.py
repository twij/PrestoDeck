"""Image processing utilities for the MPRIS server."""
import base64
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont

from config import DEFAULT_ARTWORK_SIZE

def resize_image(image_data, target_size=DEFAULT_ARTWORK_SIZE):
    """Resize image to target size and maintain aspect ratio with black borders."""
    try:
        print(f"Attempting to resize image, data length: {len(image_data)} bytes")
        img = Image.open(BytesIO(image_data))
        print(f"Successfully opened image: {img.format}, size: {img.size}, mode: {img.mode}")
        
        original_width, original_height = img.size
        aspect_ratio = original_width / original_height
        
        # Determine if we need borders (not close to square)
        needs_borders = aspect_ratio > 1.1 or aspect_ratio < 0.9
        
        if needs_borders:
            target_width, target_height = target_size
            background = Image.new('RGB', target_size, (0, 0, 0))
            
            if aspect_ratio > 1:  # landscape
                new_width = target_width
                new_height = int(new_width / aspect_ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                y_offset = (target_height - new_height) // 2
                background.paste(img, (0, y_offset))
                img = background
            else: # portrait
                new_height = target_height
                new_width = int(new_height * aspect_ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                x_offset = (target_width - new_width) // 2
                background.paste(img, (x_offset, 0))
                img = background
        else:
            img = img.resize(target_size, Image.LANCZOS)
        
        buffer = BytesIO()
        img.convert('RGB').save(buffer, format='JPEG', quality=85)
        print(f"Successfully resized image to {target_size}")
        return buffer.getvalue()
    except Exception as e:
        print(f"Error resizing image: {e}")
        return None

def fetch_art_from_url(url):
    """Fetch album art from URL and resize it."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return resize_image(response.content)
    except Exception as e:
        print(f"Error fetching image from URL {url}: {e}")
    return None

def generate_placeholder_art(text="No Cover", size=DEFAULT_ARTWORK_SIZE):
    """Generate a placeholder image with text."""
    try:
        img = Image.new('RGB', size, color=(0, 0, 128))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        try:
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            text_width = right - left
            text_height = bottom - top
        except AttributeError:
            try:
                text_width, text_height = font.getsize(text)
            except:
                text_width, text_height = len(text) * 10, 40
        
        position = ((size[0]-text_width)//2, (size[1]-text_height)//2)
        draw.text(position, text, fill=(255, 255, 255), font=font)
        
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        print(f"Error generating placeholder: {e}")
        try:
            img = Image.new('RGB', size, color=(0, 0, 100))
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            return buffer.getvalue()
        except:
            print("Unable to generate a basic placeholder")
            return None

def encode_image_base64(image_data):
    """Encode binary image data as base64 string."""
    if image_data:
        return base64.b64encode(image_data).decode('utf-8')
    return None