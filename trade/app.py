from flask import Flask, render_template
from flask_socketio import SocketIO
import asyncio
from threading import Thread
import websockets
import pandas as pd
import pandas_ta as ta
import json
from flask_cors import CORS
import pymongo
import traceback

# Mongodb_btc setup
ip = '185.92.220.43'
client = pymongo.MongoClient("mongodb://user:userpassword@185.92.220.43:27017/")
db_btc = client['BTC_indicators']
db_eth = client['ETH_indicators']

btcadx_indicators = db_btc['ADX']
btcsma_indicators = db_btc['SMA']
btccmf_indicators = db_btc['CMF']
btcrsi_indicators = db_btc['RSI']
btcmfi_indicators = db_btc['MFI']

ethadx_indicators = db_eth['ETH_ADX']
ethsma_indicators = db_eth['ETH_SMA']
ethcmf_indicators = db_eth['ETH_CMF']
ethrsi_indicators = db_eth['ETH_RSI']
ethmfi_indicators = db_eth['ETH_MFI']

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

btc = pd.DataFrame(columns=['Timestamp', 'open', 'high', 'low', 'close', 'volume'])
eth = pd.DataFrame(columns=['Timestamp', 'open', 'high', 'low', 'close', 'volume'])

async def calculate_indicators():
    MAX_RETRIES = 30
    INITIAL_DELAY = 1
    retries = 0
    delay = INITIAL_DELAY

    while retries <= MAX_RETRIES:
        try:
            async with websockets.connect('wss://stream.binance.com:9443/ws/btcusdt@kline_1s') as btc_ws, \
                    websockets.connect('wss://stream.binance.com:9443/ws/ethusdt@kline_1s') as eth_ws:
                while True:
                    response_btc = await btc_ws.recv()
                    response_eth = await eth_ws.recv()

                    json_data_btc = json.loads(response_btc)
                    json_data_eth = json.loads(response_eth)

                    # BTC calculations
                    timestamp_btc = pd.to_datetime(json_data_btc['k']['t'], unit='ms')
                    timestamp_btc = timestamp_btc.strftime("%Y-%m-%d %H:%M:%S")
                    open_price_btc = float(json_data_btc['k']['o'])
                    high_btc = float(json_data_btc['k']['h'])
                    low_btc = float(json_data_btc['k']['l'])
                    close_btc = float(json_data_btc['k']['c'])
                    volume_btc = float(json_data_btc['k']['v'])

                    new_row_btc = {
                        'Timestamp': timestamp_btc,
                        'open': open_price_btc,
                        'high': high_btc,
                        'low': low_btc,
                        'close': close_btc,
                        'volume': volume_btc
                    }
                    btc.loc[len(btc)] = new_row_btc

                    if len(btc) >= 50:
                        # BTC indicators calculations
                        df_adx_btc = ta.adx(btc['high'], btc['low'], btc['close']).tail(14)
                        df_cmf_btc = ta.cmf(btc['high'], btc['low'], btc['close'], btc['volume']).tail(20)
                        df_mfi_btc = ta.mfi(btc['high'], btc['low'], btc['close'], btc['volume']).tail(14)
                        df_rsi_btc = ta.rsi(btc['close']).tail(14)
                        df_sma_btc = ta.sma(btc['close']).tail(10)
                        df_cdl_inside_btc = ta.cdl_inside(btc['open'], btc['high'], btc['low'], btc['close']).tail(14)
                        df_qqe_btc = ta.qqe(btc['close']).tail(14)
                        df_qqe_btc.fillna(value=0, inplace=True)  # Replace NaNs with 0
                        df_percent_rtrn_btc = ta.percent_return(btc['close']).tail(20)
                        df_psar_btc = ta.psar(btc['high'], btc['low']).tail(50)
                        df_cdl_pattern = ta.cdl_pattern(btc['open'], btc['high'], btc['low'], btc['close']).tail(50)
                        df_cdl_z_btc = ta.cdl_z(btc['open'], btc['high'], btc['low'], btc['close']).tail(50)
                        df_ha_btc = ta.ha(btc['open'], btc['high'], btc['low'], btc['close']).tail(50)






                        df_adx_btc['timestamp'] = btc['Timestamp'].tail(14)
                        df_qqe_btc['timestamp'] = btc['Timestamp'].tail(14)
                        df_psar_btc['timestamp'] = btc['Timestamp'].tail(50)
                        df_cdl_pattern['timestamp'] = btc['Timestamp'].tail(50)
                        df_ha_btc['timestamp'] = btc['Timestamp'].tail(50)
                        adx_dict_btc = {
                            'ADX_14': {df_adx_btc['timestamp'].iloc[-1]: df_adx_btc['ADX_14'].iloc[-1]},
                            'DMP_14': {df_adx_btc['timestamp'].iloc[-1]: df_adx_btc['DMP_14'].iloc[-1]},
                            'DMN_14': {df_adx_btc['timestamp'].iloc[-1]: df_adx_btc['DMN_14'].iloc[-1]}
                        }

                        cmf_dict_btc = {btc["Timestamp"].tail(20).iloc[-1]: df_cmf_btc.iloc[-1]}
                        mfi_dict_btc = {btc["Timestamp"].tail(14).iloc[-1]: df_mfi_btc.iloc[-1]}
                        rsi_dict_btc = {btc["Timestamp"].tail(14).iloc[-1]: df_rsi_btc.iloc[-1]}
                        sma_dict_btc = {btc["Timestamp"].tail(10).iloc[-1]: df_sma_btc.iloc[-1]}
                        cdl_inside_btc = {btc["Timestamp"].tail(14).iloc[-1]: df_cdl_inside_btc.iloc[-1]}
                        qqe_btc = {
                                col: {df_qqe_btc['timestamp'].iloc[-1]: df_qqe_btc[col].iloc[-1]} for col in df_qqe_btc.columns if col != 'timestamp'
                            }
                        percent_rtrn = {btc['Timestamp'].tail(20).iloc[-1]: df_percent_rtrn_btc.iloc[-1]}
                        psar_btc = {
                            col: {df_psar_btc['timestamp'].tail(50).iloc[-1]: df_psar_btc[col].iloc[-1]} for col in df_psar_btc.columns if col != 'timestamp'
                            
                        }
                        cdl_pattern_btc = {
                            col: {df_cdl_pattern['timestamp'].tail(50).iloc[-1]: df_cdl_pattern[col].iloc[-1]} for col in df_cdl_pattern.columns if col != 'timestamp'

                        }
                        cdl_z_btc = {btc['Timestamp'].tail(50).iloc[-1]: df_cdl_z_btc.iloc[-1]}
                        ha_btc = {
                            col: {df_ha_btc['timestamp'].tail(50).iloc[-1]: df_ha_btc[col].iloc[-1]} for col in df_ha_btc.columns if col != 'timestamp'

                        }



                        print('qqe btc : ', qqe_btc)
                        print('cdl inside btc: ', cdl_inside_btc)
                        print('percent_return :', percent_rtrn)
                        print('psar : ', psar_btc)
                        print('cdl pattern btc : ', cdl_pattern_btc)
                        print('cdl z btc : ', cdl_z_btc)


                        # Emitting BTC data
                        socketio.emit('adx', {'data': adx_dict_btc})
                        btcadx_indicators.insert_one(adx_dict_btc)

                        socketio.emit('cmf', {'data': cmf_dict_btc})
                        btccmf_indicators.insert_one(cmf_dict_btc)

                        socketio.emit('mfi', {'data': mfi_dict_btc})
                        btcmfi_indicators.insert_one(mfi_dict_btc)

                        socketio.emit('rsi', {'data': rsi_dict_btc})
                        btcrsi_indicators.insert_one(rsi_dict_btc)

                        socketio.emit('sma', {'data': sma_dict_btc})
                        btcsma_indicators.insert_one(sma_dict_btc)

                    # ETH calculations
                    timestamp_eth = pd.to_datetime(json_data_eth['k']['t'], unit='ms')
                    timestamp_eth = timestamp_eth.strftime("%Y-%m-%d %H:%M:%S")
                    open_price_eth = float(json_data_eth['k']['o'])
                    high_eth = float(json_data_eth['k']['h'])
                    low_eth = float(json_data_eth['k']['l'])
                    close_eth = float(json_data_eth['k']['c'])
                    volume_eth = float(json_data_eth['k']['v'])

                    new_row_eth = {
                        'Timestamp': timestamp_eth,
                        'open': open_price_eth,
                        'high': high_eth,
                        'low': low_eth,
                        'close': close_eth,
                        'volume': volume_eth
                    }
                    eth.loc[len(eth)] = new_row_eth
                    print(len(eth))

                    if len(eth) >= 50:
                        # ETH indicators calculations
                        df_adx_eth = ta.adx(eth['high'], eth['low'], eth['close']).tail(14)
                        df_cmf_eth = ta.cmf(eth['high'], eth['low'], eth['close'], eth['volume']).tail(20)
                        df_mfi_eth = ta.mfi(eth['high'], eth['low'], eth['close'], eth['volume']).tail(14)
                        df_rsi_eth = ta.rsi(eth['close']).tail(14)
                        df_sma_eth = ta.sma(eth['close']).tail(10)
                        df_cdl_inside_eth = ta.cdl_inside(eth['open'], eth['high'], eth['low'], eth['close']).tail(14)
                        df_qqe_eth = ta.qqe(eth['close'])
                        df_qqe_eth.fillna(value=0, inplace=True)  # Replace NaNs with 0
                        df_percent_rtrn_eth = ta.percent_return(eth['close']).tail(20)
                        df_psar_eth = ta.psar(eth['high'], eth['low']).tail(50)
                        

                        

                        df_adx_eth['timestamp'] = eth['Timestamp'].tail(14)
                        df_qqe_eth['timestamp'] = eth['Timestamp'].tail(14)
                        df_psar_eth['timestamp'] = eth['Timestamp'].tail(50)
                        
                        adx_dict_eth = {
                            'ADX_14': {df_adx_eth['timestamp'].iloc[-1]: df_adx_eth['ADX_14'].iloc[-1]},
                            'DMP_14': {df_adx_eth['timestamp'].iloc[-1]: df_adx_eth['DMP_14'].iloc[-1]},
                            'DMN_14': {df_adx_eth['timestamp'].iloc[-1]: df_adx_eth['DMN_14'].iloc[-1]}
                        }

                        cmf_dict_eth = {eth["Timestamp"].tail(20).iloc[-1]: df_cmf_eth.iloc[-1]}
                        mfi_dict_eth = {eth["Timestamp"].tail(14).iloc[-1]: df_mfi_eth.iloc[-1]}
                        rsi_dict_eth = {eth["Timestamp"].tail(14).iloc[-1]: df_rsi_eth.iloc[-1]}
                        sma_dict_eth = {eth["Timestamp"].tail(10).iloc[-1]: df_sma_eth.iloc[-1]}
                        cdl_inside_eth = {eth["Timestamp"].tail(10).iloc[-1]: df_cdl_inside_eth.iloc[-1]}

                        qqe_eth = {
                                col: {df_qqe_eth['timestamp'].iloc[-1]: df_qqe_eth[col].iloc[-1]} for col in df_qqe_eth.columns if col != 'timestamp'
                            }
                        percent_rtrn_eth = {eth['Timestamp'].tail(20).iloc[-1]: df_percent_rtrn_eth.iloc[-1]}
                        psar_eth = {
                                col: {df_psar_eth['timestamp'].iloc[-1]: df_psar_eth[col].iloc[-1]} for col in df_psar_eth.columns if col != 'timestamp'
                            }

                        print('qqe eth: ', qqe_eth)
                        print('cdl inside eth : ', cdl_inside_eth)
                        print('percent_rtrn_eth: ', percent_rtrn_eth)
                        print('psar eth : ', psar_eth)

                        # Emitting ETH data
                        socketio.emit('adx', {'data': adx_dict_eth})
                        ethadx_indicators.insert_one(adx_dict_eth)

                        socketio.emit('cmf', {'data': cmf_dict_eth})
                        ethcmf_indicators.insert_one(cmf_dict_eth)

                        socketio.emit('mfi', {'data': mfi_dict_eth})
                        ethmfi_indicators.insert_one(mfi_dict_eth)

                        socketio.emit('rsi', {'data': rsi_dict_eth})
                        ethrsi_indicators.insert_one(rsi_dict_eth)

                        socketio.emit('sma', {'data': sma_dict_eth})
                        ethsma_indicators.insert_one(sma_dict_eth)

        except websockets.ConnectionClosed:
            print("Connection with server closed. Reconnecting...")
        except Exception as e:
            tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
            print("".join(tb_str))
            print(f"An unexpected error occurred: {str(e)}. Attempting to reconnect...")
                
        await asyncio.sleep(delay)  # pause before reattempting connection
        delay *= 2  # double the delay for each retry attempt
        retries += 1

    print("Max retries exceeded. Please check the connection and try again.")


def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


new_loop = asyncio.new_event_loop()
t = Thread(target=start_loop, args=(new_loop,))
t.start()
asyncio.run_coroutine_threadsafe(calculate_indicators(), new_loop)


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
