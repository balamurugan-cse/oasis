# Oasis Chat

Browser-based real-time chat built with Python and a lightweight threaded HTTP server.

## Website

- `webapp.py` runs the website and API.
- `web/index.html`, `web/styles.css`, and `web/app.js` provide the interface.

## Run It

1. Start the website server:

   ```bash
   python webapp.py
   ```

2. Open the printed local URL in your browser.

3. Open a second tab or window and send messages to see the room update live.

## Optional Legacy Client

The original terminal chat files are still available if you want the socket-based version:

```bash
python server.py
python client.py
```