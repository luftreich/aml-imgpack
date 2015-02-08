import sys
import struct
import argparse
import binascii


IH_MAGIC = 0x27051956  # Image Magic Number
IH_NMLEN = 32   # Image Name Length

AML_RES_IMG_VERSION_V1 = 0x01
AML_RES_IMG_VERSION_V2 = 0x02
AML_RES_IMG_ITEM_ALIGN_SZ = 16
AML_RES_IMG_VERSION = 0x01
AML_RES_IMG_V1_MAGIC_LEN = 8
AML_RES_IMG_V1_MAGIC = "AML_RES!" # 8 chars
AML_RES_IMG_HEAD_SZ = AML_RES_IMG_ITEM_ALIGN_SZ * 4 # 64
AML_RES_ITEM_HEAD_SZ = AML_RES_IMG_ITEM_ALIGN_SZ * 4 # 64
IH_MAGIC = 0x27051956 # Image Magic Number
IH_NMLEN = 32 # Image Name Length

ARCH_ARM = 8

# typedef struct {
#     __u32   crc;    //crc32 value for the resouces image
#     __s32   version;//current version is 0x01
#     __u8    magic[AML_RES_IMG_V1_MAGIC_LEN];  //resources images magic
#     __u32   imgSz;  //total image size in byte
#     __u32   imgItemNum;//total item packed in the image
#     __u32   alignSz;//AML_RES_IMG_ITEM_ALIGN_SZ
#     __u8    reserv[AML_RES_IMG_HEAD_SZ - 8 * 3 - 4];
# }AmlResImgHead_t;

# typedef struct pack_header{
#     unsigned int    magic;  /* Image Header Magic Number    */
#     unsigned int    hcrc;   /* Image Header CRC Checksum    */
#     unsigned int    size;   /* Image Data Size      */
#     unsigned int    start;  /* item data offset in the image*/
#     unsigned int    end;    /* Entry Point Address      */
#     unsigned int    next;   /* Next item head offset in the image*/
#     unsigned int    dcrc;   /* Image Data CRC Checksum  */
#     unsigned char   index;  /* Operating System     */
#     unsigned char   nums;   /* CPU architecture     */
#     unsigned char   type;   /* Image Type           */
#     unsigned char   comp;   /* Compression Type     */
#     char    name[IH_NMLEN]; /* Image Name       */
# }AmlResItemHead_t;

class AmlResourcesImage(object):
    def __init__(self):
        self.header = AmlResImgHead()
        self.items = []

    @classmethod
    def unpack_from(cls, fp):
        img = cls()
        fp.seek(0)
        img.header = AmlResImgHead.unpack_from(fp)
        while True:
            item = AmlResItem.unpack_from(fp)
            img.items.append(item)
            if item.next == 0:
                break
            fp.seek(item.next)
        return img

    def pack(self):
        self.header.imgItemNum = len(self.items)
        self.header.imgSz = 0
        packed = self.header.pack()
        for item in self.items():
            packed += item.pack()

class AmlResItem(object):
    _format = "IIIIIIIBBBB%ss" % IH_NMLEN
    size = struct.calcsize(_format)
    magic = IH_MAGIC


    @classmethod
    def unpack_from(cls, fp):
        h = cls()
        h.magic, h.hcrc, h.size, h.start, h.end, h.next, h.dcrc, h.index, \
        h.nums, h.type, h.comp, h.name = struct.unpack(h._format, fp.read(h.size))
        h.name = h.name.rstrip('\0')
        if h.magic != IH_MAGIC:
            raise Exception("Invalid item header magic, should 0x%x, is 0x%x", \
                IH_MAGIC, h.magic)
        fp.seek(h.start)
        h.data = fp.read(h.size)
        return h

    def pack(self):
        return struct.pack(self._format, self.magic, self.hcrc, self.size, \
            self.start, self.end, self.next, self.dcrc, self.index, self.nums,
            self.type, self.comp, self.name) + self.data

    def __repr__(self):
        return "AmlResItem(name=%s start=0x%x size=%d)" % (self.name, self.start, self.size)



class AmlResImgHead(object):
    _format = "Ii%dsIII%ds" % (AML_RES_IMG_V1_MAGIC_LEN, AML_RES_IMG_HEAD_SZ - 8 * 3 - 4)
    size = struct.calcsize(_format)
    magic = AML_RES_IMG_V1_MAGIC
    alignSz = AML_RES_IMG_ITEM_ALIGN_SZ
    version = AML_RES_IMG_VERSION_V2

    @classmethod
    def unpack_from(cls, fp):
        h = cls()
        h.crc, h.version, h.magic, h.imgSz, h.imgItemNum, h.alignSz, \
        h.reserv = struct.unpack(h._format, fp.read(h.size))
        if h.magic != AML_RES_IMG_V1_MAGIC:
            raise Exception("Magic is not right, should %s, is %s" % (AML_RES_IMG_V1_MAGIC, h.magic))
        if h.version > AML_RES_IMG_VERSION_V2:
            raise Exception("res-img version %d not supported" % h.version)
        return h

    def pack(self):
        return struct.pack(self._format, self.crc, self.version, self.magic, \
            self.imgSz, self.imgItemNum, self.alignSz, self.reserv)

    def __repr__(self):
        return "AmlResImgHead(crc=0x%x version=%d imgSz=%d imgItemNum=%d alignSz=%d)" % \
            (self.crc, self.version, self.imgSz, self.imgItemNum, self.alignSz)



def list_items(logo_img_file):
    print "Listing assets in %s" % logo_img_file
    with open(logo_img_file) as fp:
        img = AmlResourcesImage.unpack_from(fp)
        print img.header
        for item in img.items:
            print "    %s" % item
        img.pack()

def unpack_image_file(logo_img_file):
    print "Unpacking assets in %s" % logo_img_file
    with open(logo_img_file) as fp:
        img = AmlResourcesImage.unpack_from(fp)
        for item in img.items:
            print "Unpacking %s" % item.name
            with open("%s.bmp" % item.name, "w") as item_fp:
                item_fp.write(item.data)

def pack_image_file(assets):
    img = AmlResourcesImage()


def main():
    parser = argparse.ArgumentParser(description='Pack and unpack amlogic uboot images')
    parser.add_argument("--unpack", help="Unpack logo.img file", dest='unpack', action="store_true")
    parser.add_argument("--pack", help="Unpack logo.img file", dest="pack", action="store_true")
    parser.add_argument("--logo", help="Source/Destination logo.img file")

    args = parser.parse_args()
    if args.unpack:
        unpack_image_file(args.logo)
    # elif args.pack:
    #     pass
    else:
        list_items(args.logo)

main()