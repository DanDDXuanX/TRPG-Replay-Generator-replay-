"""
回声工坊主页面
"""
import tkinter as tk
from .AppFrame import AppFrame
from PIL import Image,ImageTk,ImageFont,ImageDraw
import webbrowser
import os
import appFrames as af
from tkinter import messagebox

class MainFrame(AppFrame):
    def __init__(self,master,app,*args, **kwargs):
        super().__init__(master,app,*args, **kwargs)
        self.place(x=10,y=50)
        self.createWidgets()

    def createWidgets(self):
        # main_frame
        # 路径
        filepath = tk.LabelFrame(self,text='文件路径')
        filepath.place(x=10,y=10,width=600,height=200)

        tk.Label(filepath, text="媒体定义：",anchor=tk.W).place(x=10,y=5,width=70,height=30)
        tk.Label(filepath, text="角色配置：",anchor=tk.W).place(x=10,y=50,width=70,height=30)
        tk.Label(filepath, text="log文件：",anchor=tk.W).place(x=10,y=95,width=70,height=30)
        tk.Label(filepath, text="输出路径：",anchor=tk.W).place(x=10,y=140,width=70,height=30)
        tk.Entry(filepath, textvariable=self.app.media_define).place(x=80,y=5+3,width=430,height=25)
        tk.Entry(filepath, textvariable=self.app.characor_table).place(x=80,y=50+3,width=430,height=25)
        tk.Entry(filepath, textvariable=self.app.stdin_logfile).place(x=80,y=95+3,width=430,height=25)
        tk.Entry(filepath, textvariable=self.app.output_path).place(x=80,y=140+3,width=430,height=25)
        self.new_or_edit = tk.Button(filepath, command=self.call_Edit_windows,text="新建")
        self.new_or_edit.place(x=555,y=5,width=35,height=30)
        tk.Button(filepath, command=lambda:self.call_browse_file(self.app.media_define),text="浏览").place(x=520,y=5,width=35,height=30)
        tk.Button(filepath, command=lambda:self.call_browse_file(self.app.characor_table),text="浏览").place(x=520,y=50,width=70,height=30)
        tk.Button(filepath, command=lambda:self.call_browse_file(self.app.stdin_logfile),text="浏览").place(x=520,y=95,width=70,height=30)
        tk.Button(filepath, command=lambda:self.call_browse_file(self.app.output_path,'path'),text="浏览").place(x=520,y=140,width=70,height=30)


        # 选项
        optional = tk.LabelFrame(self,text='选项')
        optional.place(x=10,y=210,width=600,height=110)

        tk.Label(optional,text="分辨率-宽:",anchor=tk.W).place(x=10,y=5,width=70,height=30)
        tk.Label(optional,text="分辨率-高:",anchor=tk.W).place(x=160,y=5,width=70,height=30)
        tk.Label(optional,text="帧率:",anchor=tk.W).place(x=310,y=5,width=70,height=30)
        tk.Label(optional,text="图层顺序:",anchor=tk.W).place(x=10,y=50,width=70,height=30)
        tk.Entry(optional,textvariable=self.app.project_W).place(x=80,y=5,width=70,height=25)
        tk.Entry(optional,textvariable=self.app.project_H).place(x=230,y=5,width=70,height=25)
        tk.Entry(optional,textvariable=self.app.project_F).place(x=380,y=5,width=70,height=25)
        tk.Entry(optional,textvariable=self.app.project_Z).place(x=80,y=50,width=370,height=25)

        # 标志
        flag = tk.LabelFrame(self,text='标志')
        flag.place(x=10,y=320,width=600,height=110)

        tk.Checkbutton(flag,text="先执行语音合成",variable=self.app.synthanyway,anchor=tk.W,command=lambda:self.highlight(self.app.synthanyway)).place(x=10,y=0,width=150,height=30)
        tk.Checkbutton(flag,text="导出为PR项目",variable=self.app.exportprxml,anchor=tk.W,command=lambda:self.highlight(self.app.exportprxml)).place(x=10,y=27,width=150,height=30)
        tk.Checkbutton(flag,text="导出为.mp4视频",variable=self.app.exportmp4,anchor=tk.W,command=lambda:self.highlight(self.app.exportmp4)).place(x=170,y=27,width=150,height=30)
        tk.Checkbutton(flag,text="取消系统缩放",variable=self.app.fixscrzoom,anchor=tk.W,command=lambda:self.highlight(self.app.fixscrzoom)).place(x=170,y=0,width=150,height=30)
        tk.Checkbutton(flag,text="保存设置内容",variable=self.app.save_config,anchor=tk.W).place(x=10,y=55,width=150,height=30)

        self.my_logo = ImageTk.PhotoImage(Image.open('./media/logo.png').resize((236,75))) # 教训：如果不设置为属性，则图片对象会被回收
        tk.Button(flag,image = self.my_logo,command=lambda: webbrowser.open('https://www.wolai.com/PjcZ7xwNTKB2VJ5AJYggv'),relief='flat').place(x=339,y=0)

        # 开始
        tk.Button(self, command=self.run_command_main,text="开始",font=self.app.big_text).place(x=260,y=435,width=100,height=50)

        # 初始化highlight和编辑/新建按钮的显示
        try:
            for flag in [self.app.synthanyway,self.app.exportmp4,self.app.exportprxml,self.app.fixscrzoom]:
                if flag.get() == 1:
                    self.highlight(flag)
            if os.path.isfile(self.app.media_define.get()):
                self.new_or_edit.config(text='编辑')
            else:
                self.new_or_edit.config(text='新建')
        except Exception:
            pass

    def call_Edit_windows(self):
        """
        调出媒体定义文件编辑器
        """
        Edit_filepath=self.app.media_define.get()
        fig_W = self.app.project_W.get()
        fig_H = self.app.project_H.get()
        try:
            self.master.attributes('-disabled',True) # 开着编辑器的时候，将窗体设置为禁用
        except Exception:
            pass
        # 如果Edit_filepath是合法路径
        if os.path.isfile(Edit_filepath): # alpha 1.8.5 非法路径
            return_from_Edit = af.EditorFrame(self.master,Edit_filepath,fig_W,fig_H).openEditorWindows()
        else:
            self.new_or_edit.config(text='新建')
            self.app.media_define.set('')
            return_from_Edit = af.EditorFrame(self.master,'',fig_W,fig_H).openEditorWindows()
        try:
            self.master.attributes('-disabled',False)
        except Exception:
            pass
        self.master.lift()
        self.master.focus_force()
        # 如果编辑窗的返回值是合法路径
        if os.path.isfile(return_from_Edit):
            self.media_define.set(return_from_Edit)
            self.new_or_edit.config(text='编辑')
        else:
            self.new_or_edit.config(text='新建')

    def run_command_main(self):
        optional = {1:'--OutputPath {of} ',2:'--ExportXML ',3:'--ExportVideo --Quality {ql} ',4:'--SynthesisAnyway --AccessKey {AK} --AccessKeySecret {AS} --Appkey {AP} --Azurekey {AZ} --ServRegion {SR} ',5:'--FixScreenZoom '}
        command = self.app.python3 + ' ./replay_generator.py --LogFile {lg} --MediaObjDefine {md} --CharacterTable {ct} '
        command = command + '--FramePerSecond {fps} --Width {wd} --Height {he} --Zorder {zd} '
        if self.app.output_path.get()!='':
            command = command + optional[1].format(of=self.app.output_path.get().replace('\\','/'))
        if self.app.synthanyway.get()==1:
            command = command + optional[4].format(AK=self.app.AccessKey.get(),AS=self.app.AccessKeySecret.get(),AP=self.app.Appkey.get(),AZ=self.app.AzureKey.get(),SR=self.app.ServiceRegion.get()).replace('\n','').replace('\r','') # a 1.10.7 处理由于key复制导致的异常换行
        if self.app.exportprxml.get()==1:
            command = command + optional[2]
        if self.app.exportmp4.get()==1:
            command = command + optional[3].format(ql=self.app.project_Q.get())
        if self.app.fixscrzoom.get()==1:
            command = command + optional[5]
        if '' in [self.app.stdin_logfile.get(),self.app.characor_table.get(),self.app.media_define.get(),self.app.project_W.get(),self.app.project_H.get(),self.app.project_F.get(),self.app.project_Z.get()]:
            messagebox.showerror(title='错误',message='缺少必要的参数！')
        else:
            command = command.format(lg = self.app.stdin_logfile.get().replace('\\','/'),md = self.app.media_define.get().replace('\\','/'),
                                     ct=self.app.characor_table.get().replace('\\','/'),fps=self.app.project_F.get(),
                                     wd=self.app.project_W.get(),he=self.app.project_H.get(),zd=self.app.project_Z.get())
            try:
                print('[32m'+command+'[0m')
                exit_status = os.system(command)
                if exit_status != 0:
                    raise OSError('Major error occurred in replay_generator!')
                else:
                    # 如果指定了要先语音合成，而且星标文件存在，且退出状态是正常，把log文件设置为星标文件：
                    if (self.app.synthanyway.get() == 1):
                        messagebox.showinfo(title='完毕',message='语音合成程序执行完毕！\nLog文件已更新')
            except Exception:
                messagebox.showwarning(title='警告',message='似乎有啥不对劲的事情发生了，检视控制台输出获取详细信息！')