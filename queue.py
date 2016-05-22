class queue:
    def __init__(self):
        self.data={}
        self.queue =[]
    def push(self,data):
        self.queue.append(data)
    def pop(self):
        if self.queue !=[]:
                return self.queue.pop()
        else:
                return None
    def head(self):
        if self.queue !=[]:
            return self.queue[0]
        else:
            return None
    def tail(self):
        if self.queue !=[]:
            return self.queue[-1]
        else:
            return None
    def length(self):
        return len(self.queue)

    def isempty(self):
        return self.queue == []
