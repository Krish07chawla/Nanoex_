# User manual

## Before you start
- Look at the grey bar under the menu. It tells you if prices are real (Yahoo, delayed about 15 minutes) or simulated (DEMO), and whether the market is open.
- Everything uses **virtual money**.

## Everyone
1. Open the website and click **Create an account**. Choose **Student** or **Trader**.
2. Log in with your email and password.

## Student

**Get money.** Your admin sends you virtual money. Check **Wallet** to see it. Until then the dashboard says you have none.

**Trade.** Open **Market**, click a stock, then use the form on the right.
- *Market*: buys or sells now at the live price.
- *Limit*: you choose a price. A buy waits until the price falls to it; a sell waits until the price rises to it.
- *Stop-loss* (selling only): sells if the price falls to the trigger price, to limit your loss.
- A small brokerage (0.03%, at most ₹20) is added to every trade.

**Watch.** Click the ☆ next to a stock to add it to your watchlist. Use **Price alert** to be told when a price goes above or below a number; a message pops up on screen.

**Check your results.** **Portfolio** shows what you own and your profit or loss. **Orders** shows waiting orders (you can change or cancel them) and your history (you can download it as CSV). **Leaderboard** ranks students by percentage return.

**Join a class.** Open **Classes**, type the 6-letter code from your trader and click Join. Open the class to see the live chart and the trader's notes. Ask questions in the Questions box. Write your own notes in **My private notes**. When the class has ended, click **Replay** and drag the slider to go through it.

**AI Advisor.** Click **Get trade ideas**. It reads your trading history and the market and suggests trades. The label tells you if Grok or the simple backup made them. Click **Try this idea** to fill the order form, then check it and press Buy or Sell yourself. These are learning ideas, not financial advice.

## Trader
1. Open **My Classes**. Type a title, tick up to 6 stocks, click **Create class**.
2. Give the 6-letter **join code** to your students.
3. Click **Open**, then **Start class**.
4. Choose a type (Note, Buy idea, Sell idea) and a stock, write your explanation and click **Post to class**. Students see it at once with the price at that moment.
5. Answer student questions in the Questions box.
6. Click **End class** when you finish. Students can replay it afterwards.

## Admin
- **Users**: see every student with cash, total value and profit/loss.
- **Send virtual money**: choose Send or Take back, type an amount and a note, tick students in the table (or tick *All students*) and click **Apply**.
- **Open** on a student shows their holdings, orders and wallet ledger.
- **Disable / Enable** blocks or allows an account.
- **Audit log** lists every money move and account change.
- The first admin account comes from `ADMIN_EMAIL` and `ADMIN_PASSWORD` in the `.env` file.

## If something looks wrong
- *"DEMO feed"* in the grey bar: Yahoo could not be reached, so prices are simulated. Check your internet; the app retries every 15 seconds.
- *Prices do not move*: the market is closed (Yahoo shows the last price).
- *AI says rule-based*: no Grok key is set, or Grok returned an error. The message next to the label says which.
