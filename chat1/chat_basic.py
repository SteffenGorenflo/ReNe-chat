import socket               
import time
from threading import Thread

# global data
goon=True               # Threads stop if goon==0
debug=False           # flag for enabling debug information


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
general_tries=3

sock=''

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


    nick2host[nick] =addr
    host2nick[addr] =nick 
    
    #TODO timestamp, maybe:
    last_buddy_update[nick] =t


    

# function deletes a nick/addr pair from buddy lists
def delete_from_buddy_list(nick, addr):
    global nick2host, host2nick, last_buddy_update


    del nick2host[nick]
    del host2nick[addr]

    #TODO timestamp, maybe:
    del last_buddy_update[nick]


    

# receive function
def my_receive(s):      # s is an open UDP socket
    global debug
    global goon, my_nick
    # main loop: repeat until program stops (goon==false)
    while goon:
        # read messages and call my_analyse
        # if debug: give also error messages for closed ports
        try:
            data, addr = s.recvfrom(1024) # buffer size is 1024 bytes
            my_analyse(data.decode('utf-8'), addr,s)

            pass
        except socket.error as serr:
            if debug:
                pass
                #print(time.time())
                #print("not reachable: " + str(s) + " because of: " + str(serr))
        else:
            pass
        finally:
            pass
        

# analyse function
def my_analyse(msg, addr,s):
    global debug
    global sent_welcome_msg
    global sent_chat_msg
    global msg_pre
    global my_nick

    if debug:
        print(': from '+addr[0]+'/'+str(addr[1])+':'+msg)


    # analyse the message
    if msg.startswith(msg_pre['w']):    # welcome message
        add_to_buddy_list(get_nick_from_welcome(msg), addr, time.time())
        send_message(s,msg_pre['ack w'],addr) 

    elif msg.startswith('ACK: welcome'):    # ACK to welcome message
        del sent_welcome_msg[addr]

    elif msg.startswith('From'):    # chat message
        print(str(msg))
        send_message(s,msg_pre['ack c'],addr)

    elif msg.startswith('ACK: chat'):   # ACK to chat message
        del sent_chat_msg[addr]
    
    elif msg.startswith('request to join by'):  # request message
        send_message(s,msg_pre['w'] + my_nick,addr)
               
        sent_welcome_msg[addr] = (time.time() ,0 , get_nick_from_welcome(msg) )

    else:
        print('received a message with unknown format')
        print(msg)

# scanning ports
def my_scan():
    global sock
    global my_nick, my_host, my_port, host_list, port_range
    global msg_pre
    global sent_requests
    print('Scanning ports\n')

    for ip in host_list:
        for port in port_range:
            send_message(sock,'request to join by '  + my_nick, (ip,port))
            # key: addr, value: (time, tries)
            sent_requests[(ip,port)] = (time.time(),0)



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
    return
    global my_nick
    global msg_pre
    global goon
    global sent_requests, sent_chat_msg, sent_welcome_msg
    global retry_timer_req, max_retries_req
    global retry_timer_welcome, max_retries_welcome
    global retry_timer_chat, max_retries_chat
                           
    while goon:

        ###### check for request timeouts

        t=time.time()   # get the current time
        for addr,status in sent_requests.items():
            count = status[1] + 1
            if (count > general_tries):
                print ("timeout of request: " + str(sent_requests[addr]))
                del sent_requests[addr]
            else:
                send_message(s, msg_pre['r'] + my_nick, addr)
                sent_requests[addr] = (t,count)


        ###### check for welcome timeouts

        t=time.time()
        for addr,status in sent_welcome_msg.items():
            count = status[1] + 1
            if (count > general_tries):
                print ("timeout of welcome message: " + str(sent_welcome_msg[addr]))
                del sent_welcome_msg[addr]
            else:
                send_message(s, msg_pre['w'] + my_nick, addr)
                sent_welcome_msg[addr] = (t,count,my_nick)


        ###### check for chat messages timeouts

        t=time.time()
        for addr,status in sent_chat_msg.items():
            count = status[1] + 1
            if (count > general_tries):
                print ("timeout of chat message: " + str(sent_chat_msg[addr]))
                del sent_chat_msg[addr]
            else:
                send_message(s, status[3], addr)
                sent_chat_msg[addr] = (t,count,my_nick)
    

        ##### check again after 3s
        time.sleep(3)


def my_list():
    print('My buddy list:')
    for nick, addr in nick2host.items():
        print('Nick: '+nick+' at '+ str(addr)+'\n')
    
def my_chat():
    global my_nick, sent_chat_msg, nick2host
    global sock
    print('Enter chat message:'+'\n')
    to_nick=input('To? ')
    message = "From " + my_nick + ": " + input('message? ')

    if to_nick=='All':
        for nick, addr in nick2host.items():
            send_message(sock,message,nick2host[nick])
            # key: addr, value: (time, num_retry, to_nick, msg) 
            sent_chat_msg[addr] = (time.time(), 0 , nick, message)

    else:
        send_message(sock,message,nick2host[to_nick])
        sent_chat_msg[nick2host[to_nick]] = (time.time(), 0 , to_nick, message)

    

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

sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((my_host,my_port))
sock.settimeout(1)

pass # implement: start receive and retransmit threads
zzz=Thread(target=my_receive,args=(sock,))
zzz.start()

xxx=Thread(target=my_retransmit,args=(sock,))
xxx.start()

# main loop waiting for input
while goon:
    t_in=Thread(target=my_input)
    t_in.start()
    t_in.join()


zzz.join()
xxx.join()


            

      
