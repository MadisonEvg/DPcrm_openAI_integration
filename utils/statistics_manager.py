import json
import os
from config import Config

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
                "GPT-4o-MINI-total_tokens_in": 0,
                "GPT-4o-MINI-total_tokens_out": 0,
                "GPT-4o-total_cost_in": 0.0,
                "GPT-4o-total_cost_out": 0.0,
                "GPT-4o-MINI-total_cost_in": 0.0,
                "GPT-4o-MINI-total_cost_out": 0.0,
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
            "GPT-4o-MINI-total_tokens_in": 0,
            "GPT-4o-MINI-total_tokens_out": 0,
            "GPT-4o-total_cost_in": 0.0,
            "GPT-4o-total_cost_out": 0.0,
            "GPT-4o-MINI-total_cost_in": 0.0,
            "GPT-4o-MINI-total_cost_out": 0.0,
            "processed_numbers": []
        }
        self.save_statistics()
        print("Статистика была сброшена.")

    def calculate_cost(self, input_tokens, output_tokens, model):
        if model == "gpt-4o":
            cost_in = input_tokens * Config.TOKEN_COST_IN_GPT4O
            cost_out = output_tokens * Config.TOKEN_COST_OUT_GPT4O
        elif model == "gpt-4o-mini":
            cost_in = input_tokens * Config.TOKEN_COST_IN_GPT4_MINI
            cost_out = output_tokens * Config.TOKEN_COST_OUT_GPT4_MINI
        else:
            cost_in = 0
            cost_out = 0
        return cost_in, cost_out

    def update_statistics(self, input_tokens_mini, output_tokens_mini, input_tokens_o, output_tokens_o, is_successful,
                          phone_number):
        if phone_number not in self.stats["processed_numbers"]:
            self.stats["processed_numbers"].append(phone_number)
            self.stats["total_dialogs"] += 1

        if is_successful:
            self.stats["successful_dialogs"] += 1

        if self.stats["total_dialogs"] > 0:
            self.stats["conversion"] = (self.stats["successful_dialogs"] / self.stats["total_dialogs"]) * 100
        else:
            self.stats["conversion"] = 0.0

        self.stats["GPT-4o-MINI-total_tokens_in"] += input_tokens_mini
        self.stats["GPT-4o-MINI-total_tokens_out"] += output_tokens_mini

        self.stats["GPT-4o-total_tokens_in"] += input_tokens_o
        self.stats["GPT-4o-total_tokens_out"] += output_tokens_o

        cost_in_mini, cost_out_mini = self.calculate_cost(input_tokens_mini, output_tokens_mini, model="gpt-4o-mini")
        self.stats["GPT-4o-MINI-total_cost_in"] += cost_in_mini
        self.stats["GPT-4o-MINI-total_cost_out"] += cost_out_mini

        cost_in_o, cost_out_o = self.calculate_cost(input_tokens_o, output_tokens_o, model="gpt-4o")
        self.stats["GPT-4o-total_cost_in"] += cost_in_o
        self.stats["GPT-4o-total_cost_out"] += cost_out_o

        self.save_statistics()