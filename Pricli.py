## This is, what i hope to be, a wrapper class for ncurses python library
## which is a wrapper for the C library...
## The goal is to simplify the process of working with the curses library,
## without throwing any curses (hopefully).
## I present: Print Cli (Pricli)

import curses
from curses import wrapper
from textwrap import wrap
import time
import random
from threading import Lock

test_string = "ddd6989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891698916989169891ddddddd"
test_list = ["Giorgos",'\t',"Halios"]
colors = [curses.COLOR_GREEN, curses.A_NORMAL, curses.COLOR_RED]


class Line:
    def __init__(self,pricli,line,colors=None):
        self.line = line
        self.colors = None
        self.pricli = pricli
        if colors is None:
            self.colors = [curses.A_NORMAL]*len(self.line)
        else:
            self.colors = colors


    def PrintLine(self,row=None,col=None):
        # if row is None:
            # row = self.pricli.GetCur()
        # if col is None:
            # col = self.pricli.GetPos()
        current_pos = self.pricli.GetPos()
        for index in range(0,len(self.line)):
            color = self.pricli.normal_color
            if self.colors[index] is not None:
                color = self.colors[index]
            self.pricli.Print(self.line[index],color,row,col)
            # self.pricli.Print('Page: '+str(self.pricli.current_view_page_index)+"/"+str(len(self.pricli.pages)),curses.A_NORMAL,1,100)
            self.pricli.screen.addstr(1,100,'Page: '+str(self.pricli.current_view_page_index+1)+"/"+str(len(self.pricli.pages)))
            # self.pricli.screen.addstr(1,100,str(len(self.pricli.pages[self.pricli.current_page_index].lines))) #### UNCOMMENT THESE LINES FOR DEBUGING
            self.pricli.screen.refresh()
        self.pricli.UpdateCur()
        self.pricli.Refresh()
        self.pricli.ChangePos(current_pos)




class Page: #### represents a screen page as seen by the human eye
    def __init__(self,pricli):
        self.lines = []
        self.current_line = 0
        self.pricli = pricli
        self.current_selected_line = -1
    
    def GetLines(self):
        return self.lines
    
    def InsertLine(self,line,colors):
        self.lines.append(Line(self.pricli,line,colors))
        self.current_line += 1
    
    def PrintPage(self):
        # self.pricli.ChangeCur(self.pricli.GetTop())
        for line in self.lines:
            line.PrintLine()
        self.pricli.Init()

    def Clear(self):
        for line in self.lines:
            del line
            self.lines.clear()



    #### An Info Window looks like: 
    # ****************
    # * Title        *
    # ****************
    # * Line1        *
    # * Line2        *
    # * Line3        *
    # * Line4        *
    # ****************
class InfoWindow:
    def __init__(self,pricli,title,lines,colors,border_color = curses.COLOR_RED):
        self.pricli = pricli
        self.title = title
        self.lines = lines
        self.colors = colors
        self.lines_to_draw = []
        self.colors_to_draw = []
        self.border_color = border_color 

        max_width = 0
        for line in lines:
            txt = ''
            for l in line:
                txt += l
            length = len(txt)
            if '\t' in txt:
                length += 8
            if length > max_width:
                max_width = len(txt)

        self.max_width = max_width

        #### Create the drawable window
        self.lines_to_draw.append(['*'*(self.max_width+2)])
        self.colors_to_draw.append([self.border_color])
        # colors = []
        # self.title.insert(0,'*')
        self.title.insert(0,'*')
        self.title[1] = self.CenterText(self.title[1])
        self.title.append(self.CreateTrailingText(self.title))
        self.lines_to_draw.append(self.title)
        title_colors = self.colors[0]
        title_colors.insert(0,self.border_color)
        title_colors.append(self.border_color)
        self.colors_to_draw.append(title_colors)

        self.lines_to_draw.append(['*'*(self.max_width+2)])
        self.colors_to_draw.append([self.border_color])

        for line_index  in range(0,len(self.lines)):
            line = self.lines[line_index]
            col = self.colors[line_index+1]
            line.insert(0,'*')
            line.append(self.CreateTrailingText(line))
            col.insert(0,self.border_color)
            col.append(self.border_color)

            self.lines_to_draw.append(line)
            self.colors_to_draw.append(col)

        self.lines_to_draw.append(['*'*(self.max_width+2)])
        self.colors_to_draw.append([self.border_color])

    
    def CreateTrailingText(self,line):
        txt = ''
        for l in line:
            txt += l
        spaces = (self.max_width - len(txt) + 1)*' '
        return spaces + '*'
    
    def CenterText(self,text):
        spaces = 0
        while spaces + int(len(text)/2) < int(self.max_width/2):
            spaces += 1
        return spaces*' '+text

    def HasIndex(self,index):
        if index >= len(self.lines_to_draw):
            return False
        return True
        
    def DrawWindow(self,pricli): 
        top_row = pricli.GetCur()
        if pricli.GetPos() + self.max_width + 2 < pricli.screen_cols:
            for line_index in range(0,len(self.lines_to_draw)):
                line = self.lines_to_draw[line_index]
                colors = self.colors_to_draw[line_index]
                pricli.UpdatePage(line,colors)
            pricli.ChangePos(self.max_width + 2)
            pricli.ChangeCur(top_row)
            return True
        return False
        


class ControlPanel:
    def __init__(self,pricli,banner_text,subtitle,subtitle_colors):
        self.banner_text = banner_text
        self.control_keys = dict()
        self.control_keys_lines = []
        self.top_seperator1 = '='*(pricli.screen_cols - 2)
        self.top_seperator2 = '|'*(pricli.screen_cols - 2)
        self.top_seperator3 = '='*(pricli.screen_cols - 2)
        self.subtitle = subtitle
        self.subtitle_colors = subtitle_colors
        self.info_windows = []
        self.progress_line = 0

        # self.window_title_colors = 
        # [pricli.normal_color,pricli.BLUE,pricli.normal_color,pricli.RED,pricli.normal_color]

        self.pricli = pricli
        self.control_keys['q'] = 'Quit'
        self.control_keys['k'] = 'Previous Page'
        self.control_keys['l'] = 'Next Page'

    def PrintBanner(self):
        # self.pricli.Clear()
        # self.pricli.Init()
        # self.pricli.Refuresh()
        self.pricli.ClearPages()
        text = """
░██████╗░█████╗░░█████╗░███╗░░██╗██╗░░░░░░█████╗░██████╗░
██╔════╝██╔══██╗██╔══██╗████╗░██║██║░░░░░██╔══██╗██╔══██╗
╚█████╗░██║░░╚═╝███████║██╔██╗██║██║░░░░░███████║██████╦╝
░╚═══██╗██║░░██╗██╔══██║██║╚████║██║░░░░░██╔══██║██╔══██╗
██████╔╝╚█████╔╝██║░░██║██║░╚███║███████╗██║░░██║██████╦╝
╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚══╝╚══════╝╚═╝░░╚═╝╚═════╝░ """


        b1 ='░██████╗░█████╗░░█████╗░███╗░░██╗██╗░░░░░░█████╗░██████╗░'
        b2 ='██╔════╝██╔══██╗██╔══██╗████╗░██║██║░░░░░██╔══██╗██╔══██╗'
        b3 ='╚█████╗░██║░░╚═╝███████║██╔██╗██║██║░░░░░███████║██████╦╝'
        b4 ='░╚═══██╗██║░░██╗██╔══██║██║╚████║██║░░░░░██╔══██║██╔══██╗'
        b5 ='██████╔╝╚█████╔╝██║░░██║██║░╚███║███████╗██║░░██║██████╦╝'
        b6 ='╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚══╝╚══════╝╚═╝░░╚═╝╚═════╝░'
        self.pricli.UpdatePage([b1]) # Title for this menu
        self.pricli.UpdatePage([b2]) # Title for this menu
        self.pricli.UpdatePage([b3]) # Title for this menu
        self.pricli.UpdatePage([b4]) # Title for this menu
        self.pricli.UpdatePage([b5]) # Title for this menu
        self.pricli.UpdatePage([b6]) # Title for this menu
        # self.pricli.UpdateCur(text.count('\n'))
        # self.pricli.UpdatePage([title]) #Subtitle for this menu
    
    def InsertWindow(self,window):
        self.info_windows.append(window)
    
    def Draw(self):
        self.PrintBanner()
        # key_colors = []
        # key_colors.append(self.pricli.MAGENTA)
        # key_colors.append(self.pricli.CYAN)
        self.pricli.UpdatePage(['\n'])
        self.pricli.UpdatePage(['-'*self.pricli.screen_cols])
        line = '|'
        for key in self.control_keys.keys():
            key_pair_string = key+": "+self.control_keys[key]+" "
            if len(key_pair_string) + len(line) > self.pricli.screen_cols:
                self.control_keys_lines.append(line)
                line = ''
            line += key_pair_string
        line += '|'
        self.control_keys_lines.append(line)
        # self.pricli.UpdatePage(['\n'])
        for line in self.control_keys_lines:
            self.pricli.UpdatePage(line)
        self.pricli.UpdatePage(['-'*self.pricli.screen_cols])
        
        self.pricli.UpdatePage(['\n'])
        self.pricli.UpdatePage([self.top_seperator1],[self.pricli.RED])
        self.progress_line = self.pricli.GetCur()
        self.pricli.UpdatePage([self.top_seperator2],[self.pricli.GREEN])
        self.pricli.UpdatePage([self.top_seperator3],[self.pricli.RED])
        self.pricli.UpdatePage(['\n'])
        self.pricli.UpdatePage(self.subtitle,self.subtitle_colors)
        self.pricli.UpdatePage(['\n'])
        
        if len(self.info_windows) == 1:
            self.info_windows[0].DrawWindow(self.pricli)
        else:
            self.DrawInfoWindows()
        
        self.pricli.RefreshPage()


    def DrawInfoWindows(self):
        max_width = 0
        max_lines = 0
        for w in self.info_windows:
            if w.max_width < max_width:
                max_width = w.max_width
            if len(w.lines_to_draw) > max_lines:
                max_lines = len(w.lines_to_draw)

        for line_index in range(max_lines):
            line = []
            colors = []
            for w in self.info_windows:
                if w.HasIndex(line_index):
                    line += w.lines_to_draw[line_index]
                    colors += w.colors_to_draw[line_index]
                else:
                    line += [' '*(w.max_width+2)]
                    colors += [self.pricli.normal_color]
                line += [' '*2]
                colors += [self.pricli.normal_color]
            self.pricli.UpdatePage(line,colors)

    def AddControlKey(self,key,value):
        self.control_keys[key] = value

class ChoiceMenu:
    def __init__(self,pricli):
        self.pricli = pricli
        self.choice = 1
        self.pos = 1
        self.key_pressed = None
    
    def Init(self):
        self.choice = 1
        self.pos = 1
        self.key_pressed = None
    
    


    def Menu(self,title,choices):
        self.Init()
        # Loop until return key is pressed
        while self.key_pressed !=ord('\n'):
        # pricli.screen.clear() #clears previous screen on key press and updates display based on pos
        # pricli.screen.border(0)
            self.pricli.Clear()
            text = """
░██████╗░█████╗░░█████╗░███╗░░██╗██╗░░░░░░█████╗░██████╗░
██╔════╝██╔══██╗██╔══██╗████╗░██║██║░░░░░██╔══██╗██╔══██╗
╚█████╗░██║░░╚═╝███████║██╔██╗██║██║░░░░░███████║██████╦╝
░╚═══██╗██║░░██╗██╔══██║██║╚████║██║░░░░░██╔══██║██╔══██╗
██████╔╝╚█████╔╝██║░░██║██║░╚███║███████╗██║░░██║██████╦╝
╚═════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚══╝╚══════╝╚═╝░░╚═╝╚═════╝░ """

            self.pricli.Printblnr(text,2,1) # Title for this menu
            self.pricli.Printblnr(title,11,2) #Subtitle for this menu

            # Detects what is higlighted, every entry will have two lines, a condition if the menu is highlighted and a condition for if the menu is not highlighted
            # to add additional menu options, just add a new if pos==(next available number) and a correspoonding else
            # I keep exit as the last option in this menu, if you do the same make sure to update its position here and the corresponding entry in the main program
            self.pricli.AddTab()
            for pos in range(1,len(choices)+1):
                if self.pos == pos:
                    self.pricli.Printhlnr(str(pos) + " - "+choices[pos-1])
                else:
                    self.pricli.Printlnr(str(pos) + " - "+choices[pos-1])
            self.key_pressed = self.pricli.Input() # Gets user input
            

            # What is user input? This needs to be updated on changed equal to teh total number of entries in the menu
            # Users can hit a number or use the arrow keys make sure to update this when you add more entries
            # for choice in range(1,len(choices)+1):
                # if self.key_pressed == ord(str(choice)):
                    # self.pos = int(choice)
            
            if self.key_pressed == 258: ## down arrow
                if self.pos < len(choices):
                    self.pos += 1
                else: self.pos = 1
            elif self.key_pressed == 259: ## up arrow
                if self.pos > 1:
                    self.pos += -1
            # This needs to be updated on changes to equal the total number of entries in the menu
                else: self.pos = len(choices)
            elif self.key_pressed != ord('\n'): ## if enter not pressed, flash the screen
                curses.flash()
        # return ord(str(self.pos))
        return self.pos






class WindowOptions:
    def __init__(self):
        self.text = ""
        self.top_position = 1
        self.pos = 1
        self.current_line = 1        
        # self.pages = [] ## holds multiple pages (text) in order to simulate scrollable screen
        # self.pages.append(self.text)
        self.page_index = 0
    

    def Change(self,top,cur,pos,txt):
        self.top_position = top
        self.current_line = cur
        self.pos = pos
        self.text = txt
    
    def GetTop(self):
        return self.top_position
    
    def GetCur(self):
        return self.current_line
    
    def GetPos(self):
        return self.pos

    def GetText(self):
        return self.text
    
    def ChangeTop(self,top):
        self.top_position = top
    
    def ChangeCur(self,cur):
        self.current_line = cur
    
    def ChangePos(self,pos):
        self.pos = pos
    
    def ChangeText(self,text):
        self.text = text
    
    def UpdateText(self,text):
        self.text += text

class Pricli:
    def __init__(self,num_screens=1):
        # self.numScreens = num_screens
        # self.screens = [curses.initscr()]*num_screens
        
        ## text positioning
        # self.top_position = 1
        # self.options.ChangeCur(self.options.GetPos())
        # self.options.GetPos() = 1
        self.screen1_options = WindowOptions()
        self.screen2_options = WindowOptions()
        self.options = self.screen1_options

        ## actual text of screen

        self.pages = []
        self.pages.append(Page(self))
        self.current_page_index = 0
        self.current_view_page_index = 0
        self.current_page = self.pages[0]
        self.current_view_page = self.pages[0]

        # self.screen_text = ""

        ## indexing of screens

        self.screen_in_use = 1

        #### curses general initializations
        ## Screen objects ##
        self.screen1 = curses.initscr()
        self.screen2 = None
        self.screen = self.screen1
        self.unused_screen = None

        # self.screen.nodelay(1)

        ## Pad objects for scrollable content ##
        # self.scrollable_window = None


        curses.noecho()
        curses.cbreak()
        curses.start_color()
        self.screen.keypad(True)

        #### END curses general initializations

        self.screen_rows = curses.LINES-1
        self.screen_cols = curses.COLS-1

        
        self.longest_pos = 1


        ## initalize color pairs
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_CYAN, curses.COLOR_BLACK)


        ## colors
        self.GREEN = 1
        self.BLUE = 2
        self.WHITE = 3
        self.RED = 4
        self.YELLOW = 5
        self.MAGENTA = 6
        self.CYAN = 7

        self.BOLD = curses.A_BOLD

        self.TAB = '\t'


        self.normal_color = curses.A_NORMAL
        self.highlighted_color = curses.color_pair(self.GREEN)
        self.bold = self.BOLD

        ## KEYS
        self.UP = curses.KEY_UP
        self.DOWN = curses.KEY_DOWN
        self.RIGHT = curses.KEY_RIGHT
        self.LEFT = curses.KEY_LEFT
        
        ## menu

        self.menu = ChoiceMenu(self)

        ## Locks
        self.lock = Lock()

    def GetTop(self):
        return self.options.GetTop()
    
    def GetCur(self):
        return self.options.GetCur()
    
    def GetPos(self):
        return self.options.GetPos()

    def GetText(self):
        return self.options.GetText()
    
    def ChangeTop(self,top):
        self.options.ChangeTop(top)
    
    def ChangeCur(self,cur):
        self.options.ChangeCur(cur)
    
    def ChangePos(self,pos):
        self.options.ChangePos(pos)
    
    def ChangeText(self,text):
        self.options.ChangeText(text)
    
    def UpdateText(self,text):
        self.options.UpdateText(text)

    def UpdateCur(self,cur=1):
        self.options.ChangeCur(self.options.GetCur() + cur)
    def UpdatePos(self,pos=1):
        self.options.ChangePos(self.options.GetPos() + pos)

    def UpdateLongestPos(self,text_length):
        if self.GetPos() + text_length > self.longest_pos:
            self.longest_pos = self.GetPos() + text_length
    
        
    def ChangeWindow(self,reset=False):
        if self.screen2 == None:
            self.screen2 = curses.newwin(self.screen_rows,self.screen_cols)
            self.screen = self.screen2
            self.screen_in_use = 2
            self.options = self.screen2_options
            return
        if reset:
            self.Init()
            self.Clear()
            self.Refresh()
        if self.screen_in_use == 1:
            self.screen = self.screen2
            self.screen_in_use = 2
            self.options = self.screen2_options
        else:
            self.screen = self.screen1
            self.screen_in_use = 1
            self.options = self.screen1_options


 

    def GetWindowSize(self):
        return curses.LINES-1 , curses.COLS-1
    
    
    def Print(self,text,color=curses.A_NORMAL,line=None,pos=None): ## print some text and refresh the screen
        if line is not None:
            self.ChangeCur(line)
        if pos is not None:
            self.ChangePos(pos)
        
        if self.GetCur() > self.screen_rows - 1:
            self.ChangeCur(self.GetTop())
        # self.UpdateLongestPos(len(text))
        self.screen.addstr(self.GetCur(),self.GetPos(),text,curses.color_pair(color))
        self.UpdatePos(len(text))
        if '\t' in text:
            self.UpdatePos(8)
        self.UpdateText(str(text))
        self.screen.refresh()

    def Printlnr(self,text,color=curses.A_NORMAL,line=None,pos=None): ## print some text and refresh the screen
        if line is not None:
            self.ChangeCur(line)
        if pos is not None:
            self.ChangePos(pos)
        
        if self.GetCur() > self.screen_rows - 1:
            self.ChangeCur(self.GetTop())
        self.UpdateLongestPos(len(text))
        self.screen.addstr(self.GetCur(),self.GetPos(),text,curses.color_pair(color))
        self.UpdateCur()
        self.UpdateText(str(text))
        self.screen.refresh()

    def Println(self,text,color=curses.A_NORMAL,line=None,pos=None): ## print some text without refreshing the screen
        if line is not None:
            self.ChangeCur(line)
        if pos is not None:
            self.ChangePos(pos)

        if self.GetCur() > self.screen_rows - 1:
            self.ChangeCur(self.GetTop())
        self.UpdateLongestPos(len(text))
        self.screen.addstr(self.GetCur(),self.GetPos(),text,curses.color_pair(color))
        self.UpdateCur()
        self.UpdateText(str(text))

    def Printhln(self,text,line=None,pos=None): ## print some text without refreshing the screen
        if line is not None:
            self.ChangeCur(line)
        if pos is not None:
            self.ChangePos(pos)

        if self.GetCur() > self.screen_rows - 1:
            self.ChangeCur(self.GetTop())
        self.UpdateLongestPos(len(text))
        self.screen.addstr(self.GetCur(),self.GetPos(),text,self.highlighted_color)
        self.UpdateCur()
        self.UpdateText(str(text))

    def Printhlnr(self,text,color=curses.A_NORMAL,line=None,pos=None): ## print some text without refreshing the screen
        if line is not None:
            self.ChangeCur(line)
        if pos is not None:
            self.ChangePos(pos)

        if self.GetCur() > self.screen_rows - 1:
            self.ChangeCur(self.GetTop())
        self.UpdateLongestPos(len(text))
        self.screen.addstr(self.GetCur(),self.GetPos(),text,self.highlighted_color)
        self.UpdateCur()
        self.UpdateText(str(text))
        self.screen.refresh()

    def Printblnr(self,text,line=None,pos=None): ## print some text without refreshing the screen
        if line is not None:
            self.ChangeCur(line)
        if pos is not None:
            self.ChangePos(pos)

        if self.GetCur() > self.screen_rows - 1:
            self.ChangeCur(self.GetTop())
        self.UpdateLongestPos(len(text))
        self.screen.addstr(self.GetCur(),self.GetPos(),text,self.bold)
        self.UpdateCur()
        self.UpdateText(str(text))
        self.screen.refresh()
    

    
    def PrintFormatlnr(self,text_list,color_list,seperator=None): ## prints text, but each chunk of text in text_list, has color specified in color_list in corresponding index
        if seperator is None:
            seperator = self.TAB
        current_pos = self.GetPos()
        # current_length = len(text_list[0])
        lines = 0
        for index in range(0,len(text_list)):
            if self.GetCur() > self.screen_rows - 1:
                self.ChangeCur(self.GetTop())
            # text = ''
            # if index != len(text_list)-1:
            #     # text,linenum = self.FixWidth(text_list[index+1])
            #     current_length += len(text_list[index+1])
            #     text = text_list[index]
            #     if current_length >= 40:
            #         text = text +'\n'
            # else:
            #     text = text_list[index]
            text = text_list[index]
            text,linenum = self.FixWidth(text)
            if linenum > lines:
                lines = linenum
            # if linenum > 1:
            #     texts = text.splitlines()
            #     for line in range(0,linenum):
            #         text = texts[line]
            #         self.screen.addstr(self.GetCur(),self.GetPos(),text,curses.color_pair(color_list[index]))
            # else:
            self.screen.addstr(self.GetCur(),self.GetPos(),text,curses.color_pair(color_list[index]))
            # self.GetPos() += len(text_list[index])
            self.ChangePos(self.GetPos() + len(text_list[index]))
            # self.AddTab()
            self.UpdateLongestPos(len(text_list[index]))
            # self.screen.addstr(self.GetCur(),self.GetPos(),seperator)
            self.UpdateText(text_list[index])
        self.UpdateCur(lines)
        self.ChangePos(current_pos)
        self.screen.refresh()
    
    # def PrintFormatlistr(self,text_list,color_list,seperator=None): ## prints text, but each chunk of text in text_list, has color specified in color_list in corresponding index
    #     if seperator is None:
    #         seperator = self.TAB
    #     current_pos = self.GetPos()
    #     for index in range(0,len(text_list)):
    #         if self.GetCur() > self.screen_rows - 1:
    #             self.ChangeCur(self.GetTop())
    #             self.ChangePos(self.longest_pos+1)
    #         self.screen.addstr(self.GetCur(),self.GetPos(),text_list[index],curses.color_pair(color_list[index]))
    #         # self.GetPos() += len(text_list[index])
    #         self.ChangePos(self.GetPos() + len(text_list[index]))
    #         self.UpdateLongestPos(len(text_list[index]))
    #         self.screen.addstr(self.GetCur(),self.GetPos(),seperator)
    #         self.UpdateText(text_list[index])
    #     self.UpdateCur()
    #     self.ChangePos(current_pos)
    #     self.screen.refresh()
    
    # def Printlistr(self,text,color=curses.A_NORMAL,line=None,pos=None):
    #     if line is not None:
    #         self.ChangeCur(line)
    #     if pos is not None:
    #         self.ChangePos(pos)

    #     # if self.GetCur() > self.screen_rows - 1:
    #     #     self.ChangeCur(self.GetTop())
    #         # self.ChangePos(self.longest_pos+1)
    #     self.screen.addstr(1,80,"Row: "+str(self.GetCur()) +" and pos: "+str(self.GetPos()))
    #     self.screen.refresh()
    #     self.UpdateLongestPos(len(text))
    #     text,lines=self.FixWidth(text)
    #     self.screen.addstr(self.GetCur(),self.GetPos(),text,color)
    #     self.UpdateCur(lines)
    #     self.UpdateText(str(text))
    #     self.screen.refresh()

    # def PrintFormatlistr(self,tex,color=curses.A_NORMAL,line=None,pos=None):
    #     if line is not None:
    #         self.ChangeCur(line)
    #     if pos is not None:
    #         self.ChangePos(pos)
    #     current_pos = self.GetPos()
    #     for index in range(0,len(text_list)):
    #         if self.GetCur() > self.screen_rows - 1:
    #             self.ChangeCur(self.GetTop())
    #             self.ChangePos(self.longest_pos+1)
    #         self.screen.addstr(self.GetCur(),self.GetPos(),text_list[index],curses.color_pair(color_list[index]))
    #         # self.GetPos() += len(text_list[index])
    #         self.ChangePos(self.GetPos() + len(text_list[index]))
    #         self.UpdateLongestPos(len(text_list[index]))
    #         self.screen.addstr(self.GetCur(),self.GetPos(),seperator)
    #         self.UpdateText(text_list[index])
    #     self.UpdateCur()
    #     self.ChangePos(current_pos)
    #     self.screen.refresh()
    
    def CreateNewPage(self):
        # self.pricli.ClearPage()
        self.Init()
        self.pages.append(Page(self))
        self.current_page_index += 1
        self.current_page = self.pages[self.current_page_index]
        
    def GoToNextPage(self):
        # self.ClearPage()
        if self.current_view_page_index < len(self.pages) - 1:
            self.Init()
            self.Clear()
            self.current_view_page_index += 1
            self.current_view_page = self.pages[self.current_view_page_index]
            self.current_view_page.PrintPage()
        # self.UpdatePage()
    
    def GoToPreviousPage(self):
        # self.ClearPage()
        if self.current_view_page_index > 0:
            self.Init()
            self.Clear()
            self.current_view_page_index -= 1
            self.current_view_page = self.pages[self.current_view_page_index]
            self.current_view_page.PrintPage()
        # self.UpdatePage()
    
    def RefreshPage(self):
        self.current_view_page.PrintPage()

    def UpdatePage(self,text_list,colors=None):
        self.Clear()
        self.Init()
        # self.lock.acquire()
        self.current_page.InsertLine(text_list,colors)
        # self.lock.release()
        # if self.self.current_page == self.current_view_page:
        # self.current_view_page.PrintPage() 
    
    def ClearPage(self):
        self.lock.acquire()
        self.current_view_page.Clear()
        self.lock.release()

    def ClearPages(self):
        self.lock.acquire()
        for page in self.pages:
            page.Clear()
            self.pages.remove(page)
        self.pages = []
        self.current_page_index = 0
        self.current_view_page_index = 0
        self.Init()
        self.Clear()
        self.pages.append(Page(self))
        self.lock.release()
        self.current_page = self.pages[0]
        self.current_view_page = self.pages[0]
    


    def Init(self):
        self.ChangeCur(self.GetTop())
        self.ChangePos(1)
        # self.ChangeTop(1)

    def Input(self):
        return self.screen.getch()

    ## COLORS ##
    def SetHcolor(self,color):
        self.highlighted_color = color

    ## POSITIONING ##
    def AddTab(self):
        self.ChangePos(self.GetPos()+4)
        # self.GetPos() += 4
    
    def RemoveTab(self):
        self.ChangePos(self.GetPos()-4)
    
    def AssessText(self,text):
        # text,linesnum = self.FixWidth(text)
        if self.current_page.current_line + len(text.splitlines()) > self.screen_rows - 2:
            return False
        return True
            # self.ChangePos(35 + self.GetPos())
            # self.ChangeCur(self.GetTop()+1)
        # if self.GetPos() + 45 > self.screen_cols - 2:
        #     self.Clear()
        #     self.ChangePos(1)
        #     self.ChangeCur(self.GetTop()+1)
    
    def FixWidth(self,text):
        lines = wrap(text,20,drop_whitespace=False,break_on_hyphens=False)
        txt = ""
        for line in lines:
            txt += line + "\n"
        return txt , len(lines)
    
    def Refresh(self):
        self.screen.refresh()

    def Clear(self):
        self.screen.clear()
        # self.screen.border(0)

    def End(self):
        curses.nocbreak()
        self.screen.keypad(False)
        curses.echo()
        curses.endwin()
    
    def Debug(self,text):
        self.screen.addstr(2,100,text)
        self.screen.refresh()


def FixWidth(text):
    lines = wrap(text,25,drop_whitespace=False,break_on_hyphens=False)
    txt = ""
    for line in lines:
        txt += line + "\n"
    return txt , len(lines)
    

# pricli = Pricli()

# txt,linesnum = pricli.FixWidth(test_string)
# # print(linesnum)

# # pricli.screen.addstr(30,40,'Lines are: '+txt)
# # pricli.screen.refresh()
    
# time.sleep(1)
# # pricli.Printlnr(str(len(txt)))
# for i in range(0,linesnum):
#     w = random.randint(3,8)
#     lines = ""
#     for l in txt.splitlines()[i:i+w]:
#         lines += l+'\n'
#     time.sleep(1)
#     pricli.AssessText(lines)
#     splitted = lines.splitlines()
#     # pricli.screen.addstr(30,60,'Lines are: '+str(splitted))
#     pricli.screen.refresh()
#     for line in splitted:
#         pricli.Printlistr(str(line))    

# time.sleep(5)
# pricli.End()


# pricli = Pricli()
# topmenu(pricli)
# pricli.PrintFormatlnr(['hostname: ','192.168.1.1'],[BLUE,RED])
# pricli.Input()
# pricli.ChangeWindow()
# pricli.PrintFormatlnr(['hostname: ','192.168.1.1'],[YELLOW,GREEN])
# pricli.Input()
# pricli.End()


# pricli = Pricli()
# line = Line(pricli,test_list,colors)
# line.PrintLine()
# time.sleep(2)
# pricli.End()