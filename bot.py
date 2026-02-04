from botcity.plugins.http import BotHttpPlugin
from botcity.plugins.telegram import BotTelegramPlugin
from bs4 import BeautifulSoup as bs
from requests.exceptions import ConnectionError
from datetime import datetime
import os
from botcity.maestro import *
from time import sleep

class CinemaEmPoa:
    def __init__(
        self,
        url="https://cinemaempoa.com.br/program",
        token="8123421335:ABFwVGLoyMxTpPXWTtG7Ugl136L_1W8s9wE",
    ):
        self.http = BotHttpPlugin(url)
        self.telegram = telegram = BotTelegramPlugin(token=token)
        self.page = None
        self.message_films = None
        self.films = {}
        self.last_time = None
        self.last_update_id = self.load_offset()
        self.get_data()
        self.create_message()
        self.start()

    def save_offset(self, offset):
        with open("last_id.data", "w") as f:
            f.write(str(offset))

    def load_offset(self):
        if os.path.exists("last_id.data"):
            with open("last_id.data", "r") as f:
                return int(f.read())
        return None

    def get_page(self):
        try:
            source = self.http.get().content
            self.page = bs(source, "html.parser")
        except ConnectionError:
            print("error: connection")

    def get_films(self):
        _dates = self.page.find_all(class_="col-md-8")

        for _date in _dates:
            _date_text = _date.find(class_="mb-2 fs-5").getText()
            self.films[f"{_date_text}"] = []
            _films = _date.find_all(class_="mb-1")
            for _film in _films:
                _location = _film.getText().strip().split(" ")[-1]
                _title_film = _film.getText().strip().split(" ")[1:-1]
                _hour = _film.getText().strip().split(":")[0]
                _title_film = " ".join(_title_film)
                self.films[f"{_date_text}"].append(
                    {"location": _location, "title": _title_film, "hour": _hour}
                )

    def create_message(self):

        self.message_films = ""
        for films in self.films.keys():
            for film in self.films[f"{films}"]:
                location = film["location"]
                title = film["title"]
                hour = film["hour"]

                self.message_films += " ".join(
                    [films, "-", hour, "-", title, "-", location, "\n"]
                )

    def get_data(self):
        self.get_page()
        self.get_films()
        self.last_time = datetime.now()

    def bot_telegram(self):

        updates = self.telegram.bot.get_updates(offset=self.last_update_id)

        if len(updates) == 0:
            return

        for update in updates:
            message = update.message
            chat_id = message.chat.id
            text = message.text

            if text == "/start":
                self.telegram.bot.send_message(
                    chat_id,
                    "Este é o bot do Cinema em POA feito com o BotCity! Agora você pode ver todos os filmes que passarão na cidade :D\n/filmes - para ver a lista completa de filmes\n/ajuda - veja o que este bot pode fazer!\n\n Mais informações em www.lcsvillela.com",
                )

            elif text == "/status":
                self.telegram.bot.send_message(
                    chat_id, "O sistema está rodando perfeitamente! 🚀"
                )

            elif text == "/ajuda":
                self.telegram.bot.send_message(
                    chat_id, "Use /filmes para ver todos os filmes que estão passando!"
                )

            elif text == "/filmes":
                self.telegram.bot.send_message(chat_id, self.message_films)

            self.last_update_id = update.update_id + 1
            self.save_offset(self.last_update_id)

    def start(self):

        while True:
            if (datetime.now() - self.last_time).days:
                self.get_data()
                self.create_message()
            self.bot_telegram()
            sleep(1)


maestro = BotMaestroSDK.from_sys_args()
CinemaEmPoa()
maestro.finish_task(
    task_id=execution.task_id,
    status=AutomationTaskFinishStatus.SUCCESS,
    message="Task Finished with Success.",
    total_items=100,
    processed_items=100,
    failed_items=10,
)
