from io import BytesIO
from typing import Literal
from xml.etree.ElementTree import ElementTree

from pdf417gen import encode, render_image, render_svg
from PIL.Image import Image
from pydantic import validate_call


@validate_call()
def generate_qr_code(
    data: str, format: Literal["png", "jpg", "webp", "svg"], columns=8
) -> BytesIO:
    """
    Generates a QR code from the given data.

    Args:
        data (str): The data to encode in the QR code.
        format (Literal["png", "jpg", "webp", "svg"]): The format of the QR code image.
        columns (int): The number of columns in the QR code.

    Returns:
        BytesIO: A bytes stream containing the QR code image.
    """
    qr: list[list[int]] = encode(data, columns)
    qr_img: BytesIO = BytesIO()

    if format == "svg":
        svg: ElementTree = render_svg(qr, ratio=1)
        svg.write(qr_img)
    else:
        im: Image = render_image(qr, ratio=1)
        im.save(qr_img, format=format)

    qr_img.seek(0)
    return qr_img
