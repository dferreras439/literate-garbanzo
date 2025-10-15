import yt_dlp, apprise
import requests
import json
import os


ENV_APP = os.getenv('ENV_APP')
ENV_OAI = os.getenv('ENV_OAI')
ENV_MEP = ''
ENV_SYS = ''
ENV_URL = os.getenv('ENV_URL')

class MyCustomPP(yt_dlp.postprocessor.PostProcessor):
    '''
    Hook for doing logic after a video.
    '''
    def run(self, info):
        # Construct the subtitle filename
        subtitle_filename = f"{info['id']}.en.ttml"

        # Read subtitle content from the file
        with open(subtitle_filename, 'r', encoding='utf-8') as file:
            subtitle_content = file.read()

        print(subtitle_filename)

        # API Request details
        url = ENV_OAI
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "microsoft/phi-4",
            "messages": [
                {"role": "system", "content": "Instructions: Extract script without XML. Format to proper punctuations and newlines, without 'um' 'ah'. Next, respond without a presentation or introduction."},
                {"role": "user", "content": subtitle_content}
            ]
        }

        # Send request to the API
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(response.json()) # If choices doesn't exist
        msg = response.json()['choices'][0]['message']['content']
        # print(msg)
        # print(info.get('id', 'unknown id'), info.get('title', 'No Title'), info.get('upload_date', 'Unknown Date'))
        title = "*"+"".join(info.get('title', 'No Title').split('#'))+"*"
        send(msg, title)
        return [], info

from datetime import datetime, timedelta

def uploaded_within_last_hour(info_dict):
    """ Custom filter to allow only videos uploaded within the last hour """
    upload_date_str = info_dict.get('upload_date')  # Format: YYYYMMDD
    upload_time_str = info_dict.get('timestamp')  # UNIX timestamp

    if upload_time_str:
        # Convert timestamp to datetime
        upload_time = datetime.utcfromtimestamp(upload_time_str)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        if upload_time >= one_hour_ago:
            return None  # Video is within the last hour, allow download
        else:
            return f"Skipped: Uploaded at {upload_time}, more than an hour ago"

    if upload_date_str:
        # Fallback: Handle upload_date (only contains year, month, day)
        upload_date = datetime.strptime(upload_date_str, "%Y%m%d")
        one_hour_ago = datetime.utcnow().date() - timedelta(hours=1)
        
        if upload_date >= one_hour_ago.date():
            return None  # Allow same-day videos (less accurate)
        else:
            return f"Skipped: Uploaded on {upload_date}, more than an hour ago"

    return "Skipped: No upload date available"


def fetch():
    """todo"""
    ydl_opts = {
        'writeautomaticsub' : True,
        'skip_download': True,
        'subtitlesformat': 'ttml',
        'outtmpl': '%(id)s',
        'playlist_items': '1-10',  # Download first 10 videos from the playlist
        #'listsubtitles': True,
        #'force_write_download_archive': True,
        #'download_archive': 'downloaded.txt',
        #'break_on_existing': True,
        #'daterange': yt_dlp.utils.DateRange('now-1day', 'now'), # New stateless mode. But no granularity.
        'break_on_reject': True,
        'match_filter': uploaded_within_last_hour,
    }
    with  yt_dlp.YoutubeDL(ydl_opts) as ydl:
      ydl.add_post_processor(MyCustomPP(), when='after_video')

      try:
          ydl.download([ENV_URL])
      except yt_dlp.utils.RejectedVideoReached:
          print("A video did not match the filter. Gracefully handled.")

def send(body, title=''):
    """
    Sends long messages to Discord via Apprise, respecting Discord's 2000-char limit,
    never cutting mid-word, and ensuring ordered sequential delivery.
    """
    import re
    import time

    # Discord message max (Apprise adds small metadata, so we stay below the edge)
    MAX_LEN = 1950  

    apobj = apprise.Apprise()
    apobj.add(ENV_APP)

    # Combine title + body for accurate length accounting on first message
    title_len = len(title)
    available = MAX_LEN - title_len - 10  # -10 buffer for formatting/safety

    # Clean up newlines / spaces
    body = re.sub(r'\s+', ' ', body.strip())

    chunks = []
    current = []

    for word in body.split():
        if len(' '.join(current + [word])) <= available:
            current.append(word)
        else:
            chunks.append(' '.join(current))
            current = [word]
            # After the first chunk, full 1950 available
            available = MAX_LEN
    if current:
        chunks.append(' '.join(current))

    # Send in sequence (guaranteed order)
    if not chunks:
        return

    # Send first message with title
    apobj.notify(title=title, body=chunks[0])
    print(f"Sent chunk 1/{len(chunks)} ({len(chunks[0])} chars)")

    # Send subsequent messages in order
    for i, chunk in enumerate(chunks[1:], start=2):
        # small delay ensures strict ordering (Discord webhooks are async)
        time.sleep(1)
        apobj.notify(title='', body=chunk)
        print(f"Sent chunk {i}/{len(chunks)} ({len(chunk)} chars)")


fetch()
