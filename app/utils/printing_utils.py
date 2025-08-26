import base64
import os
from pprint import pprint
from typing import Literal

IS_PRINT_DEV = True

ColorTypes = Literal[
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
]

ALLOWED_COLORS: set[ColorTypes] = {
    "magenta",
    "red",
    "blue",
    "green",
    "yellow",
    "cyan",
    "white",
    "black",
}


# TODO(): Pull out the dev log printing into a separate file, so that we don't have to import everything when we *.
def get_embedded_bookmark_file_link(dir_abs_slash_path: str, text: str):
    if text == "📁":
        file_path = os.path.join(dir_abs_slash_path, "folder_meta.json")
    else:
        file_path = os.path.join(dir_abs_slash_path, "bookmark_meta.json")

    # Ensure three slashes after file:
    uri = f"file://{file_path}" if file_path.startswith("/") else f"file:///{file_path}"
    return f"\033]8;;{uri}\033\\{text}\033]8;;\033\\"


def colorize_text_standard(
    text: str, color: ColorTypes | None = None, is_bg: bool = False
) -> str:
    if not color:
        return text

    if is_bg:
        bg_color_codes = {
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "yellow": (255, 255, 0),
            "blue": (0, 0, 255),
            "magenta": (255, 0, 255),
            "cyan": (0, 255, 255),
            "white": (255, 255, 255),
        }
        return f"\033[48;2;{bg_color_codes[color][0]};{bg_color_codes[color][1]};{bg_color_codes[color][2]}m{text}\033[0m"
    else:
        color_codes = {
            "black": 30,
            "red": 31,
            "green": 32,
            "yellow": 33,
            "blue": 34,
            "magenta": 35,
            "cyan": 36,
            "white": 37,
            # 'bright_black': 90,
            # 'bright_red': 91,
            # 'bright_green': 92,
            # 'bright_yellow': 93,
            # 'bright_blue': 94,
            # 'bright_magenta': 95,
            # 'bright_cyan': 96,
            # 'bright_white': 97
        }
        return f"\033[{color_codes[color]}m{text}\033[0m"


def colorize_text_rgb(
    text: str, color: tuple[int, int, int] | None = None, is_bg: bool = False
) -> str:
    if not color:
        return text

    if is_bg:
        return f"\033[48;2;{color[0]};{color[1]};{color[2]}m{text}\033[0m"
    else:
        return f"\033[38;2;{color[0]};{color[1]};{color[2]}m{text}\033[0m"


def colorize_text(
    text: str,
    color: ColorTypes | tuple[int, int, int] | None = None,
    bg_color: ColorTypes | tuple[int, int, int] | None = None,
) -> str:
    if not color and not bg_color:
        return text

    if color and isinstance(color, str) and color in ALLOWED_COLORS:
        text = colorize_text_standard(text, color)
    elif color and isinstance(color, tuple):
        text = colorize_text_rgb(text, color)

    if bg_color and isinstance(bg_color, str) and bg_color in ALLOWED_COLORS:
        text = colorize_text_standard(text, bg_color, is_bg=True)
    elif bg_color and isinstance(bg_color, tuple):
        text = colorize_text_rgb(text, bg_color, is_bg=True)
    return text


def print_color(
    text: str,
    color: ColorTypes | tuple[int, int, int] | None = None,
    bg_color: ColorTypes | tuple[int, int, int] | None = None,
    is_disabled: bool = False,
) -> None:
    if is_disabled:
        return
    print(colorize_text(text, color, bg_color))


def print_dev(
    text: str,
    color: ColorTypes | None = None,
    is_print: bool = IS_PRINT_DEV,
):
    if not is_print:
        return None
    if not color:
        return print(text)
    return print_color(text, color)


def pprint_dev(text, color: ColorTypes | None = None, is_print: bool = IS_PRINT_DEV):
    if not is_print:
        return None
    if not color:
        return pprint(text)
    return print_color(text, color)


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


def print_dev_empty_lines(n: int = 1, is_print: bool = IS_PRINT_DEV):
    if not is_print:
        return
    print("\n" * n)


def print_dev_separator(n: int = 10, char: str = "=", is_print: bool = IS_PRINT_DEV):
    if not is_print:
        return
    print(char * n)


# def gg_print(var, color=None):
#     # Try to get the variable name from the caller's source code
#     frame = inspect.currentframe().f_back
#     try:
#         # Get the line of code that called gg_print
#         call_line = inspect.getframeinfo(frame).code_context[0]
#         # Find the argument inside gg_print(...)
#         import re
#         match = re.search(r'gg_print\(([^,)\n]+)', call_line)
#         var_name = match.group(1).strip() if match else "variable"
#     except Exception:
#         var_name = "variable"
#     finally:
#         del frame

#     # Print in your double-line style

#     if color:
#         print_color(f"-- {var_name}:", color)
#     else:
#         print(f"-- {var_name}:")
#     pprint(var)
