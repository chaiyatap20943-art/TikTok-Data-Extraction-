import io

import pytest
from PIL import Image, ImageDraw, ImageFont

from collector.screenshots import extract_text


def test_image_limits():
    with pytest.raises(ValueError):
        extract_text(b'x' * (10 * 1024 * 1024 + 1))
    image = Image.new('RGB', (5000, 4001), 'white')
    output = io.BytesIO()
    image.save(output, format='PNG')
    with pytest.raises(ValueError, match='megapixels'):
        extract_text(output.getvalue())


def test_real_ocr_synthetic_evidence():
    image = Image.new('RGB', (1000, 250), 'white')
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 48)
    draw = ImageDraw.Draw(image)
    draw.text((30, 30), 'VIEWS 1234', fill='black', font=font)
    output = io.BytesIO()
    image.save(output, format='PNG')
    text = extract_text(output.getvalue())
    assert '1234' in text
    # extract_text requires and uses both Thai and English models; values remain
    # unverified evidence and are never automatically committed to records.
