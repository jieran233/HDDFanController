from os import path
from subprocess import PIPE, Popen
from time import sleep


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
        disk_temp = int(disk_info[9])
        return disk_temp
    else:
        return ""

def main():
    GPIO_PIN = 21  # BCM
    DUTATION = 30  # s
    TEMP_LIMIT = 40  # ℃
    cli = 'python3 ' + path.split(path.realpath(__file__))[0] + '/control.py ' + str(GPIO_PIN) + ' ' + str(DUTATION)
    # print(cli)
    while True:
        cur_temp = get_disk_temp('/dev/sdb')
        print(cur_temp)
        if cur_temp >= TEMP_LIMIT:
            sleep(DUTATION)
            continue
        execute_command_line(cli)


if __name__ == '__main__':
    main()