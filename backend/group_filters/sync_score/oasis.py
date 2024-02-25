def oasis(
    word_user1: str,
    smile_user1: list[float],
    word_bins_user2: list[list[str]],
    smile_user2: list[float],
    window_size: int,
    n_bins: int,
    energy_threshold: float = 0.1,
) -> float:
    # Initialize the synchrony score as 0
    sync_score = 0

    # Calculate the signal energy for AU data of both user
    energy_user1 = calc_signal_energy(smile_user1, window_size)
    energy_user2 = calc_signal_energy(smile_user2, window_size)
    min_energy = min(energy_user1, energy_user2)

    # Continue only if the minimum signal energy > threshold
    if min_energy > energy_threshold:
        for j, compare_bin in enumerate(word_bins_user2):
            # Calculate offset coefficient
            offset_coefficient = 1 - (j / window_size)

            if sync_score >= offset_coefficient:
                return sync_score

            # Calculate shape similarity
            compare_word = compare_bin[0]
            shape_similarity = 1 - calc_euclidean_word_distance(
                word_user1, compare_word, n_bins
            )

            # Calculate value similarity
            energy_user2_with_offset = calc_signal_energy(smile_user2, window_size, j)
            value_similarity = 1 - (
                abs(energy_user1 - energy_user2_with_offset) / window_size
            )

            # Update synchrony score
            sync_score = max(
                sync_score,
                offset_coefficient * shape_similarity * value_similarity,
            )

    return sync_score


def calc_signal_energy(signal, window_size, offset=0):
    sum = 0
    for i in range(window_size):
        if offset + i < len(signal):
            sum += abs(signal[offset + i])
    return sum / window_size


def calc_euclidean_word_distance(word, compare_word, num_bins):
    distance = 0
    for c1, c2 in zip(word, compare_word):
        char_distance = abs(ord(c1) - ord(c2)) / (num_bins - 1)
        distance += char_distance
    return distance / len(word)
