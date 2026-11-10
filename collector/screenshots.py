"""OCR produces evidence text only. Users must verify all resulting records."""
import io

import pytesseract
from PIL import Image

MAX_IMAGE_BYTES = 10 * 1024 * 1024


def extract_text(payload):
    if len(payload) > MAX_IMAGE_BYTES:
        raise ValueError('Screenshot exceeds 10 MB.')
    with Image.open(io.BytesIO(payload)) as image:
        if image.width * image.height > 20_000_000:
            raise ValueError('Screenshot exceeds 20 megapixels.')
        image.load()
        available = pytesseract.get_languages(config='')
        if not {'eng', 'tha'} <= set(available):
            raise RuntimeError('Install Tesseract with English and Thai language data.')
        return pytesseract.image_to_string(image.convert('RGB'), lang='eng+tha', timeout=30)
