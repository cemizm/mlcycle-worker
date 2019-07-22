import app

import time

from urllib.error import URLError, HTTPError

while True:
    try:
        app.run()
    except HTTPError as e:
        print(e)
        time.sleep(20)
    except URLError as e:
        print(e)
        time.sleep(60)
    except Exception as e:
        print(e)
        time.sleep(5)