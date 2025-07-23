from typing import Literal
import base64
import os

from app.bookmarks_consts import ABS_OBS_BOOKMARKS_DIR


def get_embedded_file_link(func):
    file_path = os.path.abspath(func.__code__.co_filename)

    # Ensure three slashes after file:
    uri = f"file://{file_path}" if file_path.startswith(
        '/') else f"file:///{file_path}"
    return f"\033]8;;{uri}\033\\{func.__name__}\033]8;;\033\\"


def get_embedded_bookmark_file_link(colon_separated_path, text):
    slash_separated_path = colon_separated_path.replace(':', '/')
    if text == "📁":
        file_path = ABS_OBS_BOOKMARKS_DIR + '/' + slash_separated_path + "/folder_meta.json"
    else:
        file_path = ABS_OBS_BOOKMARKS_DIR + '/' + slash_separated_path + "/bookmark_meta.json"

    # Ensure three slashes after file:
    uri = f"file://{file_path}" if file_path.startswith(
        '/') else f"file:///{file_path}"
    return f"\033]8;;{uri}\033\\{text}\033]8;;\033\\"


ColorTypes = Literal['black', 'red', 'green',
                     'yellow', 'blue', 'magenta', 'cyan', 'white']


def print_color(text: str, color: ColorTypes):
    color_codes = {
        'black': 30,
        'red': 31,
        'green': 32,
        'yellow': 33,
        'blue': 34,
        'magenta': 35,
        'cyan': 36,
        'white': 37
    }

    print(f"\033[{color_codes[color]}m{text}\033[0m")


def get_iterm_image_code(image_path, width="auto", height="auto"):
    try:
        with open(image_path, "rb") as f:
            img_data = f.read()
        b64_img = base64.b64encode(img_data).decode("utf-8")
        return f"\033]1337;File=inline=1;width={width};height={height};preserveAspectRatio=1:{b64_img}\a"
    except Exception:
        return None


def print_image(image_path, width="auto", height="auto"):
    """
    Print an image to the iTerm2 terminal using ANSI escape codes.
    """
    image_code = get_iterm_image_code(image_path, width, height)
    if image_code:
        print(image_code)

