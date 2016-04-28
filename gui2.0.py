# -*- coding: utf-8 -*-
from Tkinter import *
from FileDialog import *
import numpy
import data_pickle
import bitmap_pickle
import bitmap_index2
import copy

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

		self.menubar = Menu(self.root)		
		self.menubar.add_command(label = 'Open',command = self.open)
		self.menubar.add_command(label = 'Save',command = self.hello)
		self.menubar.add_command(label = 'Help',command = self.hello)
		self.root['menu'] = self.menubar


		self.fm1 = Frame(self.root,width = 1200,height = 300)
		self.fm2 = Frame(self.root,bg = 'blue',width = 1200,height = 500)

		self.fm1_1 = Frame(self.fm1,bg = 'yellow',width = 500,height = 300)
		self.fm1_2 = Frame(self.fm1, width = 700, height = 300)

		self.yscrollbar = Scrollbar(self.fm2)
		self.xscrollbar = Scrollbar(self.fm2, orient=HORIZONTAL)
		self.yscrollbar.pack(side=RIGHT, fill=Y)
		self.xscrollbar.pack(side=BOTTOM, fill=X)
		self.listbox = Listbox(self.fm2, yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set, width = 1200,height = 500)
		
		self.listbox.pack(fill=BOTH)
		self.yscrollbar.config(command=self.listbox.yview)
		self.xscrollbar.config(command=self.listbox.xview)

		#-----------------fm1_2: optionMenu frame--------------------
		self.optionLabelList = [0]*self.file_attr_num  #label	
		self.menuButtonList = [0]*self.file_attr_num   #optionMenu
		self.menu = [[] for i in xrange(self.file_attr_num)]	
		for i in xrange(self.file_attr_num):
			self.optionLabelList[i] = Label(self.fm1_2, text = 'label'+str(i)+':', anchor=E, width=15, relief=FLAT)
			self.optionLabelList[i].place(relx = 0.5*(i%2)+0.25, rely = 0.2*(i/2)+0.1, anchor=E)

			self.menuButtonList[i] = Menubutton(self.fm1_2, text="All", indicatoron=True, 
                                        borderwidth=3, relief="raised", width=15)
			self.menu[i] = Menu(self.menuButtonList[i], tearoff=False)
			self.menuButtonList[i].configure(menu=self.menu[i])
			
			self.menuButtonList[i].place(relx = 0.5*(i%2)+0.25, rely = 0.2*(i/2)+0.1, anchor=W)
		self.optionbutton = Button(self.fm1_2, text='OK', state=DISABLED, command=self.displaydata)
		self.optionbutton.place(relx=0.5, rely=0.9, anchor=CENTER)
		
		self.fm1_1.grid(row=0, column=0)
		self.fm1_2.grid(row=0, column=1)
		self.fm1.pack(fill = BOTH)
		self.fm2.pack(fill = BOTH)
		self.root.mainloop()

	def hello(self):
		print 'Hello'

	def open(self):
		fd = LoadFileDialog(self.root) # 创建打开文件对话框
		self.filepath = fd.go() # 显示打开文件对话框，并获取选择的文件名称
		self.attr_dict, self.attr_values, self.attr_value_NO, self.attr_list, self.data_pic_path = data_pickle.openfile(self.filepath)	
		self.attr_num = len(self.attr_list)		
		self.selectedAttr = [['All']for i in xrange(self.attr_num)]
		self.optionItem = [[]  for i in xrange(self.attr_num)]
		print self.attr_list
		for i in xrange(self.attr_num):			
			attr_value = list(self.attr_dict[self.attr_list[i]])
			for value in attr_value:
				self.optionItem[i].append(value)
			print i
			print self.optionItem[i]
			for choice in self.optionItem[i]:
				if i == 0:
					self.menu[i].add_checkbutton(label=choice, 
                                  command=lambda option=choice: self.dealwith_option(0, option))
				elif i == 1:
					self.menu[i].add_checkbutton(label=choice, 
                                  command=lambda option=choice: self.dealwith_option(1, option))
				elif i == 2:
					self.menu[i].add_checkbutton(label=choice, 
                                  command=lambda option=choice: self.dealwith_option(2, option))
				elif i == 3:
					self.menu[i].add_checkbutton(label=choice, 
                                  command=lambda option=choice: self.dealwith_option(3, option))
				elif i == 4:
					self.menu[i].add_checkbutton(label=choice, 
                                  command=lambda option=choice: self.dealwith_option(4, option))
				elif i == 5:
					self.menu[i].add_checkbutton(label=choice, 
                                  command=lambda option=choice: self.dealwith_option(5, option))
				elif i == 6:
					self.menu[i].add_checkbutton(label=choice, 
                                  command=lambda option=choice: self.dealwith_option(6, option))
			self.optionLabelList[i]['text'] = self.attr_list[i]
		self.optionbutton['state'] = NORMAL
		
	def dealwith_option(self, i, option):
		if option in self.selectedAttr[i]:
			self.selectedAttr[i].remove(option)
		else:
			self.selectedAttr[i].append(option)
		length = len(self.selectedAttr[i])
		if length > 1:
			newlabel = ''
			for l in self.selectedAttr[i][1:length]:
				newlabel += (l+',')
			self.menuButtonList[i]['text'] = newlabel
		else:
			self.menuButtonList[i]['text'] = 'All'


	def displaydata(self):		
		print self.selectedAttr
		self.index_list = bitmap_index2.get_indexList(self.filepath, self.selectedAttr)		
		print self.index_list	
		self.file_ob = open(self.filepath)
		self.listbox.delete(0,END)
		for i in xrange(len(self.index_list)):
			if self.index_list[i] > 0:
				self.listbox.insert(END, getline(self.filepath, self.index_list[i]+1))

if __name__ == '__main__':
	a = GUI()
	
