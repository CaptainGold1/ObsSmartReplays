#  OBS Smart Replays is an OBS script that allows more flexible replay buffer management:
#  set the clip name depending on the current window, set the file name format, etc.
#  Copyright (C) 2026 CaptainGold1
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
from typing import Any

from .tech import _print

import os
import regex as re
import pathlib
import urllib
import requests


def sanitize_filename(string: str) -> str:
    # Remove characters that aren't alphanumeric, spaces, dots, underscores, or hyphens
    filename = re.sub(r'[^\w\s.-]', '', string)
    # Replace spaces with underscores and remove leading/trailing whitespace
    return filename.strip().replace(' ', '_')


def get_current_roblox_game_name() -> str | None:
    current_universe_id = get_current_roblox_universe_id()
    if not current_universe_id:
        return None

    _print(f"Determining game name for universe id {current_universe_id}.")

    universe_api_endpoint = "https://games.roblox.com/v1/games"
    params = {"universeIds": current_universe_id}

    try:
        response = requests.get(universe_api_endpoint, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()["data"]
        if data and len(data) > 0:
            _print(data)
            game_info = data[0]
            _print(f"Found game name {game_info["name"]}.")
            return sanitize_filename(game_info["name"])
        else:
            _print("Failed to get game information from Roblox API.")
            return None
    except Exception as e:
        _print(f"Error while getting game name from Roblox API: {e}.")
        return None


def get_current_roblox_universe_id() -> str | None:
    roblox_logs_dir = pathlib.Path(os.path.expandvars("%LOCALAPPDATA%/Roblox/logs"))

    roblox_logs = list(roblox_logs_dir.glob("*_Player_*.log"))
    if len(roblox_logs) == 0:
        return None

    latest_log = max(roblox_logs, key=lambda x: x.stat().st_mtime)

    try:
        logtext = latest_log.read_text(encoding="utf-8", errors="ignore")

        universe_id_pattern = re.compile(r'(?r)universeid:(\d+)') # Find the last universe id in the file
        quit_pattern = re.compile(r'(?r)leaveUGCGameInternal') # Find the last time the player quit a place

        latest_universe_id = universe_id_pattern.search(logtext)
        latest_quit = quit_pattern.search(logtext)

        if (latest_universe_id and
            # The last quit was before they joined this place, or they haven't quit before
            (not latest_quit or latest_quit.start(0) < latest_universe_id.start(0))
        ):
            universe_id = latest_universe_id.group(1)
            _print(f"Found player playing universe id {universe_id}.")
            return universe_id
        else:
            return None
    except Exception as e:
        _print(f"Error while reading Roblox log {latest_log.name}: {e}")
        return None
