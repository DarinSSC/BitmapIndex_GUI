# -*- coding: utf-8 -*-
from Tkinter import *
from FileDialog import *
import tkFont
import numpy
import data_pickle
import bitmap_pickle
import bitmap_index2
import copy
import time

def getline(thefilepath,line_num):  
    if line_num < 1 :return ''  
    for currline,line in enumerate(open(thefilepath,'rU')):  
        if currline == line_num-1 : return line.strip() 
    return '' 

class GUI():

	'''def file_menu():
	file_btn = Tkinter.Menubutton(menu_frame, text='file', underline=0)
	file_btn.pack(side=Tkinter.LEFT, padx="2m")
	file_btn.menu = Tkinter.Menu(file_btn)
	file_btn.menu.add_command(label="How To", underline=0, command=hello)
	file_btn.menu.add_command(label="About", underline=0, command=hello)
	file_btn['menu'] = file_btn.menu
	return file_btn
'''

	def __init__(self):
		#Initialize variables 
		self.attr_dict = None
		self.attr_values = None
		self.attr_value_NO = None
		self.attr_list = None

		self.file_path = ''
		self.file_ob = None
		self.attr_num = 0
		self.data_pic_path = ''
		self.bitmap_pic_path = ''
		self.file_attr_num = 7 #network traffic data has 7 attributes by default

		#optionMenu stringVar
		self.stringVarList = []
		self.optionMenuList = []
		self.menuButtonList = []
		self.selectedAttr = []

		self.root = Tk()
		self.root.title('Welcome!')
		self.root.geometry('1200x800+300+100')
		self.root.resizable(width=False, height=False)

		#----------------------- menu bar --------------------------
		self.menubar = Menu(self.root)		
		self.menubar.add_command(label = 'Open',command = self.open)
		self.menubar.add_command(label = 'Save',command = self.hello)
		self.menubar.add_command(label = 'Help',command = self.hello)
		self.root['menu'] = self.menubar


		self.fm1 = Frame(self.root,width = 1200,height = 300)
		self.fm2 = Frame(self.root,bg = 'blue',width = 1200,height = 500, borderwidth = 2)

		self.fm1_1 = Frame(self.fm1, width = 500,height = 300)
		self.fm1_2 = Frame(self.fm1, width = 698, height = 300, )
		
		self.temp_fm2_1 = Frame(self.fm2, bg='red', width=1200, height=40, borderwidth = 2)
		self.fm2_1 = Frame(self.temp_fm2_1, width=1200, height=40)
		self.fm2_2 = Frame(self.fm2, width=1200, height=460)

		#-----------------fm1_1: Entry frame-------------------------
		self.entry_label = Label(self.fm1_1, text='Enter what you\'d like to search(split by \',\'):', font=tkFont.Font(size=11))
		self.entry_label.place(relx = 0.5, rely = 0.4, anchor = CENTER)
		self.entry_value = StringVar()
		self.entry = Entry(self.fm1_1, textvariable=self.entry_value, width=20, font=tkFont.Font(family='Times',size=11), selectbackground='yellow')
		self.entry.place(relx = 0.5, rely = 0.55,relheight=0.1, relwidth=0.7, anchor=CENTER)
		self.entry_button = Button(self.fm1_1, command=self.from_entry_get_selected, text='Search', state=DISABLED)
		self.entry_button.place(relx = 0.5, rely=0.65, anchor = CENTER)

		#-----------------fm1_2: optionMenu frame--------------------
		self.optionLabelList = [0]*self.file_attr_num  #label	
		self.menuButtonList = [0]*self.file_attr_num   #optionMenu
		self.menu = [[] for i in xrange(self.file_attr_num)]	
		for i in xrange(self.file_attr_num):
			self.optionLabelList[i] = Label(self.fm1_2, text = 'label'+str(i)+':', anchor=E, width=15, relief=FLAT, state=DISABLED,font=tkFont.Font(size=11, weight='bold'))
			self.optionLabelList[i].place(relx = 0.5*(i%2)+0.25, rely = 0.2*(i/2)+0.1, anchor=E)

			self.menuButtonList[i] = Menubutton(self.fm1_2, text="All", indicatoron=True, 
                                        borderwidth=3, relief="raised", width=15)
			self.menu[i] = Menu(self.menuButtonList[i], tearoff=False)
			self.menuButtonList[i].configure(menu=self.menu[i], state=DISABLED)
			
			self.menuButtonList[i].place(relx = 0.5*(i%2)+0.25, rely = 0.2*(i/2)+0.1, anchor=W)
		self.optionbutton = Button(self.fm1_2, text='OK', state=DISABLED, command=self.displaydata)
		self.optionbutton.place(relx=0.5, rely=0.9, anchor=CENTER)
		
		#------------------fm2_1: result label----------------------
		self.result_label1 = Label(self.fm2_1, text='Total Records: ', font = tkFont.Font(size=11, weight='bold'), anchor=E)
		self.result_label2 = Label(self.fm2_1, text='---', font = tkFont.Font(size=12, weight='bold'), anchor=W, fg='red', state=DISABLED)
		self.result_label3 = Label(self.fm2_1, text='Using Time: ', font = tkFont.Font(size=11, weight='bold'), anchor=E)
		self.result_label4 = Label(self.fm2_1, text='---', font = tkFont.Font(size=12, weight='bold'), anchor=W, fg='red', state = DISABLED)
		self.result_label1.place(relx=0,rely=0.5, relwidth=0.25, anchor=W)
		self.result_label2.place(relx=0.25,rely=0.5, relwidth=0.25, anchor=W)
		self.result_label3.place(relx=0.5,rely=0.5, relwidth=0.25, anchor=W)
		self.result_label4.place(relx=0.75,rely=0.5, relwidth=0.25, anchor=W)

		#------------------fm2_2: listbox -------------------------
		self.yscrollbar = Scrollbar(self.fm2_2)
		self.xscrollbar = Scrollbar(self.fm2_2, orient=HORIZONTAL)
		self.yscrollbar.pack(side=RIGHT, fill=Y)
		self.xscrollbar.pack(side=BOTTOM, fill=X)
		self.listbox = Listbox(self.fm2_2, yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set, width=1200, height=460)		
		self.listbox.pack(fill=BOTH)
		self.yscrollbar.config(command=self.listbox.yview)
		self.xscrollbar.config(command=self.listbox.xview)
		
		self.border_in_fm1 = Frame(self.fm1, bg = 'yellow', width = 2, height=300)		
		self.fm1_1.grid(row=0, column=0)
		self.border_in_fm1.grid(row=0, column=1)
		self.fm1_2.grid(row=0, column=2)
		self.temp_fm2_1.pack()
		self.fm2_1.pack(fill = BOTH)
		self.fm2_2.pack()
		self.fm1.pack(fill = BOTH)
		self.fm2.pack(fill = BOTH)
		self.root.mainloop()

	def hello(self):
		print 'Hello'

	def open(self):
		fd = LoadFileDialog(self.root) # 创建打开文件对话框
		self.filepath = fd.go() # 显示打开文件对话框，并获取选择的文件名称
		self.attr_dict, self.attr_values, self.attr_value_NO, self.attr_list, self.data_pic_path = data_pickle.openfile(self.filepath)	
		print self.attr_value_NO
		self.attr_num = len(self.attr_list)		
		self.selectedAttr = [['All']for i in xrange(self.attr_num)]
		self.optionItem = [[]  for i in xrange(self.attr_num)]
		self.v = [[] for i in xrange(self.attr_num)]
		print self.attr_list
		for i in xrange(self.attr_num):			
			attr_value = list(self.attr_dict[self.attr_list[i]])
			for value in attr_value:
				self.optionItem[i].append(value)
				self.v[i].append(IntVar())
			self.optionLabelList[i]['state'] = NORMAL
			self.menuButtonList[i]['state'] = NORMAL
			j = 0
			for choice in self.optionItem[i]:
				if i == 0:
					self.menu[i].add_checkbutton(label=choice, variable=self.v[i][j], 
                                  command=lambda option=choice: self.dealwith_option(0, option))
				elif i == 1:
					self.menu[i].add_checkbutton(label=choice, variable=self.v[i][j], 
                                  command=lambda option=choice: self.dealwith_option(1, option))
				elif i == 2:
					self.menu[i].add_checkbutton(label=choice, variable=self.v[i][j], 
                                  command=lambda option=choice: self.dealwith_option(2, option))
				elif i == 3:
					self.menu[i].add_checkbutton(label=choice, variable=self.v[i][j], 
                                  command=lambda option=choice: self.dealwith_option(3, option))
				elif i == 4:
					self.menu[i].add_checkbutton(label=choice, variable=self.v[i][j], 
                                  command=lambda option=choice: self.dealwith_option(4, option))
				elif i == 5:
					self.menu[i].add_checkbutton(label=choice, variable=self.v[i][j], 
                                  command=lambda option=choice: self.dealwith_option(5, option))
				elif i == 6:
					self.menu[i].add_checkbutton(label=choice, variable=self.v[i][j], 
                                  command=lambda option=choice: self.dealwith_option(6, option))
				j += 1
			self.optionLabelList[i]['text'] = self.attr_list[i] + ':'
		self.optionbutton['state'] = NORMAL
		self.entry_button['state'] = NORMAL
	
	#initialize the selectedAttr and option in optionButton
	def selected_init(self):
		for i in xrange(self.attr_num):
			for vij in self.v[i]:
				vij.set(0) #initialization--nothing selected in option menus
		self.selectedAttr = [['All']for i in xrange(self.attr_num)]
	
	#update the text of the option button
	def update_option_button(self,i):
		length = len(self.selectedAttr[i])
		if length > 1:
			newlabel = ''
			for l in self.selectedAttr[i][1:length]:
				newlabel += (l+',')
				self.v[i][self.optionItem[i].index(l)].set(1) #update the selection of the menu
			self.menuButtonList[i]['text'] = newlabel
		else:
			self.menuButtonList[i]['text'] = 'All'

	def dealwith_option(self, i, option):
		if option in self.selectedAttr[i]:
			self.selectedAttr[i].remove(option)
		else:
			self.selectedAttr[i].append(option)
		self.update_option_button(i)
		

	def from_entry_get_selected(self):	
		self.selected_init()
		for i in xrange(self.attr_num):#update after initialization
			self.update_option_button(i)	
		entry_input = self.entry.get().split(',')
		input_num = len(entry_input)
		for input_attr in entry_input:
			for i in xrange(self.attr_num):
				if input_attr in self.attr_dict[self.attr_list[i]]:
					self.selectedAttr[i].append(input_attr)
		for i in range(self.attr_num):#update after gaining new selectedAttr
			self.update_option_button(i)
		self.displaydata()		
		
	#display the search result in the listbox
	def displaydata(self):		
		print self.selectedAttr
		start = time.time()
		self.index_list, search_time = bitmap_index2.get_indexList(self.filepath, self.selectedAttr)	
		end = time.time()	
		print str(end-start)
		
		print self.index_list	
		self.file_ob = open(self.filepath)
		self.listbox.delete(0,END)#clear
		counter = 0
		'''for i in xrange(len(self.index_list)):
			start = time.time()
			if self.index_list[i] > 0:
				
				self.listbox.insert(END, getline(self.filepath, self.index_list[i]+1))
				counter += 1
			end = time.time()
			print str(end-start)
		'''
		ob = open(self.filepath)
		ob.readline()
		for index in self.index_list:
			line = ob.readline()
			if index>0:
				counter += 1
				self.listbox.insert(END, line.strip())
		self.result_label2['text'] = str(counter)
		self.result_label2['state'] = NORMAL
		self.result_label4['text'] = str(round(search_time, 3)) + 's'
		self.result_label4['state'] = NORMAL
		
		

if __name__ == '__main__':
	a = GUI()
	
