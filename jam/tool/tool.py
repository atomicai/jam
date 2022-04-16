LICENSE_AGREEMENT = "\
    May the odds\
    be ever\
    in your favor\
"

from pytgbot.api_types.sendable.reply_markup import InlineKeyboardButton, InlineKeyboardMarkup
from teleflask.messages import HTMLMessage


def display_state(state_name: str, value=None, diff=None):
    state = state_name.lower()
    response = None
    if state == "asked_license":
        response = HTMLMessage(
            f"<u>License agreement</u>\n{LICENSE_AGREEMENT}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("ACCEPT", callback_data="confirm_true"),
                    ],
                    [
                        InlineKeyboardButton("DECLINE", callback_data="confirm_false"),
                    ],
                ]
            ),
        )
    elif state == "rejected_license":
        response = HTMLMessage(
            "You cannot participate unless the <u>license agreement</u> is accepted.",
            [
                [
                    InlineKeyboardButton("⎌", callback_data="confirm_true"),
                ],
            ],
        )
    elif state == "ready_to_play":
        response = HTMLMessage(
            f'<u>Current price:</u>{str(value)}\n---\n<u>Next price:</u>{str(value - diff)}',
            [
                [
                    InlineKeyboardButton("⎌", callback_data="confirm_true"),
                ],
            ],
        )
    elif state == "asked_enroll":
        response = HTMLMessage(
            f'<u>Current price:</u>{str(value)}\n---\n<u>Next price:</u>{str(value - diff)}',
            [
                [
                    InlineKeyboardButton("🚀", callback_data="confirm_true"),
                ],
                [
                    InlineKeyboardButton("❌", callback_data="confirm_false"),
                ],
            ],
        )
    else:
        raise ValueError(f"state \"{state}\" is unknown")
    return response
