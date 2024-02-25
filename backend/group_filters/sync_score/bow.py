from pyts.bag_of_words import BagOfWords
import numpy as np
import logging


class BoW:
    _bow: BagOfWords

    def __init__(self, window_size: int, word_size: int, n_bins: int, strategy: str):
        self._bow = BagOfWords(
            window_size=window_size,
            word_size=word_size,
            n_bins=n_bins,
            window_step=1,
            numerosity_reduction=False,
            strategy=strategy,
        )

        logging.getLogger("numba").setLevel(logging.WARNING)

    def apply_bow(self, data: np.ndarray) -> np.ndarray:
        # Transform data into BoW
        bow_list = self._bow.transform([data])

        # Split words into buckets
        bow_list = bow_list[0].split(" ")
        words_in_buckets = self.split_words_into_buckets(bow_list)

        return words_in_buckets

    def apply_bow_for_2_participants(
        self, data1: np.ndarray, data2: np.ndarray
    ) -> tuple[np.ndarray]:
        # Append data
        data = np.append(data1, data2)

        # Transform data into BoW
        bow_list = self._bow.transform([data])

        # Separate data
        overlap = self._bow.window_size - self._bow.window_step
        seperation_idx = len(data1) // self._bow.window_step

        bow_list = bow_list[0].split(" ")
        bow_list1 = bow_list[0 : seperation_idx - overlap]
        bow_list2 = bow_list[seperation_idx:]

        # Split words into buckets
        words_in_buckets1 = self.split_words_into_buckets(bow_list1)
        words_in_buckets2 = self.split_words_into_buckets(bow_list2)

        return (words_in_buckets1, words_in_buckets2)

    def split_words_into_buckets(self, bow_list: list[str]) -> list[list[str]]:
        n_buckets = self._bow.window_size // self._bow.window_step

        buckets = [[] for _ in range(n_buckets)]
        for i, word in enumerate(bow_list):
            bin = buckets.pop(i % n_buckets)
            bin.append(word)
            buckets.insert(i % n_buckets, bin)
        return buckets
