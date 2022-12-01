
def FindSubstr(str,substr,endstr=None,start=None,end=None):
    if endstr is None:
        endstr = '\n'
    sub1 = str[str.find(substr):]
    sub2 = sub1[len(substr):sub1.find(endstr)]
    return sub2
    # return str[str.find(substr)+len(substr):str[str.find(substr)+len(substr):].find('\n')]
