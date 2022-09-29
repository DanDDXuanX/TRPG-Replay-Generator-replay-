#!/usr/bin/env python
# coding: utf-8
from Utils import edtion

# 外部参数输入

import argparse
import sys
import os

ap = argparse.ArgumentParser(description="Export MP4 video from timeline file.")
ap.add_argument("-l", "--TimeLine", help='Timeline (and break_point with same name), which was generated by replay_generator.py.',type=str)
ap.add_argument("-d", "--MediaObjDefine", help='Definition of the media elements, using real python code.',type=str)
ap.add_argument("-t", "--CharacterTable", help='This program do not need CharacterTable.',type=str)
ap.add_argument("-o", "--OutputPath", help='Choose the destination directory to save the project timeline and break_point file.',type=str,default=None)
# 增加一个，读取时间轴和断点文件的选项！
ap.add_argument("-F", "--FramePerSecond", help='Set the FPS of display, default is 30 fps, larger than this may cause lag.',type=int,default=30)
ap.add_argument("-W", "--Width", help='Set the resolution of display, default is 1920, larger than this may cause lag.',type=int,default=1920)
ap.add_argument("-H", "--Height", help='Set the resolution of display, default is 1080, larger than this may cause lag.',type=int,default=1080)
ap.add_argument("-Z", "--Zorder", help='Set the display order of layers, not recommended to change the values unless necessary!',type=str,
                default='BG3,BG2,BG1,Am3,Am2,Am1,AmS,Bb,BbS')
ap.add_argument("-Q", "--Quality", help='Choose the quality (ffmpeg crf) of output video.',type=int,default=24)
args = ap.parse_args()

Width = args.Width #显示的分辨率
Height = args.Height
frame_rate = args.FramePerSecond #帧率 单位fps
zorder = args.Zorder.split(',') #渲染图层顺序

try:
    for path in [args.TimeLine,args.MediaObjDefine]:
        if path is None:
            print(path)
            raise OSError("[31m[ArgumentError]:[0m Missing principal input argument!")
        if os.path.isfile(path) == False:
            raise OSError("[31m[ArgumentError]:[0m Cannot find file "+path)

    if args.OutputPath is None:
        pass 
    elif os.path.isdir(args.OutputPath) == False:
        try:
            os.makedirs(args.OutputPath)
        except Exception:
            raise OSError("[31m[SystemError]:[0m Cannot make directory "+args.OutputPath)
    args.OutputPath = args.OutputPath.replace('\\','/')

    # FPS
    if frame_rate <= 0:
        raise ValueError("[31m[ArgumentError]:[0m "+str(frame_rate))
    elif frame_rate>30:
        print("[33m[warning]:[0m",'FPS is set to '+str(frame_rate)+', which may cause lag in the display!')

    if (Width<=0) | (Height<=0):
        raise ValueError("[31m[ArgumentError]:[0m "+str((Width,Height)))
    if Width*Height > 3e6:
        print("[33m[warning]:[0m",'Resolution is set to more than 3M, which may cause lag in the display!')
except Exception as E:
    print(E)
    sys.exit(1)

import pandas as pd
import numpy as np
import pygame
import ffmpeg
import pydub
import time
import re
import pickle

# 自由点
from FreePos import Pos,FreePos,PosGrid

# 类定义 alpha 1.11.0

from Medias import Text
from Medias import StrokeText
from Medias import Bubble
from Medias import Balloon
from Medias import DynamicBubble
from Medias import ChatWindow
from Medias import Background
from Medias import Animation
from Medias import GroupedAnimation
from Medias import BuiltInAnimation
from Medias import screen_config
screen_config['screen_size'] = (Width,Height)
screen_config['frame_rate'] = frame_rate

from Medias import Audio_Video as Audio
from Medias import BGM_Video as BGM

# 处理bg 和 am 的parser
def parse_timeline(layer):
    global timeline,break_point
    track = render_timeline[[layer]]
    clips = []
    item,begin,end = 'NA',0,0
    for key,values in track.iterrows():
        #如果item变化了，或者进入了指定的断点
        if (values[layer] != item) | (key in break_point.values): 
            if (item == 'NA') | (item!=item): # 如果itme是空 
                pass # 则不输出什么
            else:
                end = key #否则把当前key作为一个clip的断点
                clips.append((item,begin,end)) #并记录下这个断点
            item = values[layer] #无论如何，重设item和begin
            begin = key
        else: #如果不满足断点要求，那么就什么都不做
            pass
    # 循环结束之后，最后检定一次是否需要输出一个clips
    end = key
    if (item == 'NA') | (item!=item):
        pass
    else:
        clips.append((item,begin,end))
    return clips #返回一个clip的列表

# 渲染函数
def render(this_frame):
    global media_list
    for layer in zorder:
        # 不渲染的条件：图层为"Na"，或者np.nan
        if (this_frame[layer]=='NA')|(this_frame[layer]!=this_frame[layer]):
            continue
        elif this_frame[layer+'_a']<=0: #或者图层的透明度小于等于0(由于fillna("NA"),出现的异常)
            continue
        elif this_frame[layer] not in media_list:
            raise RuntimeError('[31m[RenderError]:[0m Undefined media object : "'+this_frame[layer]+'".')
        elif layer[0:2] == 'BG':
            try:
                exec('{0}.display(surface=screen,alpha={1},adjust={2},center={3})'.format(this_frame[layer],
                                                                                          this_frame[layer+'_a'],
                                                                                          '\"'+this_frame[layer+'_p']+'\"',
                                                                                          '\"'+this_frame[layer+'_c']+'\"'))
            except Exception:
                raise RuntimeError('[31m[RenderError]:[0m Failed to render "'+this_frame[layer]+'" as Background.')
        elif layer[0:2] == 'Am': # 兼容H_LG1(1)这种动画形式 alpha1.6.3
            try:
                exec('{0}.display(surface=screen,alpha={1},adjust={2},frame={3},center={4})'.format(
                                                                                         this_frame[layer],
                                                                                         this_frame[layer+'_a'],
                                                                                         '\"'+this_frame[layer+'_p']+'\"',
                                                                                         this_frame[layer+'_t'],
                                                                                         '\"'+this_frame[layer+'_c']+'\"'))
            except Exception:
                raise RuntimeError('[31m[RenderError]:[0m Failed to render "'+this_frame[layer]+'" as Animation.')
        elif layer[0:2] == 'Bb':
            try:
                exec('{0}.display(surface=screen,text={2},header={3},alpha={1},adjust={4},center={5})'.format(this_frame[layer],
                                                                                                   this_frame[layer+'_a'],
                                                                                                   '\"'+this_frame[layer+'_main']+'\"',
                                                                                                   '\"'+this_frame[layer+'_header']+'\"',
                                                                                                   '\"'+this_frame[layer+'_p']+'\"',
                                                                                                   '\"'+this_frame[layer+'_c']+'\"'))
            except Exception:
                raise RuntimeError('[31m[RenderError]:[0m Failed to render "'+this_frame[layer]+'" as Bubble.')
    return 1

# 被占用的变量名 # 1.7.7
occupied_variable_name = open('./media/occupied_variable_name.list','r',encoding='utf8').read().split('\n')

# Main():

print('[export Video]: Welcome to use exportVideo for TRPG-replay-generator '+edtion)
print('[export Video]: The output mp4 file will be saved at "'+args.OutputPath+'"')

# 载入timeline 和 breakpoint
timeline_ifile = open(args.TimeLine,'rb')
render_timeline,break_point,bulitin_media = pickle.load(timeline_ifile)
timeline_ifile.close()
stdin_name = args.TimeLine.replace('\\','/').split('/')[-1]

cmap = {'black':(0,0,0,255),'white':(255,255,255,255),'greenscreen':(0,177,64,255)}

# 载入od文件
try:
    object_define_text = open(args.MediaObjDefine,'r',encoding='utf-8').read()#.split('\n')
except UnicodeDecodeError as E:
    print('[31m[DecodeError]:[0m',E)
    sys.exit(1)
if object_define_text[0] == '\ufeff': # 139 debug
    print('[33m[warning]:[0m','UTF8 BOM recognized in MediaDef, it will be drop from the begin of file!')
    object_define_text = object_define_text[1:]
object_define_text = object_define_text.split('\n')

media_list=[]
for i,text in enumerate(object_define_text):
    if text == '':
        continue
    elif text[0] == '#':
        continue
    else:
        try:
            exec(text) #对象实例化
            obj_name = text.split('=')[0]
            obj_name = obj_name.replace(' ','')
            if obj_name in occupied_variable_name:
                raise SyntaxError('Obj name occupied')
            elif (len(re.findall('\w+',obj_name))==0)|(obj_name[0].isdigit()):
                raise SyntaxError('Invalid Obj name')
            media_list.append(obj_name) #记录新增对象名称
        except Exception as E:
            print('[31m[SyntaxError]:[0m "'+text+'" appeared in media define file line ' + str(i+1)+' is invalid syntax:',E)
            sys.exit(1)
black = Background('black')
white = Background('white')
media_list.append('black')
media_list.append('white')
# alpha 1.6.5 载入导出的内建媒体
for key,values in bulitin_media.iteritems():
    exec(values)
    media_list.append(key)

# 合成音轨

print('[export Video]: Start mixing audio tracks')

tracks = ['SE','Voice','BGM']
main_Track = pydub.AudioSegment.silent(duration=int(break_point.values.max()/frame_rate*1000),frame_rate=48000) # 主轨道

for tr in tracks:
    this_Track = pydub.AudioSegment.silent(duration=int(break_point.values.max()/frame_rate*1000),frame_rate=48000)
    if tr == 'BGM':
        BGM_clips = parse_timeline('BGM')
        for i,item in enumerate(BGM_clips):
            voice,begin,drop = item
            if voice == 'stop':
                continue # 遇到stop，直切切到下一段
            elif voice not in media_list: # 如果是路径形式
                temp_BGM = BGM(voice[1:-1]) # 去除引号
                voice = 'temp_BGM'
            try:
                end = BGM_clips[i+1][1]
            except IndexError:
                end = break_point.values.max()
            # print(begin,end)
            # 这里似乎是有，BGM不正常循环的bug！！！！！！！！！！
            this_Track = this_Track.overlay(
                pydub.AudioSegment.silent(duration=int((end-begin)/frame_rate*1000),frame_rate=48000).overlay(eval(voice+'.media'),loop=eval(voice+'.loop')),
                position = int(begin/frame_rate*1000)
                )
    else:
        for item in parse_timeline(tr):
            voice,begin,drop = item
            if voice not in media_list: # 如果是路径形式
                temp_AU = Audio(voice[1:-1]) # 去除引号
                voice = 'temp_AU'
            this_Track = this_Track.overlay(eval(voice+'.media'),position = int(begin/frame_rate*1000))
    main_Track = main_Track.overlay(this_Track) #合成到主音轨
    print('[export Video]: Track {0} finished.'.format(tr))

main_Track.export(args.OutputPath+'/'+stdin_name+'.mp3',format='mp3',codec='mp3',bitrate='256k')

print('[export Video]: Audio mixing done!')

# 初始化

print('[export Video]: Start encoding video, using ffmpeg.')

pygame.init()
screen = pygame.display.set_mode((Width,Height),pygame.HIDDEN)

# 转换媒体对象
for media in media_list: 
    try:
        exec(media+'.convert()')
    except Exception as E:
        print('[31m[MediaError]:[0m Exception during converting',media,':',E)
        sys.exit(1)

# ffmpeg输出
output_engine = (
    ffmpeg
    .input('pipe:',format='rawvideo',r=frame_rate,pix_fmt='rgb24', s='{0}x{1}'.format(Height,Width)) # 视频来源
    .output(ffmpeg.input(args.OutputPath+'/'+stdin_name+'.mp3').audio,
            args.OutputPath+'/'+stdin_name+'.mp4',
            pix_fmt='yuv420p',r=frame_rate,crf=args.Quality,
            **{'loglevel':'quiet','vf':'transpose=0'}) # 输出
    .overwrite_output()
    .run_async(pipe_stdin=True)
)

begin_time = time.time()
# 主循环
n=0
while n < break_point.max():
    try:
        if n in render_timeline.index:
            this_frame = render_timeline.loc[n]
            render(this_frame)
            obyte = pygame.surfarray.array3d(screen).tobytes()
        else:
            pass # 节约算力
        output_engine.stdin.write(obyte) # 写入视频
        n = n + 1 #下一帧
    except Exception as E:
        print(E)
        print('[31m[RenderError]:[0m','Render exception at frame:',n)
        output_engine.stdin.close()
        pygame.quit()
        sys.exit(1)
    if n%frame_rate == 1:
        finish_rate = n/break_point.values.max()
        print('[export Video]:','[{0}] {1},\t{2}'.format(int(finish_rate*50)*'#'+(50-int(50*finish_rate))*' ',
                                                        '%.1f'%(finish_rate*100)+'%','{0}/{1}'.format(n,'%d'%break_point.values.max())),
        end = "\r"
        )
    elif n == break_point.values.max():
        print('[export Video]:','[{0}] {1},\t{2}'.format(50*'#',
                                                        '%.1f'%100+'%','{0}/{1}'.format(n,n)))
output_engine.stdin.close()
pygame.quit()

used_time = time.time()-begin_time

print('[export Video]: Export time elapsed : '+time.strftime("%H:%M:%S", time.gmtime(used_time)))
print('[export Video]: Mean frames rendered per second : '+'%.2f'%(break_point.max()/used_time)+' FPS')
print('[export Video]: Encoding finished! Video path :',args.OutputPath+'/'+stdin_name+'.mp4')

sys.exit(0)
