from collections import OrderedDict, namedtuple
from itertools import product

class Grid:

    def __init__(self, **kwargs) -> None:
        self.gdict = OrderedDict(**kwargs)
        self.vars = list(self.gdict.keys())
        self.values = []
        for val in self.gdict.values():
            if not isinstance(val, (list, tuple)):
                raise TypeError('Each parameter set must be denoted by a list/tuple')
            
            self.values.append(val)
        
        self.combs = list(product(*self.values))
        
        self.combination = namedtuple('Combination', self.vars)
    
    def __iter__(self):
        self.i = -1
        return self
    
    def __next__(self):
        if self.i < len(self.combs) - 1:
            self.i += 1
            return self.combination(*self.combs[self.i])
        else:
            raise StopIteration()


if __name__ == '__main__':
    for (lr, bs, hid) in Grid(lr=[1e-2, 1e-3, 1e-4], batch_size=[32, 64], hidden_size=[96]):
        print(lr, bs, hid)