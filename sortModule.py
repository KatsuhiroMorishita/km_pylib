#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      morishita
#
# Created:     05/09/2012
# Copyright:   (c) morishita 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

class AttrCmp:
    def __init__(self, attr):
        self.attr=attr

    def __call__(self,x,y):
        return cmp(getattr(x,self.attr),getattr(y,self.attr))


class Item:

    def __init__(self, name, number):
        self.name = name
        self.number = number

    def __repr__(self):
        return "Item(%s, %d)" % (self.name, self.number)

def main():
    pass

if __name__ == '__main__':
    main()
