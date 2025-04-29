import aiohttp
import asyncio
import os
import re
from fuzzywuzzy import fuzz
import json
from datetime import datetime, timedelta

async def scrape_radio_stations(country):
    """
    Scrape radio stations for a given country from Radio Garden's API with dynamic matching.
    Args:
        country (str): Country code (e.g., 'US', 'UK') or name (e.g., 'South Africa').
    Returns:
        list: List of (name, url, country) tuples for radio stations.
    """

    cache_dir = os.path.join("exports", "cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{country.replace(' ', '_').lower()}.json")

    def log_message(message):
        """Append message to exports/scraper_log.txt with timestamp."""
        log_file = os.path.join("exports", "scraper_log.txt")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

    # Check cache
    if os.path.exists(cache_file):
        cache_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - cache_mtime < timedelta(hours=24):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                log_message(f"Using cached data for {country}")
                return cached_data
            except Exception as e:
                log_message(f"Error reading cache for {country}: {e}")

    async def fetch_with_retry(session, url, retries=3, timeout=10):
        """Fetch URL with retries on failure."""
        for attempt in range(1, retries + 1):
            try:
                async with session.get(url, timeout=timeout) as response:
                    response.raise_for_status()
                    log_message(f"Success: {url} (Status: {response.status})")
                    return await response.json()
            except aiohttp.ClientError as e:
                log_message(f"Attempt {attempt}/{retries} failed for {url}: {e}")
                if attempt == retries:
                    log_message(f"Max retries reached for {url}")
                    return None
                await asyncio.sleep(2**attempt)  # Exponential backoff
        return None

    try:
        # Normalize country input
        country_input = (
            country.strip().upper() if len(country) <= 3 else country.strip().title()
        )
        normalized_input = country_input.replace(" ", "").lower()
        log_message(
            f"Scraping stations for: {country_input} (Normalized: {normalized_input})"
        )

        # Fetch places from Radio Garden API
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        places_url = "http://radio.garden/api/ara/content/places"
        places = []
        async with aiohttp.ClientSession(headers=headers) as session:
            places_data = await fetch_with_retry(session, places_url)
            if not places_data:
                log_message(f"Failed to fetch places from {places_url}")
                return []

            places = places_data.get("data", {}).get("list", [])
            log_message(
                f"Places API response: {len(places)} places, sample: {places[:2]}"
            )

            # Check for pagination (Radio Garden doesn't seem to use it, but verify)
            # If pagination exists, it might use query params like ?page=2
            page = 2
            while True:
                paginated_url = f"{places_url}?page={page}"
                paginated_data = await fetch_with_retry(session, paginated_url)
                if not paginated_data or not paginated_data.get("data", {}).get(
                    "list", []
                ):
                    log_message(f"No more pages at {paginated_url}")
                    break
                places.extend(paginated_data.get("data", {}).get("list", []))
                log_message(
                    f"Fetched page {page}: {len(paginated_data['data']['list'])} places"
                )
                page += 1

        if not places:
            log_message("No places found in API response")
            return []

        # Dynamic country matching
        country_matches = []
        seen_places = set()  # Avoid duplicate place IDs
        for place in places:
            place_id = place.get("id")
            if place_id in seen_places:
                continue
            seen_places.add(place_id)
            api_country = place.get("country", "").strip().title()
            api_country_code = place.get("countryCode", "").strip().upper()
            normalized_api_country = (
                api_country.replace(" ", "").lower() if api_country else ""
            )
            # Prioritize country code for short inputs
            code_score = (
                fuzz.ratio(normalized_input, api_country_code.lower())
                if api_country_code
                else 0
            )
            name_score = (
                fuzz.ratio(normalized_input, normalized_api_country)
                if api_country
                else 0
            )
            max_score = (
                code_score
                if len(country_input) <= 3 and code_score > 70
                else max(name_score, code_score)
            )
            if max_score > 70:
                country_matches.append((place, max_score, api_country))
                log_message(
                    f"Match for {country_input}: {api_country} (ID: {place_id}, Score: {max_score})"
                )

        if not country_matches:
            log_message(f"No country match found for: {country_input}")
            return []

        # Sort by match score and process top matches
        country_matches.sort(key=lambda x: x[1], reverse=True)
        stations = []
        async with aiohttp.ClientSession(headers=headers) as session:
            for place, score, place_country in country_matches[
                :5
            ]:  # Limit to top 5 matches
                place_id = place.get("id")
                log_message(
                    f"Processing place: {place_country} (ID: {place_id}, Score: {score})"
                )

                # Fetch channels for this place
                channels_url = (
                    f"http://radio.garden/api/ara/content/page/{place_id}/channels"
                )
                channels_data = await fetch_with_retry(session, channels_url)
                if not channels_data:
                    log_message(f"Failed to fetch channels for {place_country}")
                    continue

                content = (
                    channels_data.get("data", {})
                    .get("content", [{}])[0]
                    .get("items", [])
                )
                log_message(f"Channels for {place_country}: {len(content)} items")

                for channel in content:
                    station_name = channel.get("title", "Unknown Station")
                    station_id = channel.get("page", {}).get("id")
                    if station_id:
                        stream_url = f"http://radio.garden/api/ara/content/listen/{station_id}/channel.m3u"
                        async with session.head(
                            stream_url, timeout=5, allow_redirects=True
                        ) as stream_response:
                            if stream_response.status == 200:
                                stations.append(
                                    (station_name, stream_url, place_country)
                                )
                                log_message(
                                    f"Valid station: {station_name} ({stream_url})"
                                )
                            else:
                                log_message(
                                    f"Invalid stream URL: {stream_url} (Status: {stream_response.status})"
                                )
                await asyncio.sleep(1)  # Avoid rate limits

        log_message(f"Found {len(stations)} stations for {country_input}")

        # Save to cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(stations, f)
            log_message(f"Cached data saved for {country_input}")
        except Exception as e:
            log_message(f"Error saving cache for {country_input}: {e}")

        return stations[:10]  # Limit to 10 stations per country

    except Exception as e:
        log_message(f"Unexpected error scraping {country}: {e}")


def scan_api_calls(base_path, api_base_url):
    """
    Scan project files for Radio Garden API calls and save to exports/api_endpoints.txt.
    Args:
        base_path (str): Root directory to scan.
        api_base_url (str): Base URL of the API (e.g., 'http://radio.garden/api/').
    Returns:
        list: Sorted list of unique API endpoints found.
    """
    api_calls = set()
    pattern = re.compile(re.escape(api_base_url) + r'[^\'"\\s]+')

    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".json", ".txt", ".html")):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        for match in matches:
                            api_calls.add(match)
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")

    api_calls = sorted(api_calls)
    output_file = os.path.join(base_path, "exports", "api_endpoints.txt")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for call in api_calls:
            f.write(call + "\n")
    print(f"Found {len(api_calls)} API calls. Results saved to {output_file}")

    return api_calls
