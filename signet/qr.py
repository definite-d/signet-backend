from io import BytesIO
from typing import Literal
from xml.etree.ElementTree import ElementTree

from pdf417gen import encode, render_image, render_svg
from PIL.Image import Image
from pydantic import validate_call


@validate_call()
def generate_qr_code(
    data: str, format: Literal["png", "jpg", "webp", "svg"]
) -> BytesIO:
    qr: list[list[int]] = encode(data)
    qr_img: BytesIO = BytesIO()

    if format == "svg":
        svg: ElementTree = render_svg(qr, ratio=1)
        svg.write(qr_img)
    else:
        im: Image = render_image(qr, ratio=1)
        im.save(qr_img, format=format)
    return qr_img
