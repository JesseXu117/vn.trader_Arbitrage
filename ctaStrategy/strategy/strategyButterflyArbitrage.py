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
class ButterflyStrategy(CtaArbitrageTemplate):
    """蝶式无风险套利策略"""
    strategyName = u'蝶式无风险套利策略'  # 策略实例名称
    className = u'ButterflyStrategy'
    author = u'Jesse'

    # 策略参数
    initDays = 0  # 初始化数据所用的天数, 此处只需要监控套利机会故为0
    fee = 0.0

    # 策略变量
    bar = None
    barMinute = EMPTY_STRING
    posDict = {}

    ask_C1 = 0.0
    ask_C2 = 0.0
    ask_C3 = 0.0
    bid_C1 = 0.0
    bid_C2 = 0.0
    bid_C3 = 0.0

    ask_C1_volume = 0
    ask_C2_volume = 0
    ask_C3_volume = 0
    bid_C1_volume = 0
    bid_C2_volume = 0
    bid_C3_volume = 0

    ask_P1 = 0.0
    ask_P2 = 0.0
    ask_P3 = 0.0
    bid_P1 = 0.0
    bid_P2 = 0.0
    bid_P3 = 0.0

    ask_P1_volume = 0
    ask_P2_volume = 0
    ask_P3_volume = 0
    bid_P1_volume = 0
    bid_P2_volume = 0
    bid_P3_volume = 0

    # exercise_date = '2017-08-07'
    # today = date.today()
    # T = (datetime(int(exercise_date[:4]),int(exercise_date[5:7]),int(exercise_date[-2:])) -
    #              datetime(today.year,today.month,today.day)).days
    # rate = 0.03
    # 不考虑折现

    # 参数列表，保存了参数的名称
    paramList = ['strategyName',
                 'className',
                 'author',
                 'vtSymbol',
                 'Symbol1',
                 'Symbol2',
                 'Symbol3'
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',  # 是否初始化
               'trading',  # 交易状态
               'pos',  # 仓位状态
               'option_type',
               'underlying',
               'K1',
               'K2',
               'K3'
               ]

    # ----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(ButterflyStrategy, self).__init__(ctaEngine, setting)

        if setting:
            self.symbol1 = setting['Symbol1']
            self.symbol2 = setting['Symbol2']
            self.symbol3 = setting['Symbol3']

        self.underlying = self.symbol1[:5]
        if self.symbol1[6:7] == 'C':
            self.option_type = 'Call'
        elif self.symbol1[6:7] == 'P':
            self.option_type = 'Put'
        else:
            raise ValueError('error: symbol')

        self.K1 = int(self.symbol1[-4:])
        self.K2 = int(self.symbol2[-4:])
        self.K3 = int(self.symbol3[-4:])

        if self.K1 >= self.K2 or self.K2 >= self.K3:
            raise ValueError('K1 < K2 < K3 must be satified!')

        self.posDict[self.symbol1] = 0.0
        self.posDict[self.symbol2] = 0.0
        self.posDict[self.symbol3] = 0.0

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
        # print tick.vtSymbol

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
            elif tick.vtSymbol == self.symbol3:
                self.ask_C3 = tick.askPrice1
                self.ask_C3_volume = tick.askVolume1
                self.bid_C3 = tick.askPrice1
                self.bid_C3_volume = tick.bidVolume1

                #### fee ####
                size = min(min(self.ask_C1_volume, self.bid_C2_volume), self.ask_C3_volume)

                if (self.ask_C1 - self.bid_C2 + 2 * self.fee)/(self.K2 - self.K1) < (self.bid_C2 - self.ask_C3 - 2 * self.fee)/(self.K3 - self.K2):
                    print 'call option butterfly: open position'
                    self.buy(self.ask_C1, size, self.symbol1)
                    self.short(self.bid_C2, 2 * size, self.symbol2)
                    self.buy(self.ask_C3, size , self.symbol3)

                    self.posDict[self.symbol1] += size
                    self.posDict[self.symbol2] -= 2 * size
                    self.posDict[self.symbol3] += size

                ### close a position
                if self.posDict[self.symbol1] * self.posDict[self.symbol2] < 0 and \
                    self.posDict[self.symbol2] * self.posDict[self.symbol3] < 0:

                    if (self.bid_C1 - self.ask_C2 - 2 * self.fee) / (self.K2 - self.K1) > (
                            self.ask_C2 - self.bid_C3 + 2 * self.fee) / (self.K3 - self.K2):
                        self.sell(self.bid_C1, self.posDict[self.symbol1], self.symbol1)
                        self.cover(self.ask_C2, self.posDict[self.symbol2], self.symbol2)
                        self.sell(self.bid_C3, self.posDict[self.symbol3], self.symbol3)
                        print 'call option butterfly: close position'
                ### handle the failure of order


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
            elif tick.vtSymbol == self.symbol3:
                self.ask_P3 = tick.askPrice1
                self.ask_P3_volume = tick.askVolume1
                self.bid_P3 = tick.askPrice1
                self.bid_P3_volume = tick.bidVolume1

                #### fee####
                size = min(min(self.ask_P1_volume, self.bid_P2_volume), self.ask_P3_volume)

                if (self.bid_P2 - self.ask_P1 - 2 * self.fee)/(self.K2 - self.K1) > (self.ask_P3 - self.bid_P2 + 2 * self.fee)/(self.K3 - self.K2):
                    print 'put option butterfly: open position'
                    self.buy(self.ask_P1, size, self.symbol1)
                    self.short(self.bid_P2, 2 * size, self.symbol2)
                    self.buy(self.ask_P3, size, self.symbol3)

                    self.posDict[self.symbol1] += size
                    self.posDict[self.symbol2] -= 2 * size
                    self.posDict[self.symbol3] += size

                if self.posDict[self.symbol1] * self.posDict[self.symbol2] < 0 and \
                                        self.posDict[self.symbol2] * self.posDict[self.symbol3] < 0:
                    if (self.bid_P1 - self.ask_P2 - 2 * self.fee) / (self.K2 - self.K1) > (
                                    self.ask_P2 - self.bid_P3 + 2 * self.fee) / (self.K3 - self.K2):
                        self.sell(self.bid_P1, self.posDict[self.symbol1], self.symbol1)
                        self.cover(self.ask_P2, self.posDict[self.symbol2], self.symbol2)
                        self.sell(self.bid_P3, self.posDict[self.symbol3], self.symbol3)
                        print 'put option butterfly: close position'
                ### handle the failure of order

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        pass

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        pass


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
    engine.initStrategy(ButterflyStrategy, {})

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