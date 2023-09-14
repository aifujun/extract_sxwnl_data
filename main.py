
from extract_data import DataExtractor


def test():
    tmp = 32
    tmp <<= 17
    print("0x{:0>8X}".format(tmp))


def run():
    data_extractor = DataExtractor()
    # 只有原始数据时需要初始化
    data_extractor.initialize()

    # 生成全量数据
    data_extractor.generate_c_standard_file()

    # 生成自定范围数据
    # data_extractor.generate_c_standard_file(-20, 0, column_nums=8)
    # data_extractor.generate_c_standard_file(-5, 11, column_nums=8)
    # data_extractor.generate_c_standard_file(-5, 11, column_nums=6)
    # data_extractor.generate_c_standard_file(1, 21, column_nums=8)


if __name__ == '__main__':
    run()
