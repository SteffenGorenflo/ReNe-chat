import socket               
import time
from threading import Thread

# global data
goon=True               # Threads stop if goon==0
debug=False             # falg for enabling debug information
debug=True

# local data
my_nick=''              # own nick name
my_port=0               # port of own socket
my_host='127.0.0.1'     # name of own host

# remote data
host_list=['127.0.0.1'] # list of hosts to scan
port_range=range(50000,50003)   # list of ports to scan

# messages with potential retransmissions
sent_chat_msg=dict()    # key: addr, value: (time, num_retry, to_nick, msg) 
sent_welcome_msg=dict() # key: addr, value: (time, tries, nick) 
sent_requests=dict()    # key: addr, value: (time, tries)

# buddy list
nick2host=dict()        # key: nickname, value: addr (IP, port)
host2nick=dict()        # key: addr (IP, port), value: nickname
last_buddy_update=dict()# key: nickname, value: last update

# constants for retransmissions
maxSendTries=3          # maximum number of time to try send a message

retry_timer_req=3       # requests
max_retries_req=3
retry_timer_welcome=3   # welcomes
max_retries_welcome=3
retry_timer_chat=3      # chats
max_retries_chat=3

# message prefixes
# key: {'w','r','ack w','ack c'}, value: message prefix
msg_pre=dict([('w',"welcome to the chat, I'm "),('r',"request to join by "),('ack w','ACK: welcome'),('ack c','ACK: chat')])

# little helper function, extracts nick from welcome message
def get_nick_from_welcome(msg):
    global msg_pre
    return msg[len(msg_pre['w']):]

# function adds a nick/addr pair to the buddy-lists, udates time stamp when existing
def add_to_buddy_list(nick, addr, t):
    global nick2host, host2nick, last_buddy_update

    pass # implement here

# function deletes a nick/addr pair from buddy lists
def delete_from_buddy_list(nick, addr):
    global nick2host, host2nick, last_buddy_update

    pass # implement here

# receive function
def my_receive(s):      # s i an open UDP socket
    global debug
    global goon, my_nick
    # main loop: repeat until program stops (goon==false)
    while goon:
        # read messages and call my_analyse
        # if debug: give also error messages for closed ports

        pass # implement here

# analyse function
def my_analyse(msg, addr):
    global debug
    global sent_welcome_msg

    if debug:
        print(time.time())
        print(': from '+addr[0]+'/'+str(addr[1])+':'+msg)


    # analyse the message
    if msg.startswith(msg_pre['w']):    # welcome message
        pass # implement here

    elif msg.startswith('ACK: welcome'):    # ACK to welcome message
        pass # implement here

    elif msg.startswith('From'):    # chat message
        pass # implement here

    elif msg.startswith('ACK: chat'):   # ACK to chat message
        pass # implement here
    
    elif msg.startswith('request to join by'):  # request message
        pass # implement here

    else:
        print('received a message with unknown format')
        print(msg)

# scanning ports
def my_scan():
    global my_nick, my_host, my_port, host_list, port_range
    global msg_pre
    print('Scanning ports\n')

    pass # implement here


def send_message(s, msg, addr):
    global maxSendTries
    k=0
    while k<maxSendTries:
        try:
            s.sendto(msg.encode('utf-8'),addr)
        except socket.error as e:
            print(e)
            k+=1
        if k==maxSendTries:
            print('Error: could not sent request message, maximum number of tries exceeded')
            return False
        else:
            return True,time.time()
            

# retransmission function
def my_retransmit(s):
    global my_nick
    global msg_pre
    global goon
    global sent_requests, sent_chat_msg, sent_welcome_msg
    global retry_timer_req, max_retries_req
    global retry_timer_welcome, max_retries_welcome
    global retry_timer_chat, max_retries_chat
                           
    while goon:

        ###### check for request timeouts

        # to delete requests, store the "addr" in del_addr
        del_addr=[]

        t=time.time()   # get the current time
        for addr,status in sent_requests.items():
            pass # implement here

        # delete requests with addr in del_addr
        for addr in del_addr:
            del sent_requests[addr]


        ###### check for welcome timeouts
        
        del_addr=[]
        t=time.time()
        for addr,status in sent_welcome_msg.items():
            pass # implement here
        
        for addr in del_addr:
            del sent_welcome_msg[addr]

        ###### check for chat timeouts

        del_addr=[]
        t=time.time()
        for addr,status in sent_chat_msg.items():
            pass # implement here
                    
        for addr in del_addr:
            del sent_chat_msg[addr]

        ##### check again after 1s
        time.sleep(1)


def my_list():
    print('My buddy list:')
    for nick, addr in nick2host.items():
        print('Nick: '+nick+' at '+addr2str(addr)+'\n')
    
def my_chat():
    global my_nick, sent_chat_msg, nick2host
    print('Enter chat message:'+'\n')
    to_nick=input('To? ')
    if to_nick=='All':
        pass # implement here
        # only continue if there are no outstanding ACKs for any chat message
    else:
        pass # implement here
        # only continue if there are no outstanding ACKs for the recipient

def my_quit():
    global goon
    print('Quitting!!!')
    goon=0
    

def my_input():
    global action
    time.sleep(1)
    action=input('Enter Action (<S>, <L>, <C>, <Q>)\n')
    actions[action]()


# main program
actions = {'S' : my_scan, 'L' : my_list,'C' : my_chat,'Q' : my_quit }

my_nick=input('Enter your nickname:')
print('Starting the Chat Client')
my_port=int(eval(input('Enter port number:')))
print('Opening socket on port '+str(my_port))

pass # implement: open socket

pass # implement: start receive and retransmit threads
zzz=Thread(target=yyy,args=(aaa,))
zzz.start()

# main loop waiting for input
while goon:
    t_in=Thread(target=my_input)
    t_in.start()
    t_in.join()


            

      
