from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt,QCoreApplication
from gui import *
import sys
import os
import wave
import pyaudio
from aip import AipSpeech
from character_match import result_match
import pandas as pd
import cn2an
APP_ID='28082896'
API_KEY='U0mD2DMYPmz8a97bwP8M9eF2'
SECRET_KEY='52Lq4D9PvpNW6qIDdtLy45Rx8DOuKV8Z'
CHUNK = 1024 
FORMAT = pyaudio.paInt16 # 16位深
CHANNELS = 1 #1是单声道，2是双声道。
RATE = 16000 # 采样率，调用API一般为8000或16000
RECORD_SECONDS = 5 # 录制时间4s

FilePath = "test.wav"

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
        pa = pyaudio.PyAudio()

        self.stream =  pa.open(format=FORMAT,
                         channels=CHANNELS,
                         rate=RATE,
                         input=True,
                         frames_per_buffer=CHUNK)
        
        self.client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

        self.ui.pushButton_2.clicked.connect(self.begin_recognize)
        self.ui.pushButton.clicked.connect(self.character_match)

        self.data_history = pd.DataFrame({"种类":[],"数量":[],"入库时间":[],"存放时间":[],"预计到期时间":[]})
        self.result = None

        if os.path.exists("data_history.csv"):
            self.data_history=pd.read_csv("data_history.csv",usecols=["种类","数量","入库时间","存放时间","预计到期时间"])

            
            for i in range(len(self.data_history)):
                self.table_insertrow(list(self.data_history.iloc[i]))
        

                
        

            
            

            

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

        

    def character_match(self):
        try:
            self.result = self.result.replace('，','')
            self.result = self.result.replace('。','')

            if self.result.find("删除")==-1:
                result_item_dict = result_match(self.result)
                
                # for key,value in result_item_dict.items():
                #     self.data_history[key].append(value)
                self.data_history = self.data_history.append(pd.DataFrame(result_item_dict),ignore_index=True)
                self.data_history.to_csv("data_history.csv")

                self.table_insertrow(self.data_history.iloc[-1])
            else:
                p1 = self.result.find("所有")
                if p1!=-1:
                    self.ui.tableWidget.setRowCount(0)
                    self.ui.tableWidget.clearContents()
                    self.data_history = pd.DataFrame({"种类":[],"数量":[],"入库时间":[],"存放时间":[],"预计到期时间":[]})
                    self.data_history.to_csv("data_history.csv")
                else:
                    p2 = self.result.find("第")
                    p3 = self.result.find("行")
                    del_row = cn2an.cn2an(self.result[p2+1:p3])
                    self.ui.tableWidget.removeRow(del_row-1)
                    self.data_history =self.data_history.drop(del_row-1)
                    self.data_history.to_csv("data_history.csv")
        except:
            pass

                
                



        








    def table_insertrow(self,data:list,row=None):
    #向表中插入一行数据
        if row == None:
            row = self.ui.tableWidget.rowCount()
        self.ui.tableWidget.insertRow(row)
        for index,item in enumerate(data):
            Qitem = QtWidgets.QTableWidgetItem(str(item))
            Qitem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.ui.tableWidget.setItem(row,index,Qitem)




if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    #MainWindow = QtWidgets.QMainWindow()
    window = GUI()
    #window.showFullScreen()
    window.show()
    sys.exit(app.exec_())