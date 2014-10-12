
import da
from enum import Enum
Outcome = Enum('Outcome', 'Processed InconsistentWithHistory InsufficientFunds')
ReqType = Enum('ReqType', 'Query Deposit Withdraw Transfer')
Source = Enum('Source', 'server client')

class Request(object):

    def __init__(self, reqID, reqtype, account_num, amount):
        self.reqID = reqID
        self.reqtype = reqtype
        self.account_num = account_num
        self.amount = amount

class InitReq(object):

    def __init__(self, src, srcName, bankName):
        self.src = src
        self.srcName = srcName
        self.bankName = bankName

class Reply(object):

    def __init__(self, reqID, outcome, balance):
        self.reqID = reqID
        self.outcome = outcome
        self.balance = balance
