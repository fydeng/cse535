import re
import time
import sys
import collections
from init import *
import random

def parse_config(input_str):
    input_str = input_str.replace(' ','')
    strs = input_str.split(',')
    if int(strs[0])!= 0:
       	retrans = True
       	print ('Retransmission enabled')
    else:
       	reTrans = False
    retrans_interval = int(strs[1])
    print ('Timeout is:',retrans_interval)
    retrans_time = int(strs[2])
    print ('nRetrans is:',retrans_time)
    if int(strs[3])!= 0:
    	ifRandom = True
    	print ("Random request enabled")
    else:
    	ifRandom = False
    return [retrans, retrans_interval, retrans_time, ifRandom]

def parse_server(input_str):
		input_str =input_str.strip()
		input_str =input_str.replace(' ','')
		str =input_str.split(',')
		bankName = int(str[0])
		serverIP = str[1]
		startup_delay = str[2]
		life_time = str[3]
		return [bankName,serverIP, startup_delay,life_time]

def parse_client(input_str):
		input_str = input_str.replace(' ','')
		str = input_str.split(',')
		bankName = str[0]
		account_no = str[1]
		clientIP = str[2]
		return [bankName,account_no,clientIP]

def parse_req(input_str):
    input_str = input_str.replace(' ','')
    input_str = re.sub('[()]','',input_str)
    strs = input_str.split(',')
    if(strs[0]=='getBalance'):
        reqtype = ReqType.Query
    elif(strs[0]=='deposit'):
        reqtype = ReqType.Deposit
    elif(strs[0]=='withdraw'):
        reqtype = ReqType.Withdraw
    else:
        reqtype = ReqType.Transfer
    reqID = strs[1]
    account_num = strs[2]
    if reqtype == ReqType.Query:
        amount = 0
    else:
        amount = strs[3]
    return [reqID,reqtype,account_num,amount]

def parse_randomReq(input_str):
	input_str = input_str.strip()
	input_str = input_str.replace(' ','')
	input_str = re.sub('[()]','',input_str)
	strs = input_str.split(',')
	seed_num = int(strs[0])
	num_req = int(strs[1])
	prob_query = float(strs[2])
	prob_deposit = float(strs[3])
	prob_withdraw = float(strs[4])
	prob_transfer = float(strs[5])
	return [seed_num, num_req, prob_query, prob_deposit, prob_withdraw, prob_transfer]

class Master(process):
	def setup(srvDic, cliDic, filename,waitList):
		self.timesheet ={}
		self.srvDict = srvDic
		self.cliDict = cliDic
		self.filename = filename
		self.waitList = waitList

	def setup_logfile(filename):
		rootlog = logging.getLogger('')
		filelvl = logging.INFO
		fh = logging.FileHandler(filename)
		formatter = logging.Formatter('[%(asctime)s]%(name)s: %(message)s')
		fh.setFormatter(formatter)
		fh.setLevel(filelvl)
		rootlog._filelvl = filelvl
		rootlog.addHandler(fh)	

	def receive(msg=("PING",ping), from_=src_id):
		time_recv = logical_clock()
		flag = False
		print("Received PING from: ",ping.serverIP)
		bankname = ping.bankName
		for item in  self.srvDict[bankname]:
			if ping.serverIP == item[3]:
				flag = True
				self.timesheet.update({(ping.serverIP,ping.bankName):time_recv})
			else:
				pass
		if flag == False:
			for item in self.waitList:
				if ping.serverIP == item[4]:
					bank_name = item[0]
					oldTail = item[2]
					newSrv = item[1]
					print("Extending Chain, adding new server ",item[4],' to srvDic')
					self.srvDict[item[0]].append([item[1],item[2],item[3],item[4]])
					self.waitList.remove(item)
					flush_srvDict(bank_name)
					infoCli(bank_name,"tail",newSrv)
					send(("extendChain",newSrv),to = oldTail)

	def flush_srvDict(bankname):
		for i, item in enumerate(self.srvDict[bankname]):
			if len(self.srvDict[bankname]) == 1:
				item[1] = None
				item[2] = None
				return
			if i == 0:
				item[1] = None
				item[2] = srvDict[bankname][i+1][0]
				continue
			elif i == len(srvDict[bankname]) - 1:
				item[2] = None
				item[1] = srvDict[bankname][i-1][0]
			else:
				item[1] = srvDict[bankname][i-1][0]
				item[2] = srvDict[bankname][i+1][0]

	def infoCli(bankName,type,newSrv):
		for cli in self.cliDict[str(bankName)]:
			if type == "head":
				print("SENDING NEW HEAD TO CLIENT:",cli)
				send(("newHead",newSrv),to = cli)
			elif type == "tail":
				send(("newTail",newSrv),to = cli)
			elif type == "srvFail":
				send(("srvFail",newSrv),to = cli)

	def updateSrvInfo(srv):
		port = srv[0]
		bankName = srv[1]
		prevInfo =[]		#store the prev and next server of the previous of the failed server
		nextInfo =[]
		for item in self.srvDict[bankName]:
			if port == item[3]:		#find the failed server in srvDict
				prev = item[1]
				next = item[2]
				self.srvDict[bankName].remove(item)
				flush_srvDict(bankName)
				if prev == None:	#the failed item is head
					infoCli(bankName,"head",next)
				if next == None:	#the failed item is tail
					infoCli(bankName,"tail",prev)
				elif prev != None and next != None:
					infoCli(bankName,"srvFail",None)
		for item in self.srvDict[bankName]:
			if item[0] == prev or item[0] == next:
				send(("srvFail",(item[1],item[2])),to = item[0])
			else:
				pass

	def checkSrv(timesheet):
		time_chec = logical_clock()
		failedSrv =[]
		for key in timesheet.keys():
			if time_chec - timesheet.get(key)>5:
				print("Server ",key[0]," has failed!")
				failedSrv.append(key)
		for srv in failedSrv:
			del timesheet[srv]
			updateSrvInfo(srv)
		
	def main():
		output('Master  '+ str(self.id) +'  has started.')
		print("SERVER DICTIONARY STORED IN MASTER",self.srvDict)
		print("CLIENT DICTIONARY STORED IN MASTER",self.cliDict)
		print("SERVER WAITLIST STORED IN MASTER",self.waitList)

		while(True):
			if(await(False)):
				pass
			elif(timeout(5)):
				checkSrv(self.timesheet)
	

class Server(process):
	def setup(bankName, serverIP, startup_delay, life_time, prev, next, master):
		self.bankName = bankName
		self.serverIP = serverIP
		self.startup_delay =startup_delay
		self.life_time = int(life_time)
		self.prev =prev
		self.next = next
		self.master =master
		self.sentTrans = []
		self.procTrans = {}
		self.AccountInfo = {}


	def proc_balance(req):
		outcome = Outcome.Processed
		if self.AccountInfo.get(req.account_num) == None:
			cur_balance = 0
		else:
			cur_balance = AccountInfo[req.account_num]
		if procTrans.get(req.reqID) != None:
			if procTrans[req.reqID].reqtype != req.reqtype:
				#print("inconsistent")
				outcome = Outcome.InconsistentWithHistory
			else:
				#print("duplicate")
				pass
			new_balance = cur_balance
		else:
			if (req.reqtype == ReqType.Query):
				new_balance = cur_balance
			elif (req.reqtype == ReqType.Deposit):
				new_balance = cur_balance + req.amount
			elif (req.reqtype == ReqType.Withdraw):
				if (cur_balance - req.amount < 0):
					new_balance = cur_balance
					#print("insufficient")
					outcome = Outcome.InsufficientFunds
				else:
					new_balance = cur_balance - req.amount;
		if req.reqtype != ReqType.Query:
			sentTrans.append(req)
			output("Request %s has been added to sent transaction" % req.reqID)
		AccountInfo.update({req.account_num:new_balance})		
		return [new_balance, outcome]

	def update_procTrans(reqID):
		count_clear = 0
		len_sentTrans = len(sentTrans)
		for i in range(len_sentTrans):
			if (sentTrans[i].reqID == reqID):
				req = sentTrans[i]
				sentTrans.pop(i)
				if count_clear != 0:
					output('Using ACK to clear old req ', reqID)
				count_clear += 1
				if req.reqtype == ReqType.Query:
					break
				proc_req = self.procTrans.get(req.reqID)
				if proc_req == None:
					self.procTrans.update({req.reqID:req})
					output("Request %s has been added to processed transaction" % req.reqID)
				elif req.reqtype == proc_req.reqtype:
					output('Duplicate request, donot add to processed transaction')
				else:
					output('Inconsistent With Histroy request, donot add to processed transaction')
				break

	def receive(msg=("REQ", req), from_= src_id):
		output('Request ' + str(req.reqID) + ' from client received! ')
		if(self.life_time > 0):
			self.life_time = self.life_time-1
			output('the current life_time is: '+ str(self.life_time))
		elif(self.life_time==0):
			output('Server: '+ str(self.serverIP) + ' has expired!')
			sys.exit()		#which causes the server not sending reply back to the client
		
		result = proc_balance(req)
		new_balance = result[0]
		outcome = result[1]
		reply = Reply(req.reqID,outcome,new_balance)
		ack = Ack(req.reqID)
		if (prev == None):
			send(('REQ', req), to = next)
		elif (next == None):
			update_procTrans(req.reqID)
			send(('REPLY', reply), to = req.client_id)
			if (req.reqtype != ReqType.Query):
				send(('ACK', ack), to = prev)
				output(str(ack) + ' has been sent!')
		else:
			send(('REQ', req), to = next)
		output("Reply for Request %s has been sent" % reply.reqID)

	def receive(msg=("SYNC", req), from_= src_id):
		output('Synchronization of sentTrans from previous server received! ReqID is ', req.reqID)
		if req.reqtype != ReqType.Query:
			sentTrans.append(req)
		output("Request %s has been added to sent transaction" % req.reqID)
		if next != None:
			send(('SYNC', req), to = next)

	def receive(msg=('ACK', ack), from_= next):
		output(str(ack) + ' has been received!')
		update_procTrans(ack.reqID)

	def receive(msg=("srvFail",(prev,next)), from_ = master):
		print("I'm the prev or next of the failed server, changing my prev and next...")
		self.prev = prev
		self.next = next
		print("Setting my prev to: ",self.prev," and my next to: ",self.next)
		for i in range(len(sentTrans)):
			req = sentTrans[i]
			print("Starting synchronize %s int sentTrans to next server" % req.reqID)
			send(('SYNC', req), to = next)

	def receive(msg=("extendChain",newSrv), from_ = master):
		print("Received extendChain from master,setting my next to ",newSrv)
		self.next = newSrv
		


	def main():
		time.sleep(self.startup_delay)
		output('Server: Bank Name is: '+ str(self.bankName) + '  Server IP is: '+ str(self.serverIP) + '  Life time is: ' + str(self.life_time) + '  Previous server is: ' + str(self.prev) + '  Next server is: ' + str(self.next))
		ping = Ping(self.serverIP,self.bankName)
		while(True):
			if(await(False)):
				pass
			elif(timeout(1)):
				send(('PING', ping), to = self.master)



class Client(process):
	def setup(bankName,account_no,clientIP,input_req,ifRetrans,timeout,nRetrans,ifRandom,master,head_srvs,tail_srvs):
		self.bankName = int(bankName)
		self.account_no = account_no
		self.clientIP = clientIP
		self.requests = input_req
		self.ifRetrans = ifRetrans
		self.timeout = timeout
		self.nRetrans = nRetrans
		self.ifRandom = ifRandom
		self.master = master
		self.head_srvs = head_srvs
		self.tail_srvs = tail_srvs

	def init_req():
		reqList =[]
		client_id = self.id
		if ifRandom == True:
			input_str = input_req[0]
			strs = parse_randomReq(input_str)
			seed_num = strs[0]
			num_req = strs[1]
			prob_query = strs[2]
			prob_deposit = strs[3]
			prob_withdraw = strs[4]
			prob_transfer = strs[5]
			random.seed(seed_num)
			for i in range(num_req):
				a = random.randint(1, 100)
				a = float(a/100)
				amount = random.randint(1, 10) * 100
				if a < prob_query:
					reqtype = ReqType.Query
				elif a < (prob_query + prob_deposit):
					reqtype = ReqType.Deposit
				elif a < (prob_query + prob_deposit + prob_withdraw):
					reqtype = ReqType.Withdraw
				else:
					reqtype = ReqType.Transfer
				reqID = str(self.bankName) + '.'+ str(self.account_no[0]) + '.' + str(i+1)
				req = Request(reqID,reqtype,self.account_no,amount,client_id)
				output('Generating randomized request: '+ str(req))
				reqList.append(req)
		else:
			num_req = len(input_req)
			for i in range(num_req):
				strs = parse_req(input_req[i])
				if strs[0].startswith(str(self.bankName)) and int(strs[2]) == int(self.account_no):
					req = Request(strs[0], strs[1], strs[2], strs[3], client_id)
					reqList.append(req)
				else:
					pass
		return reqList

	def receive(msg=('REPLY', reply), from_= src_id):
		output('Reply received from server: '+ str(reply))

	def receive(msg=("newHead",newSrv),from_= master):
		print("CLIENT ",self.id, "CHANGING NEW HEAD: ",newSrv)
		self.head_srvs.update({self.bankName:newSrv})

	def receive(msg=("newTail",newSrv),from_= master):
		print("SETTING NEW TAIL: ",newSrv)
		self.tail_srvs.update({self.bankName:newSrv})

	def receive(msg=("srvFail",newSrv),from_= master):
		print("CLIENT RECEIVED SERVER FAIL, STARTING TO SLEEP")
		time.sleep(5)

	def resend(req, dst):
		for i in range(self.nRetrans):
			output("Start retransmitting Request ", req.reqID)
			time.sleep(1)
			clk = logical_clock()
			send(('REQ', req), to = dst)
			if await(some(received(('REPLY', reply),from_= dst,clk=rclk),has=(rclk>clk))):
				break
			elif timeout(self.timeout):
				output('waiting for reply TIMEDOUT!')
				continue
		output('Retransmit time equals the RetransLimit, stop retransmitting Request', req.reqID)

	def main():
		output('Client: Bank Name is: '+str(self.bankName)+ '  Account number is: '+ str(self.account_no))
		reqList = init_req()
		num_req = len(reqList)
		for i in range(num_req):
			req = reqList[i]
			if req.reqtype == ReqType.Query:
				dst = self.tail_srvs.get(self.bankName)
				print("DESTINATION the dst is",dst)		
			else:
				dst = self.head_srvs.get(self.bankName)
				print("DESTINATION the dst is",dst)
			output('Request ' + str(req.reqID) + ' has been sent out')
			time.sleep(2)
			clk = logical_clock()
			send(('REQ', req), to = dst)
			if await(some(received(('REPLY', reply),from_= dst,clk=rclk),has=(rclk>clk))):
				continue	
			elif timeout(self.timeout):
				output('waiting for reply TIMEDOUT!')
				resend(req, dst)

def main():
	srvDic = collections.defaultdict(list)
	cliDic = collections.defaultdict(list)
	waitList =[]
	head_srvs ={}
	tail_srvs ={}
	config(channel='fifo',handling='all',clock='Lamport')
	flag_srv =False
	flag_cli =False
	flag_req =False
	flag_config =False
	input_srv =[]
	input_cli =[]
	input_req =[]
	config_file = None
	if len(sys.argv) < 2:
		print('Please input config file!')
		sys.exit()
	else:
		config_file = sys.argv[1]
	fp = open(config_file,'r')
	for line in fp:
		if line.startswith('//Server'):
			flag_srv =True
			continue
		elif line.startswith('//Client '):
			flag_config =True
			input_str = fp.__next__()
			list_config = parse_config(input_str)
			continue
		elif line.startswith('//Client:'):
			flag_cli =True
			continue
		elif line.startswith('//Request'):
			flag_req =True
			continue
		elif flag_srv==True and flag_config==False:
			input_srv.append(line)
		elif flag_cli==True and flag_req==False:
			input_cli.append(line)
		elif flag_req==True and line!='\n':
			input_req.append(line)
		else:
			pass

	srvList =[]
	for string in input_srv:
		srv = parse_server(string)
		srvList.append(srv)

	num_srv = len(input_srv)
	servers = list(new(Server, num = num_srv))
	bankName_srv = []
	serverIP = []
	startup_delay = []
	life_time = []

	for i in range(num_srv):
		bankName_srv.append(srvList[i][0])
		serverIP.append(srvList[i][1])
		startup_delay.append(srvList[i][2])
		life_time.append(srvList[i][3])

	for i in range(num_srv):
		if i == 0 or bankName_srv[i]!= bankName_srv[i-1]:
			prev = None
		else:
			prev = servers[i-1]
		if i == num_srv - 1 or bankName_srv[i]!= bankName_srv[i+1]:
			next = None
		else:
			next = servers[i+1]
		if prev == None:
			head_srvs.update({bankName_srv[i]:servers[i]})
		elif next == None:
			tail_srvs.update({bankName_srv[i]:servers[i]})
		if startup_delay[i] == 0:
			srvDic[bankName_srv[i]].append([servers[i],prev,next,serverIP[i]])
		else:
			waitList.append([bankName_srv[i],servers[i],prev,next,serverIP[i]])


	cliList =[]
	for string in input_cli:
		cli = parse_client(string)
		cliList.append(cli)

	num_cli =len(input_cli)
	clients = list(new(Client, num = num_cli))
	bankName_cli =[]
	account_no =[]
	clientIP =[]
	ifRetrans = list_config[0]
	timeout = list_config[1]
	nRetrans = list_config[2]
	ifRandom = list_config[3]

	for i in range(num_cli):
		bankName_cli.append(cliList[i][0])
		account_no.append(cliList[i][1])
		clientIP.append(cliList[i][2])

	for i in range(num_cli):
		cliDic[bankName_cli[i]].append(clients[i])
	print(cliDic)

	#######################Initiate Master#################################
	filename_master = '/Users/fydeng/Desktop/Distalgo/master_log.txt'
	master = new(Master)
	setup(master,(srvDic, cliDic, filename_master, waitList))
	start(master)
	#######################################################################

	#######################Initiate Servers################################
	for i in range(num_srv):
		if i == 0 or bankName_srv[i]!= bankName_srv[i-1]:
			prev = None
		else:
			prev = servers[i-1]
		if i == num_srv - 1 or bankName_srv[i]!= bankName_srv[i+1]:
			next = None
		else:
			next = servers[i+1]
		setup(servers[i],(bankName_srv[i], serverIP[i], startup_delay[i], life_time[i], prev, next, master))
	
	start(servers)

	#######################Initiate Clients################################
	for i in range(num_cli):
		setup(clients[i], (bankName_cli[i], account_no[i], clientIP[i], input_req, ifRetrans, timeout, nRetrans, ifRandom, master,head_srvs,tail_srvs))

	start(clients)
	#######################################################################
	