from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt,QCoreApplication
from gui import *
import sys
import os
import wave
import pyaudio
from aip import AipSpeech
from character_match import result_match,find_char_index_from_list
import pandas as pd
import cn2an
import datetime
APP_ID='28082896'
API_KEY='U0mD2DMYPmz8a97bwP8M9eF2'
SECRET_KEY='52Lq4D9PvpNW6qIDdtLy45Rx8DOuKV8Z'
CHUNK = 1024 
FORMAT = pyaudio.paInt16 # 16位深
CHANNELS = 1 #1是单声道，2是双声道。
RATE = 16000 # 采样率，调用API一般为8000或16000
RECORD_SECONDS = 5 # 录制时间4s

FilePath = "test.wav"


what_to_eat ={"番茄炒蛋":["番茄","鸡蛋"],
              "小炒肉":["猪肉","辣椒"],
              "番茄蛋花汤":["番茄","鸡蛋"]}



def save_wave_file(pa, filepath, data):
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pa.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(data))
    wf.close()

def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

class GUI(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super(GUI,self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("智能冰箱")
        self.move(0,0)

        self.ui.tableWidget.setColumnWidth(2,200)
        self.ui.tableWidget.setColumnWidth(4,200)
        
        self.client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

        self.ui.pushButton_2.clicked.connect(self.begin_recognize)
        self.ui.pushButton.clicked.connect(self.character_match)

        self.data_history = pd.DataFrame({"种类":[],"数量":[],"入库时间":[],"存放时间":[],"预计到期时间":[]})
        self.result = None

        if os.path.exists("data_history.csv"):
            self.data_history=pd.read_csv("data_history.csv",usecols=["种类","数量","入库时间","存放时间","预计到期时间"])
            self.data_history.sort_values(by='预计到期时间',inplace=True,ascending=True,ignore_index=False)
        self.timer_1s = QtCore.QTimer()
        self.timer_1s.timeout.connect(self.timer_1s_func)
        self.timer_1s.start(1000)

        #self.ui.label_2.setText('使用青菜100克')
        self.ui.label_2.setText('今天吃什么')
        

    def timer_1s_func(self):
        self.ui.tableWidget.setRowCount(0)
        self.ui.tableWidget.clearContents()
        if len(self.data_history)>0:
            rgb = [(144,0,0),(255,0,0)]
            timeNow = datetime.datetime.now()
            check_time_3days = list(self.data_history.iloc[:,-1] < (timeNow+datetime.timedelta(days=3)).strftime('%Y/%m/%d %H:%M:%S'))
            check_time = list(self.data_history.iloc[:,-1] < timeNow.strftime('%Y/%m/%d %H:%M:%S'))
            for i in range(len(self.data_history)):
                self.table_insertrow(list(self.data_history.iloc[i]),show_color=check_time_3days[i],rgb=rgb[int(check_time[i])])


        

            
            

            

    def get_audio(self,filepath):
        pa = pyaudio.PyAudio()
        stream = pa.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)
        
        print("*" * 10, f"开始录音：请在{RECORD_SECONDS}秒内输入语音")

        self.ui.pushButton_2.setText("正在录音")
        QCoreApplication.processEvents()
        frames = []  
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):  
            data = stream.read(CHUNK)  # 读取chunk个字节 保存到data中
            frames.append(data)  # 向列表frames中添加数据data
        
        print("*" * 10, "录音结束\n")

        stream.stop_stream()
        stream.close()  # 停止数据流
        pa.terminate()  # 关闭PyAudio
        self.ui.pushButton_2.setText("语音识别")
        #写入录音文件
        save_wave_file(pa, filepath, frames)

    def begin_recognize(self):
        self.get_audio(FilePath)

        result = self.client.asr(get_file_content(FilePath), 'wav',16000,{'dev_pid': 1537,})

        self.result = result['result'][0]

        self.ui.label_2.setText(result['result'][0])
        
    def what_to_eat_check(self,name:list):
        for key,value in what_to_eat.items():
            i = 0
            for v in value:
                if v in name:
                    i=i+1
            if i == len(value):
                return key
        return None



        

    def character_match(self):
        #测试用
        self.result = self.ui.label_2.text()


        self.result = self.result.replace('，','')
        self.result = self.result.replace('。','')

        if self.result.find("新增")!=-1:
            result_item_dict = result_match(self.result[self.result.find("新增")+2:])
            self.data_history = self.data_history.append(pd.DataFrame(result_item_dict),ignore_index=True)
            self.data_history.to_csv("data_history.csv")
        elif self.result.find('使用')!=-1:
            result = self.result[self.result.find("使用")+2:]
            #找数字位置
            digital = ['一','二','三','四','五','六','七','八','九','十','半','0','1','2','3','4','5','6','7','8','9']
            _,p1 = find_char_index_from_list(result,digital)

            #找单位位置
            uint_list = ['克','斤','份','个']
            which_uint,p2 = find_char_index_from_list(result,uint_list)

            if(p1==-1 or p2 == -1):
                print('p1=-1 or p2=-1')
                return 

            name  = result[:p1]

            count = cn2an.cn2an(result[p1:p2],'smart')

            data_list = self.data_history[self.data_history['种类'].isin([name])]
            if len(data_list)==0:
                print('data_list =None')
                return
            
            index = data_list.index.values[0]

            count_uint = data_list.loc[index,'数量']
            
            which_uint_2,p3=find_char_index_from_list(count_uint,uint_list)
            if which_uint_2!=which_uint or p3==-1:
                print('uint !=')
                return
            count_num = count_uint[:p3]
            
            count_num=cn2an.cn2an(count_num,mode='smart')

            data_number = count_num - count 
            data_uint = uint_list[which_uint]
            self.data_history.loc[index,'数量']= str(data_number)+data_uint

            if data_number<=0:
                self.data_history =self.data_history.drop(index)
                self.data_history.to_csv("data_history.csv")

        elif self.result.find('删除')!=-1:
            if self.result.find("所有")!=-1:
                #self.ui.tableWidget.setRowCount(0)
                #self.ui.tableWidget.clearContents()
                self.data_history = pd.DataFrame({"种类":[],"数量":[],"入库时间":[],"存放时间":[],"预计到期时间":[]})
                self.data_history.to_csv("data_history.csv")
            else:
                p2 = self.result.find("第")
                p3 = self.result.find("行")
                del_row = cn2an.cn2an(self.result[p2+1:p3])
                #self.ui.tableWidget.removeRow(del_row-1)
                self.data_history =self.data_history.drop(del_row-1)
                self.data_history.to_csv("data_history.csv")
            
        elif self.result.find("吃什么")!=-1:
            timeNow = datetime.datetime.now()
            name  = list(self.data_history[self.data_history.iloc[:,-1] > timeNow.strftime('%Y/%m/%d %H:%M:%S')]['种类'])
            key = self.what_to_eat_check(name)
            if key==None:
                text="我也不知道呢"
            else:
                text=f"可以吃{key}:\r\n 需要{what_to_eat[key]}"
            msg_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Information, '吃什么', text)
            msg_box.move(QtCore.QPoint(200,200))
            msg_box.exec_()








            


            # if self.result.find("删除")==-1:
            #     result_item_dict = result_match(self.result)
                
            #     # for key,value in result_item_dict.items():
            #     #     self.data_history[key].append(value)
            #     self.data_history = self.data_history.append(pd.DataFrame(result_item_dict),ignore_index=True)
            #     self.data_history.to_csv("data_history.csv")

            #     #self.table_insertrow(self.data_history.iloc[-1])
            # else:
            #     p1 = self.result.find("所有")
            #     if p1!=-1:
            #         #self.ui.tableWidget.setRowCount(0)
            #         #self.ui.tableWidget.clearContents()
            #         self.data_history = pd.DataFrame({"种类":[],"数量":[],"入库时间":[],"存放时间":[],"预计到期时间":[]})
            #         self.data_history.to_csv("data_history.csv")
            #     else:
            #         p2 = self.result.find("第")
            #         p3 = self.result.find("行")
            #         del_row = cn2an.cn2an(self.result[p2+1:p3])
            #         #self.ui.tableWidget.removeRow(del_row-1)
            #         self.data_history =self.data_history.drop(del_row-1)
            #         self.data_history.to_csv("data_history.csv")
                
                



        








    def table_insertrow(self,data:list,row=None,show_color=False,rgb=(255,0,0)):
    #向表中插入一行数据
        if row == None:
            row = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row)
        for index,item in enumerate(data):
            Qitem = QtWidgets.QTableWidgetItem(str(item))

            if show_color==True:
                Qitem.setForeground(QtGui.QBrush(QtGui.QColor(*rgb)))

            Qitem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tableWidget.setItem(row,index,Qitem)




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    #MainWindow = QtWidgets.QMainWindow()
    window = GUI()
    #window.showFullScreen()
    window.show()
    sys.exit(app.exec_())