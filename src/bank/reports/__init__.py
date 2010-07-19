from pyExcelerator import XFStyle

def get_border_style(r1, r2, c1, c2, r, c, inwidth, outwidth, cache={}):
    istop = r == r1
    isbottom = r == r2
    isleft = c == c1
    isright = c == c2
    
    key = (istop, isbottom, isleft, isright)
    
    if not key in cache:
        style = XFStyle()
        style.borders.top = outwidth if istop else inwidth
        style.borders.bottom = outwidth if isbottom else inwidth
        style.borders.right = outwidth if isright else inwidth
        style.borders.left = outwidth if isleft else inwidth
        
        cache[key] = style
    
    return cache[key]

def set_borders(sh, r1, r2, c1, c2, inwidth=1, outwidth=2):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 +1):
            sh.write(r,c, style=get_border_style(r1, r2, c1, c2, r, c, inwidth, outwidth))