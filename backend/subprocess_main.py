import asyncio
import json
from argparse import ArgumentParser
import sys
from typing import Tuple
from aiortc import RTCSessionDescription

from custom_types.filters import FilterDict
from custom_types.connection import (
    is_valid_rtc_session_description_dict,
    RTCSessionDescriptionDict,
)

from modules.connection_runner import ConnectionRunner


def parse_args() -> Tuple[
    RTCSessionDescription, str, list[FilterDict], list[FilterDict]
]:
    """Parse command line arguments.

    Raises
    ------
    ValueError
        If the offer is invalid
    """
    parser = ArgumentParser()
    parser.add_argument("-o", "--offer", dest="offer", required=True)
    parser.add_argument(
        "-l", "--log_name_suffix", dest="log_name_suffix", required=True
    )
    parser.add_argument(
        "--audio-filters", dest="audio_filters", required=False, default=[]
    )
    parser.add_argument(
        "--video-filters", dest="video_filters", required=False, default=[]
    )
    args = parser.parse_args()

    # Check and parse offer
    try:
        offer_obj = json.loads(args.offer)
        audio_filters = json.loads(args.audio_filters)
        video_filters = json.loads(args.video_filters)
    except (json.JSONDecodeError, TypeError) as e:
        print(
            "Failed to parse command line arguments received in command line arguments:"
            f" {e}",
            file=sys.stderr,
        )
        raise e

    if not is_valid_rtc_session_description_dict(offer_obj):
        print("Offer parsed from command line arguments is invalid.", file=sys.stderr)
        raise ValueError("Invalid offer")

    offer = RTCSessionDescription(offer_obj["sdp"], offer_obj["type"])

    return (offer, args.log_name_suffix, audio_filters, video_filters)


async def main() -> None:
    offer, log_name_suffix, audio_filters, video_filters = parse_args()

    runner = ConnectionRunner()
    await runner.run(offer, log_name_suffix, audio_filters, video_filters)


if __name__ == "__main__":
    asyncio.run(main())
