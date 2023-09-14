
from extract_data import DataExtractor


def test():
    tmp = 32
    tmp <<= 17
    print("0x{:0>8X}".format(tmp))


def run():
    data_extractor = DataExtractor()
    data_extractor.generate_c_standard_file()


if __name__ == '__main__':
    run()
