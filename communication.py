from collections import deque

class Communication:
    def __init__(self, monitor):
        self.monitor = monitor      # monitoring system object
        self.__outbox = deque()
        self.miss = 0

    def __send(self, message):
        # save message to outbox
        self.__outbox.append(message)

        # try to deliver all messages (new + any backlog)
        while self.__outbox:
            oldest = self.__outbox[0]

            while(self.miss < MISS):
                try:
                    # try to send oldest message
                    acknowledged = self.monitor.send(oldest) 
                except Exception:
                    acknowledged = False

                if acknowledged:
                    self.miss = 0
                    break
                
                self.miss += 1               

            # if message failed MISS (3) times means that system is offline and try again later    
            if self.miss >= MISS:
                print("ON SCREEN: Monitoring system offline.")  # printed message only for testing
                self.miss = 0
                break

            # if acknowledgment was received then delete oldest element in outbox and send rest of messages
            self.__outbox.popleft()     
                    

    def send_to_communicator(self, source, message):
        self.__send(source + ": " + message)