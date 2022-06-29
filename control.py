# argv[1] GPIO接口(BCM)
# argv[2] 持续时间(s)

from gpiozero import LED
from time import sleep
from sys import argv


def main():
    fan = LED(int(argv[1]))
    fan.off()
    sleep(int(argv[2]))
    exit()

if __name__ == '__main__':
    main()