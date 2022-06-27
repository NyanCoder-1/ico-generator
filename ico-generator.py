from PIL import Image
import io
import sys

def convert(inFileName, outFileName):
    # типа константы
    ICONDIR_size = 6
    ICONDIRENTRY_size = 16
    BMPHEADER_size = 0x28
    BMPs_sizes = (48, 32, 16)
    icon_entries = (1 + len(BMPs_sizes))

    img = Image.open(inFileName)
    if img.size != (256, 256): # приведение любого размера в 256x256 с оцентровкой и прозрачным фоном
        width, height = img.size
        if width and height:
            aspect = min(width, height) / max(width, height)
            downscale = max(width, height) > 256
            width, height = (256, int(256*aspect)) if width > height else (int(256*aspect), 256)
            img = img.resize(size = (width, height), resample=Image.LANCZOS if downscale else Image.BICUBIC)
            img1 = Image.new(mode="RGBA", size=(256, 256), color = (0, 0, 0, 0))
            img1.paste(img, (int((256 - width) / 2), int((256 - height) / 2)))
            img = img1

    # ПНГшка 256x256
    png_byte_arr = io.BytesIO()
    img.save(png_byte_arr, format='PNG')
    png_byte_arr = png_byte_arr.getvalue()
    png_size = len(png_byte_arr)

    def bmpRawSizeCalculator(width, height): # размер сырой битмапы
        return width * height * 4 + height * width * 2 // 8 + (1 if (height * width * 2 % 8) != 0 else 0)
    def getIcoBmpHeader(img): # заголовок для битмапы (только 32-битные RGBA)
        order = 'little'
        # тут надо высоту вдвое умножать, не знаю зачем, но в википедии так было написано, работает и ладно
        return b''.join([0x28.to_bytes(4, order), img.width.to_bytes(4, order), (img.height * 2).to_bytes(4, order), 0x1.to_bytes(2, order), 0x20.to_bytes(2, order), 0x0.to_bytes(4, order), bmpRawSizeCalculator(img.width, img.height).to_bytes(4, order), 0x0.to_bytes(4, order), 0x0.to_bytes(4, order), 0x0.to_bytes(4, order), 0x0.to_bytes(4, order)])
    def getBmp(img): # сырая битмапа
        data = [img.getpixel((x, img.height - y - 1)) for y in range(img.height) for x in range(img.width)]
        return b''.join([getIcoBmpHeader(img)] + [bytearray((b, g, r, a)) for r, g, b, a in data] + [bytearray([0x0 for _ in range(img.height * img.width * 2 // 8 + (1 if (img.height * img.width * 2 % 8) != 0 else 0))])]) # заголовок, цвет и "маска AND" (забитая нулями, я не разобрался но вроде работает)
    def getIconDirEntry(width, height, size, offset): # описание иконки
        return b''.join([bytearray([width, height, 0, 0, 1, 0, 32, 0]), size.to_bytes(4, 'little'), offset.to_bytes(4, 'little')])
    bmps = [getBmp(img.resize(size=(sz, sz), resample=Image.LANCZOS)) for sz in BMPs_sizes] # БМПшки

    # Запись в файл
    with open(outFileName, 'wb') as file:
        file.write(b''.join([0x0.to_bytes(2, 'little'), 0x1.to_bytes(2, 'little'), icon_entries.to_bytes(2, 'little')])) # Заголовок ico
        file.write(getIconDirEntry(0, 0, png_size, ICONDIR_size + ICONDIRENTRY_size * icon_entries)) # описание png
        offset = png_size + ICONDIR_size + ICONDIRENTRY_size * icon_entries
        for size in BMPs_sizes:
            data_size = BMPHEADER_size + bmpRawSizeCalculator(size, size)
            file.write(getIconDirEntry(size, size, data_size, offset)) # описание bmp
            offset += data_size
        file.write(png_byte_arr) # сама png
        for bmp_data in bmps:
            file.write(bmp_data) # сами bmp

if __name__ == "__main__":
    inFileName = "input.png"
    outFileName = "output.ico"
    argc = len(sys.argv)
    if argc > 1:
        inFileName = sys.argv[1]
    if argc > 2:
        outFileName = sys.argv[2]
    convert(inFileName, outFileName)