WEBHOOK_URL = os.environ['WEBHOOK_URL']

def send(body, title):
# Create an Apprise instance
    apobj = apprise.Apprise()

    # Add the Discord webhook URL to the Apprise instance
    apobj.add('WEBHOOK_URL')

    # Send a notification
    apobj.notify(body=body, title=title)
    print('sent!')