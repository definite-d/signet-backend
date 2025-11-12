from PIL.Image import Image
from io import BytesIO
from typing import Literal
from pdf417gen import encode, render_image, render_svg


# class WriterOptions(BaseModel):
#     module_width: float = 0.2
#     module_height: float = 15.0
#     quiet_zone: float = 6.5
#     font_size: float = 10
#     text_distance: float = 5
#     background: str = "white"
#     foreground: str = "black"
#     center_text: bool = True


# def generate_barcode(data: str, width: int = 3, height: int = 2):
#     barcode = Code128(data)
#     barcode.save(
#         "test",
#         WriterOptions(quiet_zone=0, font_size=0).model_dump(),
#     )
#     return barcode


def generate_qr_code(
    data: str, format: Literal["png", "jpg", "svg"]
) -> Image | BytesIO:
    qr: list[list[int]] = encode(data)
    im: Image = render_image(qr, ratio=1)
    svg = render_svg(qr, ratio=2)
    svg.write("test.svg")
    return im
    # render_svg(qr).save('test.svg')


if __name__ == "__main__":
    data = "3OP7sMiyXKf9FfQXUz/6bim5mI5xL2+e3Kk6W1x4GMiE7C2+5x6+V8jT6E0S8Y7RyWW9kpG3zZ9zBlYZaAxzBQ=="

    generate_qr_code(data, "png")
