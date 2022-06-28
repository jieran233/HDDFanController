from os import path
from subprocess import PIPE, Popen
import time


def execute_command_line(cli):
        try:
            # 返回的是 Popen 实例对象
            proc = Popen(
                str(cli),  # cmd特定的查询空间的命令
                stdin=None,  # 标准输入 键盘
                stdout=PIPE,  # -1 标准输出（演示器、终端) 保存到管道中以便进行操作
                stderr=PIPE,  # 标准错误，保存到管道
                shell=True)

            # print(proc.communicate()) # 标准输出的字符串+标准错误的字符串
            outinfo, errinfo = proc.communicate()
            outinfo = outinfo.decode('utf-8')
            errinfo = errinfo.decode('utf-8')
            infos = {'outinfo': outinfo, 'errinfo': errinfo}
            # print(outinfo.decode('gbk'))  # 外部程序(windows系统)决定编码格式
            # print(errinfo.decode('gbk'))
            return infos
        except Exception as e:
            print('\033[0;31m' + str(e.args) + '\033[0m')
            return

def get_disk_temp(disk):
    disk_info = []
    info = execute_command_line('sudo smartctl -A ' + disk + ' | grep 194')['outinfo'].split(' ')  # C2(194) 温度 Temperature
    for i in info:
        if i != '':
            disk_info.append(i)
        else:
            continue
    # print(disk_info)
    if (len(info) != 1):
        try:
            disk_temp = int(disk_info[9])
        except Exception as e:
            print('E: {}'.format(e.args))
            return -1
    else:
        return -1
    return disk_temp

def get_cpu_temp():
    tmp = open('/sys/class/thermal/thermal_zone0/temp')
    cpu = tmp.read()
    tmp.close()
    cpu_temp= int(float(cpu) / 1000)
    #print(cpu_temp)
    return cpu_temp

def get_disk_IO_util(device):
    # sudo apt-get install sysstat
    o = execute_command_line("sar -d 1 1 | grep '" + device + "'")['outinfo'].split(' ')
    while '' in o:
        o.remove('')
    # print(o)
    r = o[9].split('\n')
    return r[0]

def main(also_by_cpu_temp_control=False, do_nothing_at_night=False, not_check_disk_temp_if_not_in_use=False):
    # also_by_cpu_temp_control          风扇亦受CPU温度控制
    # do_nothing_at_night               在晚上什么都不做
    # not_check_disk_temp_if_not_in_use 如果硬盘没有使用不要检测其温度  (检测温度会阻止硬盘休眠，这样做能使硬盘能够正常休眠)
    print('also_by_cpu_temp_control={}, do_nothing_at_night={}, not_check_disk_temp_if_not_in_use={}'.format(str(also_by_cpu_temp_control), str(do_nothing_at_night), str(not_check_disk_temp_if_not_in_use)))

    GPIO_PIN = 26  # BCM
    DUTATION = 60  # s
    DISK_TEMP_LIMIT = 40  # ℃
    CPU_TEMP_LIMIT = 60  # ℃
    NIGHT_HOURS = [0,1,2,3,4,5,6]  # 0-24 hour
    DISK = '/dev/sda'
    DISK_IO_UTIL_THRESHOLD_VALUE = 0.0  # 若磁盘IO Util高于此值即判定硬盘为使用中状态
    NORMALLY_OPEN_OR_CLOSED = True  # True=继电器常开, False=继电器常闭
    RETURN_TEMP_WHEN_DISK_NOT_IN_USE = -1  # 若 not_check_disk_temp_if_not_in_use=True 且硬盘未使用中，则将这个值作为硬盘的温度供程序处理，建议根据需求设定为一个极低的值(如-1)或极高的值(如255)
    
    disk_ = DISK.split('/')[2]  # for get_disk_IO_util(device)
    cli = 'python3 ' + path.split(path.realpath(__file__))[0] + '/control.py ' + str(GPIO_PIN) + ' ' + str(DUTATION)
    # print(cli)
    while True:
        now_ = time.localtime()
        now = time.strftime("%Y-%m-%d %H:%M:%S", now_)
        hour_now = time.strftime("%H", now_)
        continue_ = False

        for i in range(0,len(NIGHT_HOURS)):
            if (str(NIGHT_HOURS[i]) == str(hour_now)):
                continue_ = True
        if continue_ and do_nothing_at_night:
            print("At night({} o'clock), do nothing.".format(str(hour_now)))
            time.sleep(DUTATION)
            continue
        
        disk_IO_util_now = get_disk_IO_util(disk_)
        not_ = ''
        nocheckdt = False
        if (not(float(disk_IO_util_now) > float(DISK_IO_UTIL_THRESHOLD_VALUE))):
            not_ = 'not '
            strs = ["[{}] Disk is {}in use ({})".format(now, not_, disk_IO_util_now), ', disk temperature will not be checked (return {})'.format(RETURN_TEMP_WHEN_DISK_NOT_IN_USE)]
            if not_check_disk_temp_if_not_in_use:
                nocheckdt = True
                print(strs[0] + strs[1])
            else:
                print(strs[0])
        else:
            strs = ["[{}] Disk is {}in use ({})".format(now, not_, disk_IO_util_now), ', disk temperature will not be checked (return {RETURN_TEMP_WHEN_DISK_NOT_IN_USE})'.format()]
            print(strs[0])
        
        if nocheckdt:
            cur_disk_temp = RETURN_TEMP_WHEN_DISK_NOT_IN_USE
        else:
            cur_disk_temp = get_disk_temp(DISK)
        cur_cpu_temp = get_cpu_temp()
        overrun = {'disk': cur_disk_temp >= DISK_TEMP_LIMIT, 'cpu': cur_cpu_temp >= CPU_TEMP_LIMIT}
        
        texts = ['[{}] '.format(now), 'Out of limit: Disk={}({}℃)'.format(overrun['disk'], cur_disk_temp), ', CPU={}({}℃)'.format(overrun['cpu'], cur_cpu_temp)]
        
        if also_by_cpu_temp_control:
            print(texts[0] + texts[1] + texts[2])
            conditions = overrun['disk'] or overrun['cpu']
        else:
            print(texts[0] + texts[1])
            conditions = overrun['disk']
        
        if NORMALLY_OPEN_OR_CLOSED:
            # 常开继电器
            if conditions:
                execute_command_line(cli)
                continue
            time.sleep(DUTATION)
        else:
            # 常闭继电器
            if conditions:
                time.sleep(DUTATION)
                continue
            execute_command_line(cli)


if __name__ == '__main__':
    main(True, True, True)