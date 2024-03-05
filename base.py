import MetaTrader5 as mt5
from telethon import TelegramClient, events
import configparser
import time

# Initializing Configuration

terminal_path = 'C:/Program Files/MetaTrader 5 IC Markets (SC)/terminal64.exe'

mt_account = 51647342
mt_pass = 'QJ&@5$qsE3Iht!'
mt_server = 'ICMarketsSC-Demo'

logged_trades = []
double_logged_trades = []

ticket = 0
time = 1
lot_sizerr = 9
entry_price = 10
stop_loss = 11
take_profit = 12
current_profit = 17
current_symbol = 16

position_symbol = None


def check_closed_positions():
    global logged_trades, double_logged_trades
    
    for trade_id, sl, tp in double_logged_trades:
        trade = mt5.positions_get(ticket=trade_id)

        if not trade:
            print(f"Position closed: {trade_id}")
            position_symbol = mt5.history_orders_get(ticket=trade_id)
                        
            text = f"🚨Position Closed🚨\n🚨EXIT TRADE🚨\n \nID: {trade_id}\nSymbol: {position_symbol[0][21]}\nClosing Price: {position_symbol[0][19]}"
            print(text)
            # Remove the closed position from the double_logged_trades list
            double_logged_trades = [(t_id, t_sl, t_tp) for t_id, t_sl, t_tp in double_logged_trades if t_id != trade_id]

            #close relevant trade


def retryable_initialize(max_retries, delay_seconds, terminal_path, a, b, c):
    for attempt in range(1, max_retries + 1):
        if mt5.initialize(terminal_path):
            authorized = mt5.login(login=a, password=b, server=c)
            #time.sleep(delay_seconds)
            if not authorized:
                
                print("Failed to connect at account #{}, error code: {}".format(mt_account, mt5.last_error()))
            return True  # If successful, exit the loop and return True
        else:
            print(f"Attempt {attempt} failed to initialize, error code: {mt5.last_error()}")
            #ime.sleep(delay_seconds)  # Wait for the specified time before the next attempt

    raise MaxRetriesExceeded(f"Max retries ({max_retries}) reached. Initialization failed.")




# Main
if __name__ == '__main__':
    try:
        print("Bot Started...")

        while True:
            retryable_initialize(3, 5, terminal_path, mt_account, mt_pass, mt_server)
            # Monitor MT5 events (checking for new trades every 5 seconds)
            trades = mt5.positions_get()

            for trade in trades:
                trade_id = trade[0]
                if trade_id not in logged_trades:
                    if trade[5] == 1:
                        print('New trade')
                        logged_trades.append(trade_id)
                        double_logged_trades.append((trade_id, trade[stop_loss], trade[take_profit]))
                        #text = f"🚨NEW SIGNAL🚨\n \nID: {trade_id}\nTYPE: *SELL*\nSYMBOL: {trade[current_symbol]}\nENTRY PRICE: {trade[entry_price]}\nTAKE PROFIT: {trade[take_profit]}\nSTOP LOSS: {trade[stop_loss]}"
                        print(trade)
                        #open sell trade on other

                        

                    elif trade[5] == 0:
                        print('New trade')
                        logged_trades.append(trade_id)
                        double_logged_trades.append((trade_id, trade[stop_loss], trade[take_profit]))
                        #text = f"🚨NEW SIGNAL🚨\n \nID: {trade_id}\nTYPE: *BUY*\nSYMBOL: {trade[current_symbol]}\nENTRY PRICE: {trade[entry_price]}\nTAKE PROFIT: {trade[take_profit]}\nSTOP LOSS: {trade[stop_loss]}"
                        
                        print(trade)
                        #open buy

                else:
                    # Check if the trade stop loss or take profit has changed
                    for i, double_trade in enumerate(double_logged_trades):
                        if trade_id == double_trade[0]:
                            if trade[stop_loss] != double_trade[1] or trade[take_profit] != double_trade[2]:
                                # SL or TP has changed
                                text = f"🚨TRADE UPDATE🚨\n \nID: {trade_id}\nSL: {trade[stop_loss]}\nTP: {trade[take_profit]}"
                                print(text)
                                # Update SL and TP in the double_logged_trades list
                                double_logged_trades[i] = (trade_id, trade[stop_loss], trade[take_profit]) 

                                #update trade


            #time.sleep(5)  # Adjust the sleep time as needed

            check_closed_positions()

    except Exception as error:
        print('Cause: {}'.format(error))
