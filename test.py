import wave
import pyaudio
from aip import AipSpeech
APP_ID='28082896'
API_KEY='U0mD2DMYPmz8a97bwP8M9eF2'
SECRET_KEY='52Lq4D9PvpNW6qIDdtLy45Rx8DOuKV8Z'
CHUNK = 1024 
FORMAT = pyaudio.paInt16 # 16位深
CHANNELS = 1 #1是单声道，2是双声道。
RATE = 16000 # 采样率，调用API一般为8000或16000
RECORD_SECONDS = 10 # 录制时间10s

def save_wave_file(pa, filepath, data):
    wf = wave.open(filepath, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(pa.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(data))
    wf.close()

def get_audio(filepath):
    isstart = input("是否开始录音？(0为退出 1为开始)")
    if isstart == "1":
        pa = pyaudio.PyAudio()
        stream = pa.open(format=FORMAT,
                         channels=CHANNELS,
                         rate=RATE,
                         input=True,
                         frames_per_buffer=CHUNK)
        print("*" * 10, "开始录音：请在10秒内输入语音")

        frames = []  
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):  
            data = stream.read(CHUNK)  # 读取chunk个字节 保存到data中
            frames.append(data)  # 向列表frames中添加数据data
        print("*" * 10, "录音结束\n")
        stream.stop_stream()
        stream.close()  # 停止数据流
        pa.terminate()  # 关闭PyAudio

        #写入录音文件
        save_wave_file(pa, filepath, frames)
    elif isstart == "0":
        exit()
    else:
        print("无效输入，请重新选择")
        get_audio(filepath)

def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

if __name__ == '__main__':
    filepath = 'test.wav'
    get_audio(filepath)
    print('over!!!')
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
    result = client.asr(get_file_content('test.wav'), 'wav',16000,{'dev_pid': 1537,})
    print(result)
