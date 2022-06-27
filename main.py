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
            outinfo = outinfo.decode('gbk')
            errinfo = errinfo.decode('gbk')
            infos = {'outinfo': outinfo, 'errinfo': errinfo}
            # print(outinfo.decode('gbk'))  # 外部程序(windows系统)决定编码格式
            # print(errinfo.decode('gbk'))
            return infos
        except Exception as e:
            print('\033[0;31m' + str(e.args) + '\033[0m')
            return

def get_disk_temp(disk):
    # disk_ = '/dev/sdb'
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

def main(also_by_CPU_temp_control=False):
    GPIO_PIN = 21  # BCM
    DUTATION = 60  # s
    DISK_TEMP_LIMIT = 40  # ℃
    CPU_TEMP_LIMIT = 60  # ℃
    DISK = '/dev/sdb'
    cli = 'python3 ' + path.split(path.realpath(__file__))[0] + '/control.py ' + str(GPIO_PIN) + ' ' + str(DUTATION)
    # print(cli)
    while True:
        cur_disk_temp = get_disk_temp(DISK)
        cur_cpu_temp = get_cpu_temp()
        overrun = {'disk': cur_disk_temp >= DISK_TEMP_LIMIT, 'cpu': cur_cpu_temp >= CPU_TEMP_LIMIT}
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        texts = ['[{}] '.format(now), 'Out of limit: Disk={}({}℃)'.format(overrun['disk'], cur_disk_temp), ', CPU={}({}℃)'.format(overrun['cpu'], cur_cpu_temp)]
        
        if also_by_CPU_temp_control:
            print(texts[0] + texts[1] + texts[2])
            conditions = overrun['disk'] or overrun['cpu']
        else:
            print(texts[0] + texts[1])
            conditions = overrun['disk']
        
        if (conditions):
            time.sleep(DUTATION)
            continue
        execute_command_line(cli)


if __name__ == '__main__':
    main(True)