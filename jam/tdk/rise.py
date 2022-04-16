import logging
import os
import pathlib
from html import escape

import dotenv
import jam.struct as struct
from flask import Flask, jsonify, request, send_from_directory
from icecream import ic
from jam import tool
from jam.ir.document_store import elastic
from jam.ir.document_store.base import Document
from jam.ir.engine import bm25

# also we want to send cool inline buttons below, so we need to import:
from pytgbot.api_types.sendable.reply_markup import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from teleflask import Teleflask

# because we wanna send HTML formatted messages below, we need:
from teleflask.messages import HTMLMessage, TextMessage
from telestate import TeleState, machine
from telestate.contrib.simple import SimpleDictDriver

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)

qas = []

dotenv.load_dotenv()

top_k = int(os.environ.get("TOP_K", 5))

app = Flask(
    __name__,
    template_folder='build',
    static_folder='build',
    root_path=pathlib.Path(os.getcwd()) / 'jam',
)

bot = Teleflask(api_key=os.environ.get("BOT_TOKEN"), app=app)

memo = SimpleDictDriver()

machine = machine.TeleStateMachine(__name__, database_driver=memo, teleflask_or_tblueprint=bot)

machine.ASKED_NAME = TeleState("ASKED_NAME", machine)
machine.ASKED_LICENSE = TeleState("ASKED_LICENSE", machine)
machine.REJECTED_LICENSE = TeleState("REJECTED_LICENSE", machine)
# machine.CONFIRMED_LICENSE = TeleState("CONFIRMED_LICENSED", machine)
machine.ASKED_ENROLL = TeleState("ASKED_ENROLL", machine)
machine.READY_TO_PLAY = TeleState("READY_TO_PLAY", machine)
machine.CONFIRMED_ENROLL = TeleState("CONFIRMED_ENROLL", machine)
machine.REJECTED_ENROLL = TeleState("REJECTED_ENROLL", machine)
machine.CONFIRM_DATA = TeleState("CONFIRM_DATA", machine)

store = elastic.ElasticDocStore()
retriever = bm25.BM25Retriever(store=store)


@app.route('/', defaults={'path': ''})
@app.route("/<path:path>")
def index(path):
    if path != '' and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


@app.route("/search", methods=["POST"])
def search():
    data = request.get_data(parse_form_data=True).decode("utf-8-sig")
    ic(data)
    response = [
        {
            "query": "What is reaping system?",
            "context": "The rules of the Hunger Games are simple. In punishment for the uprising, each of the twelve districts must provide one girl and one boy, called tributes, to participate. The twenty-four tributes will be imprisoned in a vast outdoor arena that could hold anything from a burning desert to a frozen wasteland. Over a period of several weeks, the competitors must fight to the death. The last tribute standing wins.",
            "answer": "There are twelve districts in the Republic of Panem. Each district has one girl and one boy, called tributes. The tributes compete in the Hunger Games, where they fight to the death in an outdoor arena. The last tribute standing wins.",
            "confidence": "0.5",
            "highlight": [9, 13],
        }
    ]
    return jsonify(response)


@machine.ALL.on_command("start")
def start(update, text):
    machine.set("ASKED_NAME")
    return TextMessage(
        f"Thank you for joining in 🤗! \nPlease tell me your name.",
        parse_mode="html",
    )


@machine.ALL.command("cancel")
def cmd_cancel(update, text):
    old_action = machine.CURRENT
    machine.set("DEFAULT")
    if old_action == machine.DEFAULT:
        return TextMessage("Nothing to cancel.", parse_mode="text")
    # end if
    return TextMessage("All actions are canceled.", parse_mode="text")


@machine.ASKED_NAME.on_message("text")
def fn_set_name(update, msg):
    username = msg.text.strip()
    user_id = Document.from_dict({"text": username.lower()}, uuid_type="uuid5")
    response = list(retriever.retrieve_top_k(index="login", query=username))[0][0]
    status: bool = False
    pointer = struct.NIterator(iter(response))
    while not status and pointer.has_next():
        r = pointer.next()
        if r.text == user_id.text:
            status = True

    if not status:
        return TextMessage(f"Sorry, {escape(username)} 😌 but you are not authorized. Register and come back, we'll miss you 🥲")

    machine.set("ASKED_LICENSE")
    return HTMLMessage(
        f"<u>License agreement</u>\n{tool.LICENSE_AGREEMENT}",
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


@machine.ASKED_LICENSE.on_update("callback_query")
def fn_set_license(update):
    choice = update.callback_query.data
    if choice != "confirm_true":
        machine.REJECTED_LICENSE.activate()
        return HTMLMessage(
            "You cannot participate unless the <u>license agreement</u> is accepted.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⎌", callback_data="confirm_true"),
                    ],
                ],
            ),
        )

    machine.set("ASKED_ENROLL")
    config = store.get_all_documents(index="initial")[0].meta

    return HTMLMessage(
        f'<u>Current price:</u>{str(config["value"])}\n---\n<u>Next price:</u>{str(config["value"] - config["diff"])}',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🚀", callback_data="confirm_true"),
                ],
                [
                    InlineKeyboardButton("❌", callback_data="confirm_false"),
                ],
            ],
        ),
    )


@machine.REJECTED_LICENSE.on_update("callback_query")
def fn_set_rejected(update):
    choice = update.callback_query.data
    if choice == "confirm_true":
        machine.set("ASKED_LICENSE")
        return HTMLMessage(
            f"<u>License agreement</u>\n{tool.LICENSE_AGREEMENT}",
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


@machine.ASKED_ENROLL.on_update("callback_query")
def fn_set_enroll(update):
    choice = update.callback_query.data
    config = store.get_all_documents(index="initial")[0].meta
    if choice != "confirm_true":
        machine.set("READY_TO_PLAY")
        return HTMLMessage(
            f'<u>Current price:</u>{config["value"]}\n---\n<u>Next price:</u>{config["value"] - config["diff"]}',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("⎌", callback_data="confirm_true"),
                    ],
                ],
            ),
        )


@machine.READY_TO_PLAY.on_update("callback_query")
def fn_set_ready_to_play(update):
    choice = update.callback_query.data
    config = store.get_all_documents(index="initial")[0].meta
    if choice == "confirm_true":
        machine.set("ASKED_ENROLL")
        return HTMLMessage(
            f'<u>Current price:</u>{str(config["value"])}\n---\n<u>Next price:</u>{str(config["value"] - config["diff"])}',
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🚀", callback_data="confirm_true"),
                    ],
                    [
                        InlineKeyboardButton("❌", callback_data="confirm_false"),
                    ],
                ],
            ),
        )


# end def
