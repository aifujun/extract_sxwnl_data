
def process():
    file = "data/archive/2.txt"
    with open(file, "r") as f, open("22.txt", "w+") as out:
        while line := f.readline():
            line = int(line, 16)
            ordinal_days = ((line & 0xFE0000) >> 17) + 1
            old = line & 0x1FFFF
            new_data = ordinal_days << 17
            new_data |= old
            print("0x{:0>8X}".format(new_data))
            out.write("0x{:0>8X}\n".format(new_data))


if __name__ == '__main__':
    process()
