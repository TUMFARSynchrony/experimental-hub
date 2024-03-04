from transformers import pipeline
from typing import Any

from chat_filters.chat_filter import ChatFilter


class SentimentAnalysisFilter(ChatFilter):
    sentiment_classifier: Any

    def __init__(self):
        self.sentiment_classifier = pipeline(
            "text-classification", model="cardiffnlp/twitter-roberta-base-sentiment"
        )

    @staticmethod
    def name(self) -> str:
        return "SENTIMENT ANALYSIS"

    @staticmethod
    def filter_type(self) -> str:
        return "ANALYSIS"

    def apply_filter(self, chat_message: str):
        sentiment_score = self.sentiment_classifier(chat_message)[0]
        if sentiment_score["label"] == "LABEL_0":
            sentiment_score["label"] = "negative"
        elif sentiment_score["label"] == "LABEL_2":
            sentiment_score["label"] = "positive"
        else:
            sentiment_score["label"] = "neutral"
        return sentiment_score
