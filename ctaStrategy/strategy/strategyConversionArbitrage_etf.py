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
class ETFConversionStrategy(CtaArbitrageTemplate):
    """转换无风险套利策略"""
    strategyName = u'转换无风险套利策略'  # 策略实例名称
    className = u'ETFConversionStrategy'
    author = u'Jesse'

    # 策略参数
    initDays = 0  # 初始化数据所用的天数, 此处只需要监控套利机会故为0
    option_fee = 0.0
    future_fee = 0.0
    K = 2.50
    underlying = '510050.SH'

    # 策略变量
    bar = None
    barMinute = EMPTY_STRING
    posDict = {}

    ask_call = 0.0
    bid_call = 0.0
    ask_call_volume = 0
    bid_call_volume = 0

    ask_put = 0.0
    bid_put = 0.0
    ask_put_volume = 0
    bid_put_volume = 0

    ask_underly = 0.0
    ask_underly_volume = 0
    bid_underly = 0.0
    bid_underly_volume = 0

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
                 'call_symbol',
                 'put_symbol'
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',  # 是否初始化
               'trading',  # 交易状态
               'pos',  # 仓位状态
               'underlying',
               'K'
               ]

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(ETFConversionStrategy, self).__init__(ctaEngine, setting)

        if setting:
            self.call_symbol = setting['callSymbol']
            self.put_symbol = setting['putSymbol']

        self.posDict[self.call_symbol] = 0.0
        self.posDict[self.put_symbol] = 0.0
        self.posDict[self.underlying] = 0.0

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
        # self.lastOrder = order
        pass

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
        print tick.vtSymbol

        if tick.vtSymbol == self.call_symbol:
            self.ask_call = tick.askPrice1
            self.ask_call_volume = tick.askVolume1
            self.bid_call = tick.bidPrice1
            self.bid_call_volume = tick.bidVolume1
        elif tick.vtSymbol == self.put_symbol:
            self.ask_put = tick.askPrice1
            self.ask_put_volume = tick.askVolume1
            self.bid_put = tick.bidPrice1
            self.bid_put_volume = tick.bidVolume1
        elif tick.vtSymbol == self.underlying:
            self.ask_underly = tick.askPrice1
            self.ask_underly_volume = tick.askVolume1
            self.bid_underly = tick.bidPrice1
            self.bid_underly_volume = tick.bidVolume1

            size1 = min(min(self.ask_put_volume, self.bid_call_volume), self.ask_underly_volume)
            size2 = min(min(self.bid_put_volume, self.ask_call_volume), self.bid_underly_volume)

            #### fee ####
            if self.bid_call - self.ask_put - 2 * self.option_fee  > self.ask_underly + self.future_fee - self.K:
                print 'positive conversion arbitrage'
                size = size1
                self.buy(self.ask_put, size, self.put_symbol)
                self.short(self.bid_call, size, self.call_symbol)
                self.buy(self.ask_underly, size, self.underlying)

                self.posDict[self.put_symbol] += size
                self.posDict[self.call_symbol] -= size
                self.posDict[self.underlying] += size

            elif self.ask_call - self.bid_put + 2 * self.option_fee < self.bid_underly - self.future_fee - self.K:
                print 'negenative conversion arbitrage'
                size = size2
                self.buy(self.ask_call, size, self.call_symbol)
                self.short(self.bid_put, size, self.put_symbol)
                self.buy(self.bid_underly, size, self.underlying)

                self.posDict[self.call_symbol] += size
                self.posDict[self.posDict] -= size
                self.posDict[self.underlying] += size

            ### close position
            if self.posDict[self.call_symbol] * self.posDict[self.put_symbol] < 0 and self.posDict[self.underlying]!=0:
                if self.ask_call - self.bid_put - 2 * self.option_fee  > self.bid_underly + self.future_fee - self.K:
                    self.sell(self.bid_put, self.posDict[self.put_symbol], self.put_symbol)
                    self.cover(self.ask_call, self.posDict[self.call_symbol], self.call_symbol)
                    self.sell(self.bid_underly, self.posDict[self.underlying], self.underlying)
                elif self.bid_call - self.ask_put + 2 * self.option_fee < self.ask_underly - self.future_fee - self.K:
                    self.sell(self.bid_call, self.posDict[self.call_symbol], self.call_symbol)
                    self.cover(self.ask_put, self.posDict[self.put_symbol], self.put_symbol)
                    self.sell(self.ask_underly, self.posDict[self.underlying], self.underlying)

            ### handle the failure of order

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        pass

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
    engine.initStrategy(ETFConversionStrategy, {})

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