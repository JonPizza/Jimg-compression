from PIL import Image
import sys, time

magic_values = {}
magic_values_inv = {}
mv_amt = 100

def gen_magic_values(amt: int):
    global magic_values, magic_values_inv
    for i in range(1, amt + 1):
        magic_values[i] = i * 2 + 1
    
    for i in range(1, amt + 1):
        magic_values_inv[magic_values[i]] = i


def int_to_byte(i: int) -> bytes:
    return bytes.fromhex(hex(i)[2:].zfill(2))


def ave_px_values(pxs: list) -> tuple:
    total = [0, 0, 0]
    for px in pxs:
        for i in range(3):
            total[i] += px[i]

    ret = []
    for t in total:
        ret.append(t // len(pxs))
    
    return tuple(ret)


def similar_px(px1: tuple, px2: tuple, tol: int=13) -> bool:
    for i in range(len(px1)):
        if px1[i] - tol > px2[i] or px1[i] + tol < px2[i]:
            return False
    return True


def compress(img: Image) -> bytes:
    print(img.width, img.height)
    out = b'JPNG' + img.width.to_bytes(2, byteorder='big') + img.height.to_bytes(2, byteorder='big')

    history = []
    gen_magic_values(mv_amt)

    for y in range(img.height):
        for x in range(img.width):
            px = img.getpixel((x, y))[:3]
            if len(history) == 0 or (similar_px(history[0], px) and len(history) < mv_amt - 1):
                history.append(px)

            elif len(history) == 1:
                if history[0][0] in magic_values_inv:
                    out += int_to_byte(history[0][0] + 1)
                else:
                    out += int_to_byte(history[0][0])

                for i in range(2):
                    out += int_to_byte(history[0][i + 1])
                
                history = [px]
            
            else:
                out += int_to_byte(magic_values[len(history)]) # magic byte
                ave = ave_px_values(history)

                for b in ave:
                    out += int_to_byte(b)
                
                history = [px]
    
    return out


def decompress(img: bytes) -> Image:
    assert img[:4] == b'JPNG', 'Not a JPNG!'
    width = int(img[4:6].hex(), 16)
    height = int(img[6:8].hex(), 16)

    new_img = Image.new('RGB', (width, height))

    buf = []
    i = 0

    try:
        for b in img[8:]:
            buf.append(b)
            if len(buf) == 3 and buf[0] not in magic_values_inv:
                new_img.putpixel((i % width, i // width), tuple(buf))
                # print('Set new px:', (i % width, i // width), tuple(buf))
                buf = []
                i += 1
            elif len(buf) == 4 and buf[0] in magic_values_inv:
                # print(f'Setting the next {magic_values_inv[buf[0]]} pixels {tuple(buf[1:])}')
                for _ in range(magic_values_inv[buf[0]]):
                    new_img.putpixel((i % width, i // width), tuple(buf[1:]))
                    # print('Set new px:', (i % width, i // width), tuple(buf[1:]))
                    i += 1
                buf = []

    except IndexError as e:
        print(e)

    return new_img

def main():
    img = Image.open(sys.argv[1])
    print('Compressing...')
    compressed = compress(img)
    open('img-compressed.jpng', 'wb').write(compressed)
    print('Decompressing...')
    decompress(compressed).save('decompressed.png')

if __name__ == '__main__':
    main()