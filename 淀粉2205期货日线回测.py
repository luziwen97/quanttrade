#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 12 18:22:55 2021

@author: imac
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  2 21:16:59 2021

@author: imac
"""

import akshare as ak
import time 
import pandas as pd
from tqsdk.tafunc import ema,ref,llv,hhv,sma
import mplfinance as mpf
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import numpy as np


import plotly
import plotly.graph_objects as go

#获取历史数据，进行回测使用
def get_hisdata():
    df = ak.futures_zh_daily_sina(symbol="ma2209")
    df['var1']=(df['close']+df['high']+df['low'])/3
    df['var2']=ema(df['var1'],10)
    df['var3']=ref(df['var2'],1)
    
    df['hv'] = df["high"].rolling(9).max()
    df['lv'] = df["low"].rolling(9).min()
    df['rsv']=((df['close']-df['lv'])/(df['hv']-df['lv']))*100
    df['up_buy']=sma(df['rsv'], 3, 1)
    df['down_sell']=sma(df['up_buy'],3,1)
    

    
    return df
#将数据mpf话，方便进行mpf画图
def mp(data):
    data.rename(
            columns={
            'date': 'Date', 'open': 'Open', 
            'high': 'High', 'low': 'Low', 
            'close': 'Close', 'volume': 'Volume'}, 
            inplace=True)
    
    data['Date'] = pd.to_datetime(data['Date'])
    data.set_index(['Date'], inplace=True)
    return data
#当与交易时间同步时，调用该方法进行数据获取



class Astock(object):
    def __init__(self,strategy_name):
        self._strategy_name = strategy_name
        self.dt=[]
        self.open=[]
        self.high=[]
        self.low=[]
        self.close=[]
        self.volume=[]
        self.settle=[]
        self.var1=[]
        self.var2=[]
        self.var3=[]
        self.hold=[]

        
        #多单列表
        self.more_current_orders = {}
        self.more_history_orders = {}
        self.more_order_number = 0

        
        #空单列表
        self.empty_current_orders = {}
        self.empty_history_orders = {}
        self.empty_order_number = 0

        
    def run(self,hisdata):
        if self.dt!=hisdata[0]:
            self.dt.insert(0,hisdata[0])
            self.open.insert(0,hisdata[1])
            self.high.insert(0,hisdata[2])
            self.low.insert(0,hisdata[3])
            self.close.insert(0,hisdata[4])
            self.volume.insert(0,hisdata[5])
            self.hold.insert(0,hisdata[6])
            self.settle.insert(0,hisdata[7])
            self.var1.insert(0,hisdata[8])
            self.var2.insert(0,hisdata[9])
            self.var3.insert(0,hisdata[10])
            
            
         #做多 
    def make_more(self,price,volume):
        self.more_order_number += 1
        key="order" + str(self.more_order_number)
        self.more_current_orders[key]={
            "open_datetime" : self.dt[0],
            "open_price"  : price,
            "volume"    : volume
            }
        #做空

        
    def make_empty(self,price,volume):
        self.empty_order_number += 1
        key="order" + str(self.empty_order_number)
        self.empty_current_orders[key]={
            "open_datetime" : self.dt[0],
            "open_price"  : price,
            "volume"    : volume
            }
        #平多

        
    def sell_more(self,key,price):
        self.more_current_orders[key]['close_price']=price
        self.more_current_orders[key]['close_datetime']=self.dt[0]
        self.more_current_orders[key]['pnl'] = \
            (price - self.more_current_orders[key]['open_price'])
        self.more_history_orders[key] = self.more_current_orders.pop(key)
        
        #平空
    def sell_empty(self,key,price):
        self.empty_current_orders[key]['close_price']=price
        self.empty_current_orders[key]['close_datetime']=self.dt[0]
        self.empty_current_orders[key]['pnl'] = \
            (self.empty_current_orders[key]['open_price'] - price) 
        self.empty_history_orders[key] = self.empty_current_orders.pop(key)

        
        #策略方法
    def strategy(self):
        #做多平多
        if 0 == len(self.more_current_orders) :
            if  self.var2 >self.var3:
                
                    self.make_more(self.close[0],1)
                    print("做多")
            else:
                    print("做多等待")
                
        elif 1 == len(self.more_current_orders):
            
            if self.var2 <self.var3:
                key = list(self.more_current_orders.keys())[0]
                if self.dt[0] != self.more_current_orders[key]['open_datetime'][0]:
                        self.sell_more(key, self.close[0])
            
                        print('open date is %s, close date is: %s.'
                          % (self.more_history_orders[key]['open_datetime'],
                             self.dt[0]))
                        
        
        #做空平空   
        if 0 == len(self.empty_current_orders) :
            if self.var2 <self.var3:
                    self.make_empty(self.close[0],1)
                    print("做空")
            else:
                    print("做空等待")
        elif 1 == len(self.empty_current_orders):    
            if self.var2 >self.var3:
                key = list(self.empty_current_orders.keys())[0]
                if self.dt[0] != self.empty_current_orders[key]['open_datetime'][0]:
                        self.sell_empty(key, self.close[0])

                        print('open date is %s, close date is: %s.'
                          % (self.empty_history_orders[key]['open_datetime'],
                             self.dt[0]))
        
        
        
                        
        

            

 

if __name__ =="__main__":
    ast=Astock("ma") #初始化类
    
    
    data=get_hisdata()
    
    dat=mp(get_hisdata())

    dat['open_price']=np.nan
    dat['close_price']=np.nan
    
    for i in range(len(data)):
            hisdata=data.loc[i]
            ast.run(hisdata)
            ast.strategy()
           
            #订单行情
            more_orders=ast.more_history_orders
            empty_orders=ast.empty_history_orders
            cur=ast.more_current_orders
        
    empty_orders_df=pd.DataFrame(empty_orders)
    
    more_orders_df=pd.DataFrame(more_orders)
    more_orders_df.loc['close_datetime']=pd.to_datetime(more_orders_df.loc['close_datetime'],format="%Y-%m-%d")
    more_orders_df.loc['open_datetime']=pd.to_datetime(more_orders_df.loc['open_datetime'],format="%Y-%m-%d")
    list_dttt=dat.index.to_list()
    y=more_orders_df.loc['open_price'].to_list()
    x=more_orders_df.loc['open_datetime'].to_list()
    
    
    
    more_pnl=more_orders_df.loc['pnl'].to_list()
    
    pnl_more_all=0
    for i in more_pnl:
        
        pnl_more_all+=i
    more_all=pnl_more_all

    empty_pnl=empty_orders_df.loc['pnl'].to_list()
    
    pnl_empty_all=0
    for i in empty_pnl:
        
        pnl_empty_all+=i
    empty_all=pnl_empty_all
    
    
    
    for p in range(len(x)):
        xx=x[p]
        
        for i in range(len(list_dttt)):
            if xx==list_dttt[i]:
                dat['open_price'][i]=y[p]
                
    yy=more_orders_df.loc['close_price'].to_list()
    xx=more_orders_df.loc['close_datetime'].to_list()
 
    #订单OPEN时间及价格
    for p in range(len(xx)):
        xxx=xx[p]
        
        for i in range(len(list_dttt)):
            if xxx==list_dttt[i]:
                dat['close_price'][i]=yy[p]
                


   
    
    ap=[
        mpf.make_addplot(dat['open_price'], type='scatter', marker='^', markersize=200, color='r'),
        mpf.make_addplot(dat['close_price'], type='scatter', marker='v', markersize=200, color='g'),
        mpf.make_addplot(dat['lv'], type='line',color='b'),
        mpf.make_addplot(dat['hv'], type='line',color='b'),
        #mpf.make_addplot(dat['var1'], type='line',color='r'),
        mpf.make_addplot(dat['var2'], type='line',color='b'),
        mpf.make_addplot(dat['var3'], type='line',color='g'),
        
        mpf.make_addplot(dat['up_buy'], type='line',color='r',panel=1),
        mpf.make_addplot(dat['down_sell'], type='line',color='g',panel=1),
        ]
    mpf.plot(dat,type="candle",ylabel='Candle' ,addplot=ap,figratio=(10, 5),volume=False,figscale=1)
 
   

 
    '''
   实时跟进时调用
    while True:  
        hisdata=get_hisdata()
        hisdata=hisdata.to_list()
        if a != hisdata:
            a=hisdata
            ast.run(a)
            print(ast.dt[0])
            ast.strategy()
            print(ast.more_current_orders)
            print(ast.more_history_orders)
            print(ast.empty_current_orders)
            print(ast.empty_history_orders)
        elif a==hisdata:
            pass
        
        
        time.sleep(1)
   
    '''

    
    
        
        
