'''
English-Dutch auction simulation for selling train tickets 
'''
from threading import Lock, Thread
from multiprocessing.pool import ThreadPool
import time
import calendar
import random

bidders = {}
param = {}                                      #dict to store parameters 
class auction:
   lock = Lock()                                #lock,price & winner are static var accessible by all methods(threads)
   price = 0                                   #initial price       
   winner = {'id':-1,'price':0 }
   reservePrice=0

   def english_auctioneer(self,id,perChange):           #returns 1 when winner found else 0
      global bidders
      flag=0
      for key in bidders:                           
        if bidders[key]['price'] !=0:                    
            flag=1                              #flag=1 => continue raising price
      if flag:                                 #msgs not empty
        if auction.price == param['initial_price']:                #start of auction 
            print("auctioneer",id," says ", auction.price)
        else:
            auction.lock.acquire()
            auction.price += auction.price*perChange        #auctioneer changing price
            auction.lock.release()
            print("auctioneer",id," says ", auction.price)
        return 0
      else:                                        #msgs empty
         return 1
         
      

   def english_bidder(self,id,myHighest,perChange):
      global bidders
      if auction.price < myHighest:                                  #can bid
         if (auction.price+ auction.price*perChange) <= myHighest:
            auction.lock.acquire()
            auction.price += auction.price*perChange
            auction.winner.update({'id':id,'price':auction.price})
            auction.lock.release()
            
         else:
            auction.lock.acquire()
            auction.price = myHighest
            auction.winner.update({'id':id,'price':auction.price})
            auction.lock.release()
         bidders[id]['price']=auction.price
         
      else:
         bidders[id]['price'] = 0                           #bidder outbid
      print("bidder",id,"says",bidders[id]['price'])
      return

   def dutch_auctioneer(self,id,perChange):           #returns 1 when winner found or auction ends, else 0
      global bidders
      flag=0
      if auction.price < auction.reservePrice:  #end auction
         return 1
      else:
         for key in bidders:
            if bidders[key]['price'] !=0:                 #flag=1 => found winner
               flag=1
         
         if flag==0:                
            auction.lock.acquire()
            auction.price -= auction.price*perChange        #auctioneer changing price
            auction.lock.release()
            print("auctioneer",id," says ", auction.price)
            return 0
         else:
            print("From the bidders: ",bidders)                            #declare winner
            print("Winner is ", auction.winner['id']," with bid ",auction.winner['price'])                     
            return 1

      

   def dutch_bidder(self,id,myHighest,perChange):
      global bidders
      if auction.price <= myHighest:                                  #can bid
         auction.winner.update({'id':id,'price':auction.price})
         bidders[id]['price']=auction.price
         
      else:
         bidders[id]['price'] = 0                           #bidder outbid
      print("bidder",id,"says",bidders[id]['price'])
      return

      

if __name__ == '__main__':

   #import parameters into dict from config file
   with open("config.txt") as fp:   
      for line in fp:
         b = line.split(" ")
         param[b[0]]=float(b[1].rstrip())
   fp.close()

   #populate variables
   threads = []
   a =auction()
   nBid=param['no_of_bidders']
   nAuc=1
   auction.reservePrice = param['reserve_price']
   auction.price = param['initial_price']
   eng_perc = param['eng_perc']
   dutch_perc = param['dutch_perc']
   n=param['n']               #tick_threshold

   #time-date settings
   #ticks=time.time()			#ticks for today’s date
   start_date = (2018, 12, 13, 8, 44, 4, calendar.weekday(2018,12,13), 347, 0)	
   travel_date = (2018, 12, 28, 8, 44, 4, 4, 362, 0)	#date of travel   # calendar.weekday(year, month, day)
   start_ticks=time.mktime(start_date)
   travel_ticks=time.mktime(travel_date)		#ticks for date of travel
   print("Ticks left till travel: ",travel_ticks-start_ticks)

   #start of English auction
   flag=0
   end_english=0
   print("Auction Type: English")
   print("auctioneer",0," says ", auction.price)
   
   for i in range(int(nBid)):                                    #initialise bidders 
      bidders[i]= {'highest':(random.randint(10,10*nBid+1)),'perc':(random.randint(0,11)/10),'price':0}
   print("bidders are : ",bidders)

   while(end_english!=1): 

      if(end_english!=1):
         for i in range(int(nBid)):                                    #bidder threads
               threads.append(Thread(target=a.english_bidder,args=(i,bidders[i]['highest'],bidders[i]['perc'])))
               threads[-1].start()
               time.sleep(1)
      start_ticks+=86400*3
      pool = ThreadPool(processes=1)                              #auctioneer thread that returns value
      async_result = pool.apply_async(a.english_auctioneer, (0,eng_perc)) 
      time.sleep(1)
      end_english = async_result.get()
   print("Ticks left: ",travel_ticks-start_ticks," Hurry!!")
   while((travel_ticks-start_ticks)>(86400*n)):
      print("waiting")
      time.sleep(1)
      start_ticks+=86400

   #start of Dutch auction
   end_dutch=0
   print("Auction Type: Dutch")
   print("auctioneer",0," says ", auction.price)
   for i in range(int(nBid)):                                    #reinitialise bidders for dutch 
      bidders[i].update({'highest':(random.randint(10,10*nBid+1)),'perc':(random.randint(0,11)/10),'price':0})
   print("bidders are : ",bidders)
   while(end_dutch!=1): 

      if(end_dutch!=1):
         for i in range(int(nBid)):                                    #bidder threads
               threads.append(Thread(target=a.dutch_bidder,args=(i,bidders[i]['highest'],bidders[i]['perc'])))
               threads[-1].start()
               time.sleep(1)

      pool = ThreadPool(processes=1)                              #auctioneer thread that returns value
      async_result = pool.apply_async(a.dutch_auctioneer, (0,dutch_perc)) 
      time.sleep(1)
      end_dutch = async_result.get()

   for thread in threads:              #Waits for threads to complete before moving on with the main script
      thread.join()

