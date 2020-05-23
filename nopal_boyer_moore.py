import pandas as pd
import re

def badMatchTable(pattern):
    # bikin bad match table
    badTab = dict()
    for idx, char in enumerate(pattern): #p a s s w o r d
        badTab[char] = max(1, len(pattern) - idx - 1)
    else:
        if "star" not in badTab:
            badTab["star"] = len(pattern)

    return badTab

def search(pattern, email, badMatchTab):
    i = 0
    jumlahKetemu = 0
    while(i + len(pattern) <= len(email["message"])):
        pointer = len(pattern) - 1

        while pointer >= 0 and email["message"][i + pointer] == pattern[pointer]:
            pointer -= 1

        if pointer < 0:
            jumlahKetemu += 1
            i += len(pattern)
        else:
            if email["message"][i + pointer] in badMatchTab:
                key = email["message"][i + pointer]
                i += badMatchTab[key]
            else:
                i += badMatchTab["star"]

    hasil_ketemu = {
        "idEmail": email["id"],
        "jumlahKetemu": jumlahKetemu,
        "pattern": pattern
    }

    return hasil_ketemu

def cleansingData(file):
    # open txt
    fraudulent = open(file, "r")

    # bagian cleansing data
    JSON_email = list()
    isi_JSON_email = dict()
    message = list()
    prev = ""
    id = 1
    for aw, row in enumerate(fraudulent):
        # untuk nyari sender nya siapa
        if re.match(r"From:.*?\<?(\w{1,}@\w{1,}\.?\w{1,}]?)\>?", row): # regular expression biar gampang nyari sendernya
            sender = re.match(r"From:.*?\<?(\w{1,}@\w{1,}\.?\w{1,}]?)\>?", row)
            isi_JSON_email["sender"] = sender.group(1) # masukkin sender yang udah ketemu
            prev = "From"

        # untuk nyari reciever nya siapa
        elif prev == "From":
            if re.match(r"^To:\s?(\w{1,}@.{1,})", row): # regular expression biar gampang nyari recievernya
                reciever = re.match(r"^To:\s?(\w{1,}@.{1,})", row)
                isi_JSON_email["reciever"] = reciever.group(1) # masukkin reciever yang udah ketemu
                prev = "To"
        # untuk nyari date nya kapan
        elif prev == "To":
            if re.match(r"^Date: .+", row): # regular expression biar gampang nyari date nya
                date = re.match(r"Date: (.+)", row)
                isi_JSON_email["date"] = date.group(1) # masukkin date yang udah ketemu
                prev = "date"

        elif prev == 'date':
            if "Status:" in row:
                prev = "status"

        elif prev == 'status':
            if row.strip() != "":
                message = [row]
                prev = "message"

        elif prev == "message":
            if "From" not in row:
                message.append(row)
            else:
                prev = 'from'
                isi_message = message.copy()
                isi_JSON_email["message"] = "".join(isi_message)
                isi_JSON_email["id"] = id
                id += 1
                JSON_email.append(isi_JSON_email.copy())

    fraudulent.close()

    return JSON_email

# 1 melakukan clean data
JSON_email = cleansingData("fradulent_emails.txt")

patterns = pd.read_excel("contohpattern.xlsx")

prevId = -1
dictEmail = dict()
for idx, value in enumerate(JSON_email):
    for index in patterns.index:
        badTab = badMatchTable(patterns.loc[index, "namapattern"])

        hasilSearch = search(patterns.loc[index, "namapattern"], value, badTab)

        if patterns.loc[index, "namapattern"] not in dictEmail:
            dictEmail[patterns.loc[index, 'namapattern']] = [hasilSearch["jumlahKetemu"]]
        else:
            dictEmail[patterns.loc[index, 'namapattern']].append(hasilSearch["jumlahKetemu"])

tabelHasil = pd.DataFrame(dictEmail, index=[i for i in range(len(JSON_email))])

print(tabelHasil.loc[0, "urgentresponse"])

for idx in (tabelHasil.sum(axis=1)).index:
    if tabelHasil.sum(axis=1)[idx] > 0:
        print(f"""
        Email ID: {idx} Terindikasi Phising!!!
        Dengan jumlah pattern ditemukan = {tabelHasil.sum(axis=1)[idx]}
""")