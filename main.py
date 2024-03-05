import MetaTrader5 as mt5
import configparser
import time
#from entry_func import *
from variables_general import *


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

inc1 = 0
inc2 = 0
inc3 = 0

full_trade_log = BidirectionalMap()

def check_closed_positions():
    global logged_trades, double_logged_trades
    
    for trade_id, sl, tp in double_logged_trades:
        retryable_initialize(3, 5, terminal_path1, mt_account1, mt_pass1, mt_server1)
        trade = mt5.positions_get(ticket=trade_id)

        if not trade:
            print(f"Position closed: {trade_id}")
            position_symbol = mt5.history_orders_get(ticket=trade_id)
                        
            text = f"🚨Position Closed🚨\n🚨EXIT TRADE🚨\n \nID: {trade_id}\nSymbol: {position_symbol[0][21]}\nClosing Price: {position_symbol[0][19]}"
            #client.loop.run_until_complete(client.send_message(chat_id, text))

            # Update your logic for max_daily_loss and total_position_risk if needed
            print(text)
            # Remove the closed position from the double_logged_trades list
            double_logged_trades = [(t_id, t_sl, t_tp) for t_id, t_sl, t_tp in double_logged_trades if t_id != trade_id]

            tic = full_trade_log.get_value_by_key1(trade_id)
            #close relevant trade
            
            retryable_initialize(3, 5, terminal_path2, mt_account2, mt_pass2, mt_server2)
            position_symboll = mt5.history_orders_get(ticket=tic[0])
            print(tic[0])
            print(tic[1])
            print(position_symboll[0][14])
            print(position_symboll[0][6])
            close_trade(tic[0], tic[1], position_symboll[0][14], position_symboll[0][6])
            print(1)






# Main
if __name__ == '__main__':
    try:
        print("Bot Started...")

        while True:
            retryable_initialize(3, 5, terminal_path1, mt_account1, mt_pass1, mt_server1)
            # Monitor MT5 events (checking for new trades every 5 seconds)
            trades = mt5.positions_get()
            is_buy = None

            for trade in trades:
                trade_id = trade[0]
                if trade_id not in logged_trades:
                    if trade[5] == 1:
                        print('New trade')
                        logged_trades.append(trade_id)
                        double_logged_trades.append((trade_id, trade[stop_loss], trade[take_profit]))
                        text = f"🚨NEW SIGNAL🚨\n \nID: {trade_id}\nTYPE: *SELL*\nSYMBOL: {trade[current_symbol]}\nENTRY PRICE: {trade[entry_price]}\nTAKE PROFIT: {trade[take_profit]}\nSTOP LOSS: {trade[stop_loss]}"
                        #client.loop.run_until_complete(client.send_message(chat_id, text))
                        print(text)
                        #open sell trade on other

                        is_buy = False
                        retryable_initialize(3, 5, terminal_path2, mt_account2, mt_pass2, mt_server2)
                        new_order = open_trade(symbol=trade[current_symbol], lot_size=trade[lot_sizerr], stop_loss = trade[stop_loss], take_profit = trade[take_profit], b_s = False)
                        full_trade_log.add_mapping(trade_id, (new_order, trade[current_symbol]))
                        

                    elif trade[5] == 0:
                        print('New trade')
                        logged_trades.append(trade_id)
                        double_logged_trades.append((trade_id, trade[stop_loss], trade[take_profit]))
                        text = f"🚨NEW SIGNAL🚨\n \nID: {trade_id}\nTYPE: *BUY*\nSYMBOL: {trade[current_symbol]}\nENTRY PRICE: {trade[entry_price]}\nTAKE PROFIT: {trade[take_profit]}\nSTOP LOSS: {trade[stop_loss]}"
                        #client.loop.run_until_complete(client.send_message(chat_id, text))

                        print(text)
                        #open buy
                        is_buy = True
                        retryable_initialize(3, 5, terminal_path2, mt_account2, mt_pass2, mt_server2)
                        new_order = open_trade(symbol=trade[current_symbol], lot_size=trade[lot_sizerr], stop_loss = trade[stop_loss], take_profit = trade[take_profit], b_s = True)
                        full_trade_log.add_mapping(trade_id, (new_order, trade[current_symbol]))
                else:
                    # Check if the trade stop loss or take profit has changed
                    for i, double_trade in enumerate(double_logged_trades):
                        if trade_id == double_trade[0]:
                            if trade[stop_loss] != double_trade[1] or trade[take_profit] != double_trade[2]:
                                # SL or TP has changed
                                text = f"🚨TRADE UPDATE🚨\n \nID: {trade_id}\nSL: {trade[stop_loss]}\nTP: {trade[take_profit]}"
                                #client.loop.run_until_complete(client.send_message(chat_id, text))
                                print(text)
                                # Update SL and TP in the double_logged_trades list
                                double_logged_trades[i] = (trade_id, trade[stop_loss], trade[take_profit]) 
                                tic = full_trade_log.get_value_by_key1(trade_id)
                                print(tic[0])
                                print(tic[1])
                                #update trade
                                retryable_initialize(3, 5, terminal_path2, mt_account2, mt_pass2, mt_server2)        
                                modify_trade(symbol = tic[1], pos_ticket = tic[0], new_stop = trade[11], new_take = trade[12])

            #time.sleep(5)  # Adjust the sleep time as needed

            check_closed_positions()

    except Exception as error:
        print('Cause: {}'.format(error))
        text = 'boom test'
        #client.loop.run_until_complete(client.send_message(chat_id, text))
