import os
import time

from itertools import takewhile, repeat
from os import PathLike
from typing import TextIO

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Comment:
    author = "aifujun 14149812@qq.com"

    lunar_data_file_start = (
        "#ifndef LUNAR_DATA_H_\n"
        "#define LUNAR_DATA_H_\n\n"
        "#define START_YEAR		({start_year})			/*!< 定义数据起始年份 */\n"
        "#define END_YEAR		({end_year})			/*!< 定义数据结束年份 */\n"
        "#define MINUS_MASK		(0x1000000)		/*!< 农历新年序数正负掩码 */\n"
        "#define ORDINAL_MASK	(0xFE0000)		/*!< 农历新年序数掩码 */\n"
        "#define LEAP_MON_MASK	(0x1E000)		/*!< 闰月数据掩码 */\n"
        "#define MON_INFO_MASK	(0x1FFF)		/*!< 月份大小月信息掩码 */\n\n\n")

    lunar_data_file_end = "#endif  //LUNAR_DATA_H_\n"

    special_month_info = (
        "/* 特殊年历大小月信息(索引0为年份, 后面依次为月份信息) */\n"
        "short SPECIAL_MONTH[10][17] = {\n"
        "    {-732, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 0, 0, 0, 0, 0, 0x156},\n"
        "    {-222, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 10, 11, 12, 0, 0x16AB},\n"
        "    {8, 1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0, 0, 0, 0x556},\n"
        "    {23, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 12, 0, 0, 0x1555},\n"
        "    {237, 1, 2, 0, 4, 5, 6, 7, 8, 9, 10, 11, 12, 0, 0, 0, 0x559},\n"
        "    {239, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 12, 0, 0, 0xD55},\n"
        "    {689, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 10, 0, 0, 0, 0, 0x752},\n"
        "    {700, 1, 12, 1, 2, 3, 4, 5, 6, 7, 7, 8, 9, 10, 11, 12, 0x7497},\n"
        "    {761, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 0, 0, 0, 0, 0, 0x34A},\n"
        "    {762, 1, 2, 3, 4, 5, 4, 5, 6, 7, 8, 9, 10, 11, 12, 0, 0x2A56}\n"
        "};\n\n\n")

    lunar_data = ("/**\n"
                  " * 农历月份信息。一年用4个字节(unsigned int)表示\n"
                  " * +-----------------------------------------------------------------------+\n"
                  " * | [32,25]  |        [24,17]       |  [16,13]  |         [12,0]          |\n"
                  " * |----------+----------------------+-----------+-------------------------|\n"
                  " * | reserved | 农历正月初一的年内序数 |   闰月    |  一位对应一个月份大小月   |\n"
                  " * +-----------------------------------------------------------------------+\n"
                  " * 以 0x003F16D2 (1900年)为例，4个字节的数据展开成二进制位：\n"
                  " *   ~0       00011111        1000      1 0 1 1 0 1 1 0 1 0 0 1 0\n"
                  " *  保留    1月31日（春节）  闰八月   十二月大,十一月小...闰八月小,八月大,七月大...正月小(从左往右)\n"
                  " *\n"
                  " * @Note:\n"
                  " *   1) 月份大小数据是月份小的在低位，月份大的在高位，即正月在最低位\n"
                  " *   2) 农历月份对应的位为0，表示这个月为29天（小月），为1表示有30天（大月）\n"
                  " *   3) 闰月需将[16,13]位转为十进制<n>，n为0表示本年内无闰月，n大于0表示本年闰n月\n"
                  " *   4）正月初一的年内序数需将[23,17]位转为十进制<n>; 高位[24位]为1则表示n为负数, 为0表示n为正数.\n"
                  " *      n表示农历正月初一的公历日期的年内序数(元旦1月1号序数为1, 前一年12月31号序数为-1)\n"
                  " */\n")

    lunar_data_note = (
        "/**\n"
        " * @file        {filename}\n"
        " * @brief       农历数据\n"
        " * @details     农历相关数据文件, 由脚本直接生成, 请勿直接修改, 否则可能会导致错误\n"
        " * @author      aifujun 14149812@qq.com\n"
        " * @date        {create_time}\n"
        " * @copyright   Copyright © 2025 Aifujun, All Rights Reserved.\n"
        "**/\n"
        "\n"
        "/**********************************************************************************************\n"
        " * 1) 公元前723年, 10个月, 无十一月和十二月\n"
        " * 2) 春秋历(公元前722年 – 前481年)没有固定的置闰法则，正月的月建并不固定，"
        "而是在建亥(即现在的十月)与建寅(现在的正月)之间摆动。\n"
        " *    春秋初期的正月月建多在建丑(现在的十二月)，末期则多在建子(现在的十一月)。"
        "目前学界对于春秋历的闰月的位置末有一致意见。\n"
        " * 3) 战国时代(约公元前480年 - 前222年)各国施行不同历法，当时使用的历法有六种:周历、鲁历、殷历、夏历、"
        "黄帝历和颛顼历，合称「古六历」。\n"
        " *    六种历法的计算方法大致相同，但各历的年首不尽相同，用以计算历法的历元也不同。\n"
        " * 4) 对春秋战国时期(公元前722年 – 前222年), 这里假设闰月置于年终，不注明闰几月。\n"
        " * 5) 秦朝及汉初(公元前221年 – 前104年)的历法沿用颛顼历的月序。"
        "颛顼历是古六历之一，据说战国后期在秦国使用。\n"
        " *    颛顼历以建亥(即今天的十月)为年首，但仍称建亥为十月。"
        "月的数序是十月、十一月、十二月、正月、二月……九月，闰月置于年终，称为后九月。\n"
        " * 6) 公元9年，王莽建立新朝，改正朔以殷正建丑(即现在的十二月)为年首，故公元8年的农历年(戊辰年)只有十一个月。\n"
        " *    农历月的数序是:建丑为正月、建寅为二月等等，与现在通用的月序相差一个月。"
        "新朝于地皇四年(癸未年，公元23年)亡，\n"
        " *    绿林军拥立汉淮南王刘玄为帝，改元更始元年，恢复以建寅(即现在的正月)为年首。地皇四年和更始元年有十一个月重叠。\n"
        " *    地皇四年用丑正、更始元年用寅正，所以地皇四年二至十二月相当于更始元年正至十一月。\n"
        " * 7) 魏青龙五年（丁巳年，公元237年），魏明帝改正朔，以殷正建丑(即现在的十二月)为年首，二月后实施，并改元景初元年。\n"
        " *    所以丁巳年没有三月份，二月后的月份是四月。农历月的数序是:建丑为正月、建寅为二月等等，与现在通用的月序相差一个月。\n"
        " *    景初三年（公元239年）明帝驾崩,次年恢复以建寅(即现在的正月)为年首。景初三年有两个十二月。\n"
        " * 8) 公元689年12月，武则天改正朔，以周正建子(即现在的十一月)为年首，建子改称正月，建寅（即现在的正月）改称一月，\n"
        " *    其他农历月的数序不变（即正月、十二月、一月、二月__十月）。公元701年2月又改回以建寅为年首。\n"
        " *    公元689年的农历年(己丑年)只有十一个月(其中一个月是闰月)，而公元700年的农历年(庚子年)有十五个月(其中一个月是闰月)\n"
        " * 9) 公元761年12月，唐肃宗改正朔，以周正建子(即现在的十一月)为年首，建子改称正月、建丑（即现在的十二月）改称二月、\n"
        " *    建寅（即现在的正月）改称三月等等，与现在通用的月序相差二个月。公元762年4月又把农历月的数序改回以建寅为正月、建卯为二月等。\n"
        " *    公元761年的农历年（辛丑年）只有十个月, 而公元762年的农历年（壬寅年）则有十四个月，其中有两个四月和两个五月。\n"
        " **********************************************************************************************/\n\n\n")

    lunar_data_bc723 = "公元前723年, 10个月, 无十一月和十二月"

    spring_autumn_leap_month = ("有13个月, 春秋历(公元前722年 – 前481年)没有固定的置闰法则，正月的月建并不固定，"
                                "而是在建亥(即现在的十月)与建寅(现在的正月)之间摆动。"
                                "春秋初期的正月月建多在建丑(现在的十二月)，末期则多在建子(现在的十一月)。"
                                "目前学界对于春秋历的闰月的位置末有一致意见。这里假设闰月置于年终，不注明闰几月")

    lunar_year_bc222 = ("战国时代(约前480年至前222年)各国施行不同历法，"
                        "当时使用的历法有六种:周历、鲁历、殷历、夏历、黄帝历和颛顼历，合称「古六历」。")

    qin_leap_month = ("13个月(后九月), 秦朝及汉初(公元前221年 – 前104年)的历法沿用颛顼历的月序。"
                      "颛顼历是古六历之一，据说战国后期在秦国使用。颛顼历以建亥(即今天的十月)为年首，但仍称建亥为十月。"
                      "月的数序是十月、十一月、十二月、正月、二月……九月，闰月置于年终，称为后九月。")

    lunar_year_8_23 = ("公元9年，王莽建立新朝，改正朔以殷正建丑(即现在的十二月)为年首，故公元8年的农历年(戊辰年)只有十一个月。"
                       "农历月的数序是:建丑为正月、建寅为二月等等，与现在通用的月序相差一个月。"
                       "新朝于地皇四年(癸未年，公元23年)亡，绿林军拥立汉淮南王刘玄为帝，"
                       "改元更始元年，恢复以建寅(即现在的正月)为年首。地皇四年和更始元年有十一个月重叠。"
                       "地皇四年用丑正、更始元年用寅正，所以地皇四年二至十二月相当于更始元年正至十一月。")

    lunar_year_237_239 = ("魏青龙五年（丁巳年，公元237年），魏明帝改正朔，以殷正建丑(即现在的十二月)为年首，"
                          "二月后实施，并改元景初元年。所以丁巳年没有三月份，二月后的月份是四月。"
                          "农历月的数序是:建丑为正月、建寅为二月等等，与现在通用的月序相差一个月。"
                          "景初三年（公元239年）明帝驾崩,次年恢复以建寅(即现在的正月)为年首。景初三年有两个十二月。")

    lunar_year_689_700 = ("公元689年12月，武则天改正朔，以周正建子(即现在的十一月)为年首，建子改称正月，"
                          "建寅（即现在的正月）改称一月，其他农历月的数序不变（即正月、十二月、一月、二月__十月）。"
                          "公元701年2月又改回以建寅为年首。公元689年的农历年（己丑年）只有十一个月（其中一个月是闰月），"
                          "而公元700年的农历年（庚子年）有十五个月（其中一个月是闰月）")

    lunar_year_761_762 = ("公元761年12月，唐肃宗改正朔，以周正建子(即现在的十一月)为年首，"
                          "建子改称正月、建丑（即现在的十二月）改称二月、建寅（即现在的正月）改称三月等等，"
                          "与现在通用的月序相差二个月。公元762年4月又把农历月的数序改回以建寅为正月、建卯为二月等。"
                          "公元761年的农历年（辛丑年）只有十个月,"
                          "而公元762年的农历年（壬寅年）则有十四个月，其中有两个四月和两个五月。")


class DataExtractor:
    month_name = ["-*-", "正", "二", "三", "四", "五", "六", "七", "八", "九", "十", "冬", "腊"]

    month_info = [
        "二月大", "三月大", "四月大", "五月大", "六月大", "七月大", "八月大", "九月大", "十月大", "冬月大", "腊月大",
        "二月小", "三月小", "四月小", "五月小", "六月小", "七月小", "八月小", "九月小", "十月小", "冬月小", "腊月小",

        "闰正月小", "闰二月大", "闰三月大", "闰四月大", "闰五月大", "闰六月大", "闰七月大", "闰八月大", "闰九月大",
        "闰十月大", "闰冬月大", "闰腊月大",
        "闰正月大", "闰二月小", "闰三月小", "闰四月小", "闰五月小", "闰六月小", "闰七月小", "闰八月小", "闰九月小",
        "闰十月小", "闰冬月小", "闰腊月小",

        "拾贰大", "拾贰小", "十三小", "十三大", "后九小", "后九大", "一月小", "一月大"
    ]

    # 春秋战国时期(公元前722年 – 前222年)
    spring_autumn_leap_year = [
        -721, -718, -715, -713, -710, -707, -704, -702, -699, -696, -694, -691, -688, -685, -683,
        -680, -677, -675, -672, -669, -666, -664, -661, -658, -656, -653, -650, -647, -645, -642,
        -639, -637, -634, -631, -628, -626, -623, -620, -618, -615, -612, -609, -607, -604, -601,
        -599, -596, -593, -590, -588, -585, -582, -580, -577, -574, -571, -569, -566, -563, -561,
        -558, -555, -552, -550, -547, -544, -542, -539, -536, -533, -531, -528, -525, -523, -520,
        -517, -514, -512, -509, -506, -504, -501, -498, -495, -493, -490, -487, -485, -482, -479,
        -476, -474, -471, -468, -466, -463, -460, -457, -455, -452, -449, -447, -444, -441, -438,
        -436, -433, -430, -428, -425, -422, -419, -417, -414, -411, -409, -406, -403, -400, -398,
        -395, -392, -390, -387, -384, -381, -379, -376, -373, -371, -368, -365, -362, -360, -357,
        -354, -352, -349, -341, -346, -343, -338, -335, -333, -330, -327, -324, -322, -319, -316,
        -314, -311, -308, -305, -303, -300, -297, -295, -292, -289, -286, -284, -281, -278, -276,
        -273, -270, -267, -265, -262, -259, -257, -254, -251, -248, -246, -243, -240, -238, -235,
        -232, -229, -227, -224
    ]

    # 秦朝及汉初(公元前221年 – 前104年)
    qin_leap_year = [
        -221, -218, -216, -213, -210, -208, -205, -202, -199, -197, -194, -191, -189, -186, -183,
        -180, -178, -175, -172, -170, -167, -164, -162, -159, -156, -153, -151, -148, -145, -143,
        -140, -137, -134, -132, -129, -126, -124, -121, -118, -115, -113, -110, -107, -105
    ]

    SOLAR_DAY_OF_MONTH = [
        [365, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
        [366, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31],
        [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365],
        [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366],
    ]

    def __init__(self,
                 _source: str | PathLike[str] = os.sep.join([BASE_DIR, "data/lunar_data.txt"]),
                 _dest: str | PathLike[str] = os.sep.join([BASE_DIR, "export/lunar_data.h"])):
        self.source = _source
        self.dest = _dest
        self.cleaned_data_file = os.sep.join([BASE_DIR, "data/cleaned_data.txt"])
        self.compress_data_file = os.sep.join([BASE_DIR, "data/compress_data.txt"])
        self._start_year = -4713
        self._end_year = 9999

    @staticmethod
    def get_current_time() -> str:
        """获取当前时间 (like: 2023-01-01 12:12:12)"""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    @staticmethod
    def is_leap_year(year: int) -> int:
        """判断公历年是否为闰年
        :param year: 公历年份
        :return:
        """
        # 对于大数值年份，能整除3200且能整除172800为闰年
        if (year < 0) and (abs(year) % 4 == 1):
            return 1

        # 世纪年能被400整除的是闰年
        if (year > 0) and (year <= 1582) and (year % 4 == 0):
            return 1

        # 普通年能被4整除且不能被100整除的为闰年
        if (year > 1582) and (
                (year % 4 == 0 and year % 100 != 0)
                or (year % 400 == 0 and year % 3200 != 0)
                or (year % 172800 == 0)):
            return 1

        return 0

    @staticmethod
    def iter_count(filename: str | PathLike[str]) -> int:
        """获取文件总行数(换行符数目+1)
        :param filename: 文件名
        :return: 文件总行数
        """
        buffer = 1024 * 1024
        with open(filename) as f:
            buf_gen = takewhile(lambda x: x, (f.read(buffer) for _ in repeat(None)))
            return sum(buf.count('\n') for buf in buf_gen) + 1

    @staticmethod
    def format_output(_data: list, out_io: TextIO, *, start: int = 0, reverse: bool = False, column_nums: int = 8):
        """将数据格式化成 C 数组
        :param _data: 输入数据(数据来源)
        :param out_io: 输出TextIO(数据输出)
        :param start: 数据起始序列(注释用)
        :param reverse: 数据序列是否倒序输出(是否为公元前)
        :param column_nums: 数组每一行包含数据个数 [1, 10000]
        :return:
        """
        out_io.write(Comment.lunar_data)
        if reverse:
            out_io.write(f"unsigned int const LUNAR_DATA_BC[{len(_data) + 1}] = {{\n")
        else:
            out_io.write(f"unsigned int const LUNAR_DATA_AD[{len(_data) + 1 if start == 0 else len(_data)}] = {{\n")

        pos = 0
        if reverse or start == 0:
            out_io.write("    0x00000000, ")
            pos += 1

        for value in _data:
            if pos == 0:
                out_io.write(f"    {value}, ")
                pos += 1
            elif pos == (column_nums - 1):
                out_io.write(f"{value},\t\t\t/*!< {start:>5d} -> {start - pos if reverse else start + pos:>5d} */\n")
                start += -column_nums if reverse else column_nums
                pos = 0
            else:
                out_io.write(f"{value}, ")
                pos += 1

        if pos == 0:
            out_io.write("};\n\n")
        else:
            end = start - pos + 1 if reverse else start + pos - 1
            tab = '\t' * (column_nums - pos) * 3
            out_io.write(f"{tab}\t\t/*!< {start:>5d} -> {end:>5d} */\n}};\n\n")

    def _inspect_month_data(self, year, leap_month, month_data) -> bool:
        if year < self._start_year - 1 or year > self._end_year or year == 0:
            raise ValueError(f"year: {year} is out of range [{self._start_year}, -1] and [1, {self._end_year}].")

        if year == self._start_year - 1:
            return False

        if len(month_data) > 13 or len(month_data) < 12:
            if len(month_data) == 10 and (year == -723 or year == 761):
                return True
            elif len(month_data) == 11 and (year == 237 or year == 689):
                return True
            elif len(month_data) == 14 and (year == -222 or year == 762):
                return True
            elif len(month_data) == 15 and year == 700:
                return True
            else:
                raise ValueError(f"year: {year}, data: {month_data} is out of range.")
        elif (len(month_data) == 12 and leap_month != 0) or (len(month_data) == 13 and leap_month == 0):
            if len(month_data) == 13 and (year == 23 or year == 239):
                return True
            if len(month_data) == 12 and year == 8:
                return True
            raise ValueError(f"year: {year}, data: {month_data} is error.")

        return True

    def initialize(self):
        self.data_cleaning()
        self.compress_data()

    def data_cleaning(self) -> None:
        """将月份信息数据清理出来"""
        year = self._start_year - 1
        month_data = ""
        leap_month = 0
        chunjie_date = ""
        with (open(self.source, "r", encoding="utf-8") as stream,
              open(self.cleaned_data_file, "w+", encoding="utf-8") as out):
            while line := stream.readline().strip():
                mon_info = line.split()[0]

                if mon_info.startswith("year") or mon_info.startswith("---"):
                    continue

                if mon_info.startswith("闰"):
                    leap_month = self.month_name.index(list(mon_info)[1])
                if year in self.spring_autumn_leap_year:
                    # 目前学界对于春秋历的闰月的位置末有一致意见。这里假设闰月置于年终，不注明闰几月
                    # Comment.spring_autumn_leap_month
                    leap_month = 12
                if year in self.qin_leap_year:
                    # 颛顼历以建亥(即今天的十月)为年首，但仍称建亥为十月.闰月置于年终，称为后九月。
                    # Comment.qin_leap_month
                    leap_month = 9

                if mon_info in ["正月小", "正月大"]:
                    # print(year, leap_month, month_data)
                    if self._inspect_month_data(year, leap_month, month_data):
                        out.write(f"{year},{chunjie_date},{leap_month},{month_data}\n")

                    # 进入新的一年
                    year += 1  # 年份加1
                    if year == 0:
                        year += 1  # 没有0年, 公元前1年-->公元1年
                    leap_month = 0  # 重置闰月信息
                    month_data = ""  # 重置月份数据

                    chunjie_date = line.split()[1]
                    month_data += "1" if mon_info.endswith("大") else "0"
                    continue
                elif mon_info not in self.month_info:
                    raise ValueError(f"{mon_info} is not expected.")

                month_data += "1" if mon_info.endswith("大") else "0"

    def compress_data(self) -> None:
        """将清理的数据压缩"""
        with (open(self.cleaned_data_file, "r", encoding="utf-8") as stream,
              open(self.compress_data_file, "w+", encoding="utf-8") as out):
            while line := stream.readline().strip():
                year, chunjie_date, leap_mon, data = line.split(",")
                chunjie_date = chunjie_date.split("(")[0]
                month, day = int(chunjie_date.split("-")[0], 10), int(chunjie_date.split("-")[1], 10)
                final_data = 0
                if month > 6:
                    # 正月在前一个月
                    chunjie_ordinal = self.SOLAR_DAY_OF_MONTH[self.is_leap_year(int(year) - 1)][month] - day
                    while month < 12:
                        chunjie_ordinal += self.SOLAR_DAY_OF_MONTH[self.is_leap_year(int(year) - 1)][month + 1]
                        month += 1
                    chunjie_ordinal = -(chunjie_ordinal + 1)
                else:
                    chunjie_ordinal = self.SOLAR_DAY_OF_MONTH[self.is_leap_year(int(year)) + 2][month - 1] + day

                if chunjie_ordinal < 0:
                    chunjie_ordinal = -chunjie_ordinal
                    final_data = 1
                    final_data <<= 24
                final_data |= (chunjie_ordinal << 17)
                final_data |= (int(leap_mon) << 13)
                data = data[::-1]  # 原始月份大小月数据排序为从左往右表示: 正月->腊月, 保存数据时需要反转
                tmp_data = (int(data, 2) & 0x1FFF)  # 只保留13位, 大于13位的年份(BC222, 700, 762)单独说明处理
                final_data |= tmp_data
                # print("{},0x{:0>8X}".format(year, final_data))
                out.write("{},0x{:0>8X}\n".format(year, final_data))

    def generate_c_standard_file(self, start_year: int = -4713, end_year: int = 9999, *, column_nums: int = 8) -> None:
        """
        生成 C 标准头文件
            1) 数组 LUNAR_DATA_BC 包含公元前的农历数据信息(如果生成范围包含)
            2) 数组 LUNAR_DATA_AD 包含公元后的农历数据信息(如果生成范围包含)
        :param start_year: 农历数据起始年 [-4713, 9999]
        :param end_year: 农历数据结束年 [-4713, 9999]
        :param column_nums: 数组每一行包含数据个数 [1, 10000]
        :return:
        """
        if start_year > self._end_year or start_year < self._start_year:
            raise ValueError(f"Start year: {start_year} is out of range [{self._start_year}, {self._end_year}].")
        if end_year > self._end_year or end_year < self._start_year:
            raise ValueError(f"Start year: {start_year} is out of range [{self._start_year}, {self._end_year}].")
        if end_year < start_year:
            raise ValueError(f"Start year: {start_year} must be less than or equal to end year: {end_year}.")

        with (open(self.compress_data_file, "r", encoding="utf-8") as stream,
              open(self.dest, "w+", encoding="utf-8") as out):
            out.write(Comment.lunar_data_note
                      .format(filename=os.path.basename(self.dest), create_time=self.get_current_time()))
            out.write(Comment.lunar_data_file_start.format(start_year=start_year, end_year=end_year))
            out.write(Comment.special_month_info)

            tmp_data_bc = []
            tmp_data_ad = []
            while line := stream.readline().strip():
                year, data = int(line.split(",")[0], 10), line.split(",")[1]
                if year > end_year:
                    break
                if year < start_year:
                    continue
                if year < 0:
                    tmp_data_bc.insert(0, data)
                else:
                    tmp_data_ad.append(data)
            if tmp_data_bc:
                self.format_output(tmp_data_bc, out, reverse=True, column_nums=column_nums)
            if tmp_data_ad:
                start = start_year if start_year > 0 else 0
                self.format_output(tmp_data_ad, out, start=start, column_nums=column_nums)

            out.write(Comment.lunar_data_file_end)


if __name__ == '__main__':
    data_extractor = DataExtractor()
    data_extractor.generate_c_standard_file()
