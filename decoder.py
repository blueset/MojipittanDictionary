import struct
import json

aid_data = open("worddata.aid", "rb").read()
cot_data = open("worddata.cot", "rb").read()
dic_data = open("worddata.dic", "rb").read()

class WordContentSet:
    # WordContentSet$$.ctor
    def __init__(self, index):
        index = index << 3
        self.diff_data = (cot_data[index] << 0x18) + (cot_data[index + 1] << 0x10) + (cot_data[index + 2] << 0x08) + (cot_data[index + 3] << 0x00)
        self.key_offset = cot_data[index + 4]
        self.notation_offset = cot_data[index + 5]
        self.meaning_offset = cot_data[index + 6]
        self.data_size = cot_data[index + 7]

    # WordContentSet$$get_m_nDataOffset
    def data_offset(self):
        return self.diff_data & 0x0FFFFFFF
    
    # WordContentSet$$get_m_nReadingKeyOfsFlag
    def reading_key_offset_flag(self):
        return bool(self.key_offset >> 7)

def shiftjis_to_str(data, start, len):
    try:
        return data[start:start + len].decode("shift_jis")
    except:
        return data[start:start + len]

class WordIndexOffset:
    # WordIndexOffset$$.ctor
    def __init__(self, index):
        offset = index
        data_len = struct.calcsize(">llll")
        self.index_table, self.index_table_size, self.index, self.index_size = struct.unpack(">llll", dic_data[offset:offset + data_len])

class WordDataHeader:
    # WordDataHeader$$.ctor
    def __init__(self):
        self.file_type = dic_data[0:4]
        offset = 4
        data_len = struct.calcsize(">Lll")
        self.file_version, self.stat_offset, self.stat_size = struct.unpack(">Lll", dic_data[offset:offset + data_len])
        offset += data_len

        self.word_idx_offsets = []
        for _ in range(8):        
            data_len = struct.calcsize(">llll")
            self.word_idx_offsets.append(WordIndexOffset(offset))
            offset += data_len
    
        data_len = struct.calcsize(">lllllllll")
        (self.m_nIdNum, 
        self.nu_book_num, 
        self.nu_notebook_id, 
        self.m_nContentOffset, 
        self.m_nContentSize, 
        self.nu_book_offset, 
        self.nu_book_data_size, 
        self.nu_persistent_id_offset, 
        self.nu_persistent_id_max) = struct.unpack(">lllllllll", dic_data[offset:offset + data_len])
        offset += data_len

        self.reserved = dic_data[offset:offset + 0xC]
        offset += 0xC
        self.source_version = dic_data[offset:offset + 0x20]
        offset += 0x20
        self.convert_version = dic_data[offset:offset + 0x20]
        offset += 0x20

word_data_header = WordDataHeader()
kana_map = " あいうえおかがきぎくぐけげこごさざしじすずせぜそぞただちぢつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもやゆよらりるれろわをんー"

# CDictionary$$GetDictionaryData
def get_dictionary_data(index):
    word_cont_set = WordContentSet(index)
    data_offset = word_cont_set.data_offset()
    notation_offset = word_cont_set.notation_offset
    meaning_offset = word_cont_set.meaning_offset
    data_size = word_cont_set.data_size

    if not word_cont_set.reading_key_offset_flag():
        reading = shiftjis_to_str(dic_data, data_offset, notation_offset)
    else:
        key = struct.unpack(">L", dic_data[data_offset:data_offset + 4])[0]
        key3 = (key & 0x7fffffff) + 3
        offsets = word_data_header.word_idx_offsets
        uint_arr = [0, 0]

        idx = 0
        offsets_key3 = key3 + offsets[0].index
        for idx in range(2):
            offsets_key3 = key3 + offsets[0].index
            val3, val2, val1, val0 = dic_data[offsets_key3 - 3:offsets_key3 + 1]
            uint_arr[idx] = (val3 << 0x18) + (val2 << 0x10) + (val1 << 0x08) + (val0 << 0x00)
            key3 += 4

        kanas = []
        uint_16 = uint_arr[0]
        if key & 0x80000000:
            uint_16 += uint_arr[1] << 32
        while uint_16:
            if uint_16 & 0x7f == 0:
                break
            kanas.append(uint_16 & 0x7f)
            uint_16 = uint_16 >> 7

        reading = "".join(kana_map[kana] for kana in kanas)
    
    notation = shiftjis_to_str(dic_data, data_offset + notation_offset, meaning_offset - notation_offset)
    notation = notation.replace("a?a?", "açaí")
    notation = notation.replace("caf?", "café")
    notation = notation.replace("clich?", "cliché")


    meaning_start = data_offset + meaning_offset
    meaning_size = data_size - meaning_offset
    while dic_data[meaning_start + meaning_size - 1] == 0:
        meaning_size -= 1

    meaning = shiftjis_to_str(dic_data, meaning_start, meaning_size)

    return reading, notation, meaning

if __name__ == "__main__":
    total_words = len(cot_data) >> 3
    dictionary = []
    for i in range(1, total_words):
        reading, notation, meaning = get_dictionary_data(i)
        dictionary.append({"reading": reading, "notation": notation, "meaning": meaning})
    with open("dictionary.json", "w") as f:
        json.dump(dictionary, f, ensure_ascii=False, indent=2)
