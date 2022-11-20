import cn2an
import datetime
digital = ['一','二','三','四','五','六','七','八','九','十','半','0','1','2','3','4','5','6','7','8','9']
time_list = ['天','小时','周','分钟','秒']
time_list_for_delta = ['days','hours','weeks','minutes','seconds']
uint_list = ['克','斤','份','个']
def find_char_index_from_list(str_:str,char_list:list):
    p_list=[]

    for index_in_list,char_ in enumerate(char_list):
        p_in_str = str_.find(char_)
        if p_in_str==-1:
            p_in_str=1000
        p_list.append(p_in_str)
    
    p_min = min(p_list)
    index_in_char_list = p_list.index(p_min)
    return index_in_char_list,p_min

def get_time(str_:str):
    time_dict ={}

    timeNow = datetime.datetime.now()
    
    time_dict['入库时间'] = [timeNow.strftime('%Y/%m/%d %H:%M:%S')]


    index,p = find_char_index_from_list(str_,time_list)

    number = str_[:p]
    number = cn2an.cn2an(number,'smart')

    d = {}
    d[time_list_for_delta[index]]=number

    time_delay = timeNow + datetime.timedelta(**d)
    time_dict['存放时间'] = [f'{number}'+time_list[index]]

    time_dict['预计到期时间'] = [time_delay.strftime('%Y/%m/%d %H:%M:%S')]

    return time_dict




def result_match(result:str):
    output = {}
    result = result.replace('，','')
    result = result.replace('。','')
    position = result.find("存放")

    name_count = result[:position]
    cunfang_time = result[position+2:]


    _,p = find_char_index_from_list(name_count,digital)
    name  = name_count[:p]
    count_uint = name_count[p:]

    which_uint,p=find_char_index_from_list(count_uint,uint_list)
    count = cn2an.cn2an(count_uint[:p],'smart')
    output['种类'] =[name]
    output['数量'] = [str(count)+ uint_list[which_uint]]

    output.update(get_time(cunfang_time))



    return output

    
#print(result_match('剁椒排骨一份，存放一年'))

# print(list(result_match('苹果，，，一公斤存放十三天。').values()))

