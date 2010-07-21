# -*- coding: utf-8 -*-

from pyExcelerator import XFStyle, Style

def get_private_attr(obj, name):
    return getattr(obj, '_%s__%s' % (obj.__class__.__name__, name))

def set_private_attr(obj, name, value):
    return setattr(obj, '_%s__%s' % (obj.__class__.__name__, name), value)

def get_style(style_col, xf_index):
    '''
    Возвращает копию стиля по его индексу в коллекции стилей
    '''
    newstyle = XFStyle()
   
    def find_key(map, value):
        for k, v in map.items():
            if v == value:
                return k
            
        return None
        
    font_idx, num_format_idx, alignment, borders, pattern, protection = find_key(style_col._xf, xf_index)

    newstyle.num_format_str  = find_key(style_col._num_formats, num_format_idx)
    newstyle.font            = find_key(style_col._fonts, font_idx).copy()
    newstyle.alignment       = alignment.copy()
    newstyle.borders         = borders.copy()
    newstyle.pattern         = pattern.copy()
    newstyle.protection      = protection.copy()
    
    return newstyle

def get_cell_style(sh, style_col, r, c):
    '''
    Возвращает копию стиля ячейки
    '''
    row_cells = get_private_attr(sh.row(r), 'cells') 
    for cell in reversed(row_cells):
        if get_private_attr(cell, 'idx') == c:
            xf_idx = get_private_attr(cell, 'xf_idx')
            return get_style(style_col, xf_idx)
        
    return XFStyle()
        
def set_cell_style(sh, style_col, r, c, style):
    '''
    Устанавливает стиль для ячейки
    '''
    row_cells = get_private_attr(sh.row(r), 'cells')

    founded = False
    for cell in reversed(row_cells):
        if get_private_attr(cell, 'idx') == c:
            xf_idx = style_col.add(style)
            set_private_attr(cell, 'xf_idx', xf_idx)
            founded = True
            break

    if not founded:
        sh.write(r, c, style=style)

class Range(object):
    def __init__(self, sheet, r1, r2, c1, c2):
        self.sheet = sheet
        self.r1 = r1
        self.r2 = r2
        self.c1 = c1
        self.c2 = c2

        self.style_col = get_private_attr(sheet.get_parent(), 'styles')
        
    def set_borders(self, inwidth=1, outwidth=2):
        for r in range(self.r1, self.r2 + 1):
            for c in range(self.c1, self.c2 + 1):
                style = get_cell_style(self.sheet, self.style_col, r, c)
                
                style.borders.top = outwidth if r == self.r1 else inwidth
                style.borders.bottom = outwidth if r == self.r2 else inwidth
                style.borders.left = outwidth if c == self.c1 else inwidth
                style.borders.right = outwidth if c == self.c2 else inwidth
                
                set_cell_style(self.sheet, self.style_col, r, c, style)
                
    def __set_format(self, format):
        for r in range(self.r1, self.r2 + 1):
            for c in range(self.c1, self.c2 + 1):
                style = get_cell_style(self.sheet, self.style_col, r, c)
                style.num_format_str = format
                set_cell_style(self.sheet, self.style_col, r, c, style)

    format = property(fset=__set_format)                
                
                
class Cell(object):
    def __init__(self, sheet, r, c):
        self.sheet = sheet
        self.r = r
        self.c = c
        self.style_col = get_private_attr(sheet.get_parent(), 'styles')
        
    def set_borders(self, width=2):
        style = self.style
        
        style.borders.top = width
        style.borders.bottom = width
        style.borders.left = width
        style.borders.right = width
        
        self.style = style
    
    def __set_format(self, format):
        style = get_cell_style(self.sheet, self.style_col, self.r, self.c)
        style.num_format_str = format
        set_cell_style(self.sheet, self.style_col, self.r, self.c, style)

    format = property(fset=__set_format)
    
    def __get_style(self):
        return get_cell_style(self.sheet, self.style_col, self.r, self.c)
    
    def __set_style(self, style):
        set_cell_style(self.sheet, self.style_col, self.r, self.c, style)
        
    style = property(__get_style, __set_style)
    
def set_style_for_book(book, format=None, alignment=None):
    style_col = get_private_attr(book, 'styles')
    
    data = {}
    for xf, xf_index in style_col._xf.items():
        font_idx, num_format_idx, old_alignment, borders, pattern, protection = xf
        if format:
            if format in style_col._num_formats:
                new_format_idx = style_col._num_formats[format]
            else:
                new_format_idx = 163 + len(style_col._num_formats) - len(Style.StyleCollection._std_num_fmt_list)
                style_col._num_formats[format] = new_format_idx
        else:
            new_format_idx = num_format_idx
        
        new_alignment = alignment if alignment else old_alignment
        
        new_xf = (font_idx, new_format_idx, new_alignment, borders, pattern, protection)
        data[new_xf] = xf_index
        
    style_col._xf = data