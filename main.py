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
            "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "messages": [
                {"role": "system", "content": "Instructions: Extract script without XML. Format to proper punctuations and newlines, without 'um' 'ah'. In your response, provide only the final output without presenting it."},
                {"role": "user", "content": subtitle_content}
            ]
        }

        # Send request to the API
        response = requests.post(url, headers=headers, data=json.dumps(data))
        msg = response.json()['choices'][0]['message']['content']
        print(msg)
        send(msg)
        return [], info



def fetch():
    """todo"""
    ydl_opts = {
        'writeautomaticsub' : True,
        'skip_download': True,
        'subtitlesformat': 'ttml',
        'outtmpl': '%(id)s',
        #'playlistend': 1,
        #'listsubtitles': True,
        #'force_write_download_archive': True,
        #'download_archive': 'downloaded.txt',
        #'break_on_existing': True,
        'daterange': yt_dlp.utils.DateRange('now-4days', 'now'), # New stateless mode.
        'break_on_reject': True,
    }
    with  yt_dlp.YoutubeDL(ydl_opts) as ydl:
      ydl.add_post_processor(MyCustomPP(), when='after_video')
      
      try:
          ydl.download([ENV_URL])
      except yt_dlp.utils.RejectedVideoReached:
          print("A video did not match the filter. Gracefully handled.")

def send(body, title='\n'):
# Create an Apprise instance
    apobj = apprise.Apprise()

    # Add the Discord webhook URL to the Apprise instance
    apobj.add(ENV_APP)

    # Send a notification
    apobj.notify(body=body, title=title)
    print('sent!')





if __name__ == "__main__":
    #
    fetch()

