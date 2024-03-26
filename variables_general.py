from datetime import datetime, timedelta
import pandas as pd
import MetaTrader5 as mt5


#IC Markets

mt_account1 = 51647342
mt_pass1 = 'QJ&@5$qsE3Iht!'
mt_server1 = 'ICMarketsSC-Demo'
terminal_path1 = 'C:/Program Files/MetaTrader 5 IC Markets (SC)/terminal64.exe'

slave_accounts = [[51648628, '!84qyzkOtMphsD', 'ICMarketsSC-Demo', 'C:/Program Files/MetaTrader 5 IC Markets (SC)/terminal64.exe', 1]]

###########################################################################

timestamp = 0
open = 1
high = 2
low = 3
close = 4
imbalance_poi_pos = []
imbalance_poi_neg = []

ticket = 0
#time = 1
lot_sizerr = 9
entry_price = 10
stop_loss = 11
take_profit = 12
current_profit = 17
current_symbol = 16


permitted_positions = []
maximum_trades = 6


rates = None

number_of_candles = 350
pipp = 0
is_buy = True
utc_from = datetime.now() + timedelta(hours=200) 

symbol_iteration = 1
class MaxRetriesExceeded(Exception):
    pass

def retryable_initialize(max_retries, delay_seconds, terminal_path, a, b, c):
    for attempt in range(1, max_retries + 1):
        if mt5.initialize(terminal_path):
            authorized = mt5.login(login=a, password=b, server=c)
            #time.sleep(delay_seconds)
            if not authorized:
                print("Failed to connect at account #{}, error code: {}".format(a, mt5.last_error()))
            return True  # If successful, exit the loop and return True
        else:
            print(f"Attempt {attempt} failed to initialize, account: {a}, error code: {mt5.last_error()}")
            #ime.sleep(delay_seconds)  # Wait for the specified time before the next attempt

    raise MaxRetriesExceeded(f"Max retries ({max_retries}) reached. Initialization failed.")

def reverse_type(type):
    if type == mt5.ORDER_TYPE_BUY:
        return mt5.ORDER_TYPE_SELL
    elif type == mt5.ORDER_TYPE_SELL:
        return mt5.ORDER_TYPE_BUY




opened_positions = []


SCRIPT_VERSION = 'V0.2.2'
SCRIPT_MAGIC = 202


class BidirectionalMap:
    def __init__(self):
        self.forward_map = {}
        self.reverse_map = {}

    def add_mapping(self, key1, key2):
        if key1 not in self.forward_map:
            self.forward_map[key1] = []
        self.forward_map[key1].append(key2)

        if key2 not in self.reverse_map:
            self.reverse_map[key2] = []
        self.reverse_map[key2].append(key1)

    def get_value_by_key1(self, key1):
        return self.forward_map.get(key1, [])

    def get_value_by_key2(self, key2):
        return self.reverse_map.get(key2, [])

class CurrencyPairMapping:
    def __init__(self):
        self.pair_mapping = {}

    def add_pair_mapping(self, broker_name, original_pair_name, broker_specific_pair_name):
        if broker_name not in self.pair_mapping:
            self.pair_mapping[broker_name] = {}
        self.pair_mapping[broker_name][original_pair_name] = broker_specific_pair_name

    def get_broker_specific_pair_name(self, broker_name, original_pair_name):
        broker_mapping = self.pair_mapping.get(broker_name, {})
        return broker_mapping.get(original_pair_name, original_pair_name)


def open_trade(symbol, lot_size=0.1, stop_loss=100, take_profit=100, deviation=20, b_s = None):
    global pipp, is_buy
    # Initialize MetaTrader 5
    is_buy = b_s
    print(f'IS IT A BUY?: {is_buy}')
    #try:
    #    if not retryable_initialize(3, 5, terminal_path2, mt_account2, mt_pass2, mt_server2):
    #        print("Initialization failed even after retries.")
    #        #send_notification('Script Stopped', 'Initialisation failed')
    #    else:
    #        print("Initialization successful!")
    #except MaxRetriesExceeded as e:
    #    print(e)
    # Check if the symbol is available in MarketWatch
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, cannot call order_check()")
        mt5.shutdown()
        return
    # Add the symbol if it is not visible
    if not symbol_info.visible:
        print(f"{symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"symbol_select({symbol}) failed, exit")
            mt5.shutdown()
            return
    # Prepare the trading request
    price = mt5.symbol_info_tick(symbol).ask if is_buy else mt5.symbol_info_tick(symbol).bid
    order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": (price - price) + stop_loss if is_buy else (price - price) + stop_loss,
        "tp": (price - price) + take_profit if is_buy else (price - price) + take_profit,
        "deviation": deviation,
        "magic": SCRIPT_MAGIC,
        "comment": SCRIPT_VERSION,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    # Send the trading request
    result = mt5.order_send(request)
    
    # Check the execution result
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"order_send failed, retcode={result.retcode}")
        result_dict = result._asdict()
        for field, value in result_dict.items():
            print(f"   {field}={value}")
            if field == "request":
                traderequest_dict = result_dict[field]._asdict()
                for tradereq_field, tradereq_value in traderequest_dict.items():
                    print(f"       traderequest: {tradereq_field}={tradereq_value}")
        print("shutdown() and quit")
        mt5.shutdown()
        return
    else:
        sl_increment = (((price - price) + take_profit if is_buy else (price - price) + take_profit) - price)/4
        opened_positions.append([result.order, price, price+sl_increment, price+(sl_increment*2), price+(sl_increment*3)])
    
    if is_buy:
        
        print("Opened BUY position with POSITION_TICKET={}".format(result.order))
        #send_notification("BUY Position opened", f"Pair: {symbol} Entry: {price} TP: {(price - price) + take_profit if is_buy else (price - price) + take_profit} SL: {(price - price) + stop_loss if is_buy else (price - price) + stop_loss}")
        pipp = result.price
        return (result.order)
    else: 
        
        print("Opened SELL position with POSITION_TICKET={}".format(result.order))
        #send_notification("SELL Position Opened", f"Pair: {symbol} Entry: {price} TP: {(price - price) + take_profit if is_buy else (price - price) + take_profit} SL: {(price - price) + stop_loss if is_buy else (price - price) + stop_loss}")
        pipp = result.price
        return (result.order)

def modify_trade(symbol = None, deviation=20, pos_ticket = None, new_stop = None, new_take = None):
    global pipp
    # Initialize MetaTrader 5
    
    # Check if the symbol is available in MarketWatch
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, cannot call order_check()")
        mt5.shutdown()
        return
    # Add the symbol if it is not visible
    if not symbol_info.visible:
        print(f"{symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"symbol_select({symbol}) failed, exit")
            mt5.shutdown()
            return
    # Prepare the trading request
    price = mt5.symbol_info_tick(symbol).ask if is_buy else mt5.symbol_info_tick(symbol).bid
    order_type = mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": pos_ticket,
        "symbol": symbol,
        "sl": new_stop,
        "tp": new_take,
        "deviation": deviation,
        "magic": SCRIPT_MAGIC,
    }
    # Send the trading request
    result = mt5.order_send(request)
    
    # Check the execution result
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"order_send failed, retcode={result.retcode}")
        result_dict = result._asdict()
        for field, value in result_dict.items():
            print(f"   {field}={value}")
            if field == "request":
                traderequest_dict = result_dict[field]._asdict()
                for tradereq_field, tradereq_value in traderequest_dict.items():
                    print(f"       traderequest: {tradereq_field}={tradereq_value}")
        print("shutdown() and quit")
        mt5.shutdown()
        return
    else:
        sl_increment = (((price - price) + take_profit if is_buy else (price - price) + take_profit) - price)/4
        opened_positions.append([result.order, price, price+sl_increment, price+(sl_increment*2), price+(sl_increment*3)])
    
    if is_buy:
        print("Opened BUY position with POSITION_TICKET={}".format(result.order))
        
        #send_notification("BUY Position opened", f"Pair: {symbol} Entry: {price} TP: {(price - price) + take_profit if is_buy else (price - price) + take_profit} SL: {(price - price) + stop_loss if is_buy else (price - price) + stop_loss}")
        
    else:
        print("Opened SELL position with POSITION_TICKET={}".format(result.order))
        
        #send_notification("SELL Position Opened", f"Pair: {symbol} Entry: {price} TP: {(price - price) + take_profit if is_buy else (price - price) + take_profit} SL: {(price - price) + stop_loss if is_buy else (price - price) + stop_loss}")
        

def close_trade(ticket, symbol, lot, typee):
    # Get position details
    price = mt5.symbol_info_tick(symbol).bid

    # Create close request
    close_request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": reverse_type(typee),
        "position": ticket,
        "price": price,
        "deviation": 20,
        "magic": 234000,
        "comment": "python script close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # Send close request
    close_result = mt5.order_send(close_request)

    # Check the execution result
    print("Close position #{}: sell {} {} lots at {} ".format(ticket, symbol, lot, price))

    if close_result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Order send failed, retcode={}".format(close_result.retcode))
        print("Result:", close_result)
    
pair_mapping_table = CurrencyPairMapping()

# Add pair mappings for different brokers
pair_mapping_table.add_pair_mapping('ICMarketsSC-MT5-2', 'EURUSD', 'EURUSD')
pair_mapping_table.add_pair_mapping('ICMarketsSC-MT5-2', 'XAUUSD', 'XAUUSD')
pair_mapping_table.add_pair_mapping('ICMarketsSC-MT5-2', 'US30', 'US30')
pair_mapping_table.add_pair_mapping('ICMarketsSC-MT5-2', 'BTCUSD', 'BTCUSD')

pair_mapping_table.add_pair_mapping('ICMarketsSC-Demo', 'EURUSD', 'EURUSD')
pair_mapping_table.add_pair_mapping('ICMarketsSC-Demo', 'XAUUSD', 'XAUUSD')
pair_mapping_table.add_pair_mapping('ICMarketsSC-Demo', 'US30', 'US30')
pair_mapping_table.add_pair_mapping('ICMarketsSC-Demo', 'BTCUSD', 'BTCUSD')

pair_mapping_table.add_pair_mapping('VantageInternational-Live', 'EURUSD', 'EURUSD')
pair_mapping_table.add_pair_mapping('VantageInternational-Live', 'XAUUSD', 'XAUUSD+')
pair_mapping_table.add_pair_mapping('VantageInternational-Live', 'US30', 'DJ30')
pair_mapping_table.add_pair_mapping('VantageInternational-Live', 'BTCUSD', 'BTCUSD')
