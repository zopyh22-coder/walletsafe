# WalletSafe

A Streamlit app that finds the cheapest nearby fuel stations using the live CSV provided at:
`https://docs.google.com/spreadsheets/d/e/2PACX-1vRLv_PUqHNCedwZhQIU5YtgH78T3uGxpd3v6CY2k368WP4gxDPFELdoplO5-ujpzSz53dJVkZ2dQbeZ/pub?gid=0&single=true&output=csv`

## Running the app
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start Streamlit:
   ```bash
   streamlit run app.py
   ```
3. Open the displayed local URL in your browser. The app automatically loads the latest station data; no manual copy/paste is required.

## Notes
- The data is cached for one hour to reduce requests.
- If loading fails, the app shows an error banner instead of breaking.
