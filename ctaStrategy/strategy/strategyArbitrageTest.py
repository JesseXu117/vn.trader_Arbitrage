# encoding: UTF-8

"""
这里的Demo是一个最简单的策略实现，并未考虑太多实盘中的交易细节，如：
1. 委托价格超出涨跌停价导致的委托失败
2. 委托未成交，需要撤单后重新委托
3. 断网后恢复交易状态
4. 等等
这些点是作者选择特意忽略不去实现，因此想实盘的朋友请自己多多研究CTA交易的一些细节，
做到了然于胸后再去交易，对自己的money和时间负责。
也希望社区能做出一个解决了以上潜在风险的Demo出来。
"""

from ctaStrategy.ctaBase import *
from ctaStrategy.ctaArbitrageTemplate import CtaArbitrageTemplate

import talib as ta
import numpy as np
from datetime import *

EMPTY_STRING = ''


########################################################################
class ArbitrageTestStrategy(CtaArbitrageTemplate):
    """套利测试策略"""
    strategyName = u'套利测试策略'        # 策略实例名称
    className = u'ArbitrageTestStrategy'
    author = u'Jesse'

    # 策略参数
    initDays = 0  # 初始化数据所用的天数, 此处只需要监控套利机会故为0

    # 策略变量
    underlying = u'm1709'

    symbol1 = u'm1709-C-2650'
    symbol2 = u'm1709-C-2700'

    if symbol1[6:7] == 'C':
        option_type = 'Call'
    elif symbol1[6:7] == 'P':
        option_type = 'Put'

    K1 = int(symbol1[-4:])
    K2 = int(symbol2[-4:])

    if K1 >= K2:
        raise ValueError('K1 must be less than K2!')

    ask_C1 = 0.0
    ask_C2 = 0.0
    bid_C1 = 0.0
    bid_C2 = 0.0

    ask_C1_volume = 0
    ask_C2_volume = 0
    bid_C1_volume = 0
    bid_C2_volume = 0

    ask_P1 = 0.0
    ask_P2 = 0.0
    bid_P1 = 0.0
    bid_P2 = 0.0

    ask_P1_volume = 0
    ask_P2_volume = 0
    bid_P1_volume = 0
    bid_P2_volume = 0

    # exercise_date = '2017-08-07'
    # today = date.today()
    # T = (datetime(int(exercise_date[:4]),int(exercise_date[5:7]),int(exercise_date[-2:])) -
    #              datetime(today.year,today.month,today.day)).days
    # rate = 0.03

    # 参数列表，保存了参数的名称
    paramList = ['strategyName',
                 'className',
                 'author',
                 'vtSymbol',
                 'Symbol1',
                 'Symbol2'
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',    # 是否初始化
               'trading',   # 交易状态
               'pos',       # 仓位状态
               'option_type',
               'underlying',
               'K1',
               'K2'
               ]

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(ArbitrageTestStrategy, self).__init__(ctaEngine, setting)

        if setting:
            self.Symbol1 = setting['Symbol1']
            self.Symbol2 = setting['Symbol2']

        self.lastOrder = None

    # ----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        if self.initDays == 0:
            return
        self.writeCtaLog(u'策略初始化')
        for vtsymbol in self.vtSymbol:
            initData = self.loadTick(self.initDays, vtsymbol)
            for tick in initData:
                self.onTick(tick)

        self.putEvent()

    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'策略启动')
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'策略停止')
        self.putEvent()

    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        self.lastOrder = order

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
        print tick.vtSymbol

        if self.option_type == 'Call':
            if tick.vtSymbol == self.symbol1:
                self.ask_C1 = tick.askPrice1
                self.ask_C1_volume = tick.askVolume1
                self.bid_C1 = tick.bidPrice1
                self.bid_C1_volume = tick.bidVolume1
            elif tick.vtSymbol == self.symbol2:
                self.ask_C2 = tick.askPrice1
                self.ask_C2_volume = tick.askVolume1
                self.bid_C2 = tick.bidPrice1
                self.bid_C2_volume = tick.bidVolume1

                #### fee ####
                if self.ask_C1 - self.bid_C2 < 0:
                    print 'call option bull spread: C1 - C2 < 0'
                    size = min(self.ask_C1_volume, self.bid_C2_volume)
                    self.buy(self.ask_C1, size, self.symbol1)
                    self.short(self.bid_C2, size, self.symbol2)
                    #### add condition to handle the failure of order

                elif self.bid_C1 - self.ask_C2 > (self.K2 - self.K1):
                    print 'call option bear spread: C1 - C2 > (K2 - K1)'
                    size = min(self.bid_C1_volume, self.ask_C2_volume)
                    self.short(self.bid_C1, size, self.symbol1)
                    self.buy(self.ask_C2, size, self.symbol2)
                    #### add condition to handle the failure of order

        elif self.option_type == 'Put':
            if tick.vtSymbol == self.symbol1:
                self.ask_P1 = tick.askPrice1
                self.ask_P1_volume = tick.askVolume1
                self.bid_P1 = tick.bidPrice1
                self.bid_P1_volume = tick.bidVolume1
            elif tick.vtSymbol == self.symbol2:
                self.ask_P2 = tick.askPrice1
                self.ask_P2_volume = tick.askVolume1
                self.bid_P2 = tick.bidPrice1
                self.bid_P2_volume = tick.bidVolume1

                #### fee####
                if self.ask_P2 - self.bid_P1 < 0:
                    print 'put option bull spread: P2 - P1 < 0'
                    size = min(self.ask_P1_volume, self.bid_P2_volume)
                    self.buy(self.ask_P2, size, self.symbol2)
                    self.short(self.bid_P1, size, self.symbol1)
                    #### add condition to handle the failure of order

                elif self.bid_P2 - self.ask_P1 > (self.K2 - self.K1):
                    print 'put option bear spread: P2 - P1 > (K2 - K1)'
                    size = min(self.bid_P1_volume, self.ask_P2_volume)
                    self.short(self.bid_P2, size, self.symbol2)
                    self.buy(self.ask_P1, size, self.symbol1)
                    #### add condition to handle the failure of order

        '''
        tickMinute = tick.datetime.minute  # by Jesse

        if tick.vtSymbol in self.barMinute.keys():  # by Jesse
            barMinute = self.barMinute[tick.vtSymbol]
        else:
            barMinute = EMPTY_STRING
        self.lastTick[tick.vtSymbol] = tick
        dt = datetime.datetime.strftime(tick.datetime, '%Y-%m-%d %H:%M:%S')
        # if tick.askPrice1 - tick.bidPrice1 >1:
        #    print dt,tick.vtSymbol,tick.lastPrice,tick.bidPrice1,tick.askPrice1
        # 撤单判断与执行,待修改
        if tickMinute != barMinute:
            if tick.vtSymbol in self.bar.keys():  # by hw
                self.onBar(self.bar[tick.vtSymbol])  # by hw

            bar = CtaBarData()
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime  # K线的时间设为第一个Tick的时间

            # 实盘中用不到的数据可以选择不算，从而加快速度
            # bar.volume = tick.volume
            # bar.openInterest = tick.openInterest

            self.bar[tick.vtSymbol] = bar  # 这种写法为了减少一层访问，加快速度 by hw
            self.barMinute[tick.vtSymbol] = tickMinute  # 更新当前的分钟 by hw
            self.barTime[tick.vtSymbol] = tick.datetime
        else:  # 否则继续累加新的K线
            bar = self.bar[tick.vtSymbol]  # 写法同样为了加快速度

            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice
        '''

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        pass
        '''
        # 计算基础变量macd，pbx .by hw
        vtsymbol = bar.vtSymbol
        if vtsymbol in self.closeList.keys():
            l = self.closeList[vtsymbol]
        else:
            l = []
            self.closeList[vtsymbol] = l

        l.append(bar.close)

        self.writeCtaLog(u'symbol:%s' % bar.vtSymbol)
        # 策略信号
        longsignal = False
        shortsignal = False
        sellsignal = False
        coversignal = False

        for vts in self.vtSymbol:
            print 'signal:', vts, self.vtSymbol, self.bar[vts].datetime.hour, self.longSymbol, self.shortSymbol, \
            self.posToday[vts], self.bar[vts].datetime.minute
            if self.posToday[vts] == 0 and cmp(vts, self.longSymbol) and self.bar[vts].datetime.hour >= 14 and self.bar[
                vts].datetime.minute < 50:
                longsignal = True
                # print longsignal
            if self.posToday[vts] == 0 and vts == self.shortSymbol and self.bar[vts].datetime.hour >= 14 and self.bar[
                vts].datetime.minute < 50:
                shortsignal = True

            if self.posToday[vts] == 1 and vts == self.longSymbol and self.bar[vts].datetime.hour >= 14 and self.bar[
                vts].datetime.minute > 50:
                sellsignal = True

            if self.posToday[vts] == -1 and vts == self.shortSymbol and self.bar[vts].datetime.hour >= 14 and self.bar[
                vts].datetime.minute > 50:
                coversignal = True

        # 金叉和死叉的条件是互斥
        # 所有的委托均以K线收盘价委托（这里有一个实盘中无法成交的风险，考虑添加对模拟市价单类型的支持）
        print longsignal, shortsignal, self.posToday[self.longSymbol], self.posToday[self.shortSymbol], self.tradeState[
            self.longSymbol], self.tradeState[self.shortSymbol]

        if sellsignal and self.posToday[self.longSymbol] == 1 and self.tradeState[self.longSymbol] <> -1:
            self.tradeID = self.sell(self.bar[self.longSymbol].close, 1, self.longSymbol)
            self.tradeState[self.longSymbol] = -1
            print 'trade 1'

        if coversignal and self.posToday[self.shortSymbol] == -1 and self.tradeState[self.shortSymbol] <> 1:
            self.tradeID = self.cover(self.bar[self.shortSymbol].close, 1, self.shortSymbol)
            self.tradeState[self.shortSymbol] = 1
            print 'trade 2'

        if longsignal and self.tradeState[self.longSymbol] <> 1:
            self.tradeID = self.buy(self.bar[self.longSymbol].close, 1, self.longSymbol)
            self.tradeState[self.longSymbol] = 1
            print 'trade 3'

        if shortsignal and self.tradeState[self.shortSymbol] <> -1:
            self.tradeID = self.short(self.bar[self.shortSymbol].close, 1, self.shortSymbol)
            self.tradeState[self.shortSymbol] = -1
            print 'trade 4'
        '''
        # 发出状态更新事件
        self.putEvent()

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        pass
        # self.posToday[trade.vtSymbol] = self.posToday[trade.vtSymbol] + self.tradeState[trade.vtSymbol]
        # self.tradeState[trade.vtSymbol] = 0
        # print 'trade', trade.vtSymbol, self.posToday[trade.vtSymbol], self.tradeState[trade.vtSymbol]


if __name__ == '__main__':
    # 提供直接双击回测的功能
    # 导入PyQt4的包是为了保证matplotlib使用PyQt4而不是PySide，防止初始化出错
    from ctaStrategy.ctaBacktesting_Arbitrage import *
    from PyQt4 import QtCore, QtGui

    # 创建回测引擎
    engine = BacktestingEngine()

    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20170101')

    # 设置产品相关参数
    engine.setSlippage(0.2)  # 股指1跳
    engine.setRate(0.3 / 10000)  # 万0.3
    engine.setSize(300)  # 股指合约大小
    engine.setPriceTick(0.2)  # 股指最小价格变动

    # 设置使用的历史数据库
    engine.setDatabase(MINUTE_DB_NAME, 'IF0000')

    # 在引擎中创建策略对象
    engine.initStrategy(ArbitrageTestStrategy, {})

    # 开始跑回测
    engine.runBacktesting()

    # 显示回测结果
    engine.showBacktestingResult()

    ## 跑优化
    # setting = OptimizationSetting()                 # 新建一个优化任务设置对象
    # setting.setOptimizeTarget('capital')            # 设置优化排序的目标是策略净盈利
    # setting.addParameter('atrLength', 12, 20, 2)    # 增加第一个优化参数atrLength，起始11，结束12，步进1
    # setting.addParameter('atrMa', 20, 30, 5)        # 增加第二个优化参数atrMa，起始20，结束30，步进1
    # setting.addParameter('rsiLength', 5)            # 增加一个固定数值的参数

    ## 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    ## 测试时还跑着一堆其他的程序，性能仅供参考
    # import time
    # start = time.time()

    ## 运行单进程优化函数，自动输出结果，耗时：359秒
    # engine.runOptimization(AtrRsiStrategy, setting)

    ## 多进程优化，耗时：89秒
    ##engine.runParallelOptimization(AtrRsiStrategy, setting)

    # print u'耗时：%s' %(time.time()-start)