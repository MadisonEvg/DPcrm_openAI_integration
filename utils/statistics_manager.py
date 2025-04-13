import json
import os
import schedule
import time
from config import Config
from threading import Thread
from logger_config import logger

def reset_statistics():
    stats_manager = StatisticsManager()
    stats_manager.reset_statistics()

def check_and_reset():
    today = time.localtime()
    if today.tm_mday == 1:
        reset_statistics()

def schedule_monthly_reset():
    # Задача будет запускаться каждый день в 00:00
    schedule.every().day.at("00:00").do(check_and_reset)

    while True:
        schedule.run_pending()
        time.sleep(60)
        
_scheduler_started = False
def start_statistic_scheduler():
    global _scheduler_started
    if not _scheduler_started:
        logger.info("----------- start_statistic_scheduler")
        _scheduler_started = True
        scheduler_thread = Thread(target=schedule_monthly_reset)
        scheduler_thread.daemon = True  # Этот поток будет завершаться при закрытии основного приложения
        scheduler_thread.start()

class StatisticsManager:
    def __init__(self):
        self.file_path = "statistics.json"
        self.stats = self.load_statistics()

    def load_statistics(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                return json.load(f)
        else:
            statistics = {
                "total_dialogs": 0,
                "successful_dialogs": 0,
                "conversion": 0.0,
                "GPT-4o-total_tokens_in": 0,
                "GPT-4o-total_tokens_out": 0,
                "GPT-4o-total_cost_in": 0.0,
                "GPT-4o-total_cost_out": 0.0,
                "processed_numbers": []
            }
            self.save_statistics(statistics)
            return statistics

    def save_statistics(self, stats=None):
        if stats is None:
            stats = self.stats
        with open(self.file_path, "w") as f:
            json.dump(stats, f, indent=4)

    def reset_statistics(self):
        self.stats = {
            "total_dialogs": 0,
            "successful_dialogs": 0,
            "conversion": 0.0,
            "GPT-4o-total_tokens_in": 0,
            "GPT-4o-total_tokens_out": 0,
            "GPT-4o-total_cost_in": 0.0,
            "GPT-4o-total_cost_out": 0.0,
            "processed_numbers": []
        }
        self.save_statistics()
        print("Статистика была сброшена.")

    def calculate_cost(self, input_tokens, output_tokens, model):
        if model == "gpt-4o":
            cost_in = input_tokens * Config.TOKEN_COST_IN_GPT4O
            cost_out = output_tokens * Config.TOKEN_COST_OUT_GPT4O
        else:
            cost_in = 0
            cost_out = 0
        return cost_in, cost_out

    def update_statistics(self, is_successful,
                          phone_number, input_tokens_o=0, output_tokens_o=0):
        if phone_number not in self.stats["processed_numbers"]:
            self.stats["processed_numbers"].append(phone_number)
            self.stats["total_dialogs"] += 1

        if is_successful:
            self.stats["successful_dialogs"] += 1

        if self.stats["total_dialogs"] > 0:
            self.stats["conversion"] = (self.stats["successful_dialogs"] / self.stats["total_dialogs"]) * 100
        else:
            self.stats["conversion"] = 0.0

        self.stats["GPT-4o-total_tokens_in"] += input_tokens_o
        self.stats["GPT-4o-total_tokens_out"] += output_tokens_o

        cost_in_o, cost_out_o = self.calculate_cost(input_tokens_o, output_tokens_o, model="gpt-4o")
        self.stats["GPT-4o-total_cost_in"] += cost_in_o
        self.stats["GPT-4o-total_cost_out"] += cost_out_o

        self.save_statistics()