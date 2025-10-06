import curses

def build_menu(window,elements,selected,border=0,row_cen=0,col_cen=0,row_off=0,col_off=0):
    for x in range(len(elements)):
        row = 0
        col = 0
        if row_cen == 1:
            _,max_col = window.getmaxyx()
            col = (max_col-len(elements[x]))//2
        else:
            col = 0 + col_off
        if col_cen == 1:
            max_row,_ = window.getmaxyx()
            row = (x+1)*((max_row-len(elements))//len(elements))
        else:
            row = x + row_off
        if x == selected:
            window.addstr(row,col,elements[x],curses.A_STANDOUT)
        else:
            window.addstr(row,col,elements[x])
    pass
