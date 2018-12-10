import re
import os
import psycopg2
from psycopg2 import sql
from decouple import config
from flask import (
    Flask, request, abort
)
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
app = Flask(__name__)
# get LINE_CHANNEL_ACCESS_TOKEN from your environment variable
line_bot_api = LineBotApi(
    config("LINE_CHANNEL_ACCESS_TOKEN",
           default=os.environ.get('LINE_ACCESS_TOKEN'))
)
# get LINE_CHANNEL_SECRET from your environment variable
handler = WebhookHandler(
    config("LINE_CHANNEL_SECRET",
           default=os.environ.get('LINE_CHANNEL_SECRET'))
)
connection = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
connection.set_session(autocommit=True)

cursor = connection.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS glv(uniq text, PRIMARY KEY(uniq), presale integer DEFAULT 1, count integer DEFAULT 0, countb integer DEFAULT 0, count1 integer DEFAULT 0, count2 integer DEFAULT 0, count3 integer DEFAULT 0, countcbt integer DEFAULT 0);')
cursor.execute('SELECT EXISTS(SELECT uniq FROM glv WHERE uniq=%s)', ('u',))
if (not cursor.fetchone()[0]):
    cursor.execute("INSERT into glv(uniq, presale, count, count1, countb, count2, count3) values (%s, 1, 0, 0, 0, 0, 0);", ('u',))
cursor.execute("CREATE TABLE IF NOT EXISTS gst19(user_id text, PRIMARY KEY(user_id), state integer DEFAULT 0, nama text, sekolah text, no_hp text, id_line text, bidang text, test text, fakultas1 text, fakultas2 text, fakultas3 text, presale integer DEFAULT 0, noref text, bayar integer DEFAULT 0, notiket text, stamp timestamp);")

questions = {
    1: "Siapa nama kamu?",

    2: "Kamu sekolah dimana?",

    3: "Nomor HP kamu berapa?\n('-' jika tidak ada)",

    4: "Apa ID Line kamu?\n('-' jika tidak ada)",

    5: "Kamu pilih bidang apa?\n(pilih SAINTEK atau SOSHUM)",

    6: "Tipe test yang mau diiikuti?\n(pilih PBT atau CBT)",

    7: "Pilihan fakultas ke-1?\n(pilih salah satu: FMIPA, FTI, FTMD, FITB, FTTM, FTSL, FSRD, STEI, SBM, SITHR, SITHS, SAPPK, SF",

    8: "Pilihan fakultas ke-2?\n(pilih salah satu: FMIPA, FTI, FTMD, FITB, FTTM, FTSL, FSRD, STEI, SBM, SITHR, SITHS, SAPPK, SF",
    
    9: "Pilihan fakultas ke-3?\n(pilih salah satu: FMIPA, FTI, FTMD, FITB, FTTM, FTSL, FSRD, STEI, SBM, SITHR, SITHS, SAPPK, SF",
}

stepVar = {
    1: 'nama',
    2: 'sekolah',
    3: 'no_hp',
    4: 'id_line',
    5: 'bidang',
    6: 'test',
    7: 'fakultas1',
    8: 'fakultas2',
    9: 'fakultas3',
    10: False,
    11: False,
    -1: 'nama',
    -2: 'sekolah',
    -3: 'no_hp',
    -4: 'id_line',
    -5: 'bidang',
    -6: 'test',
    -7: 'fakultas1',
    -8: 'fakultas2',
    -9: 'fakultas3',
}

nextStep = {
    1: 2,
    2: 3,
    3: 4,
    4: 5,
    5: 6,
    6: 7,
    7: 8,
    8: 9,
    9: 10,
    10: 11,
    11: 12,
    -1: 10,
    -2: 10,
    -3: 10,
    -4: 10,
    -5: 10,
    -6: 10,
    -7: 10,
    -8: 10,
    -9: 10
}

optional = {
    3: True,
    4: True,
    -3: True,
    -4: True,
}

reRegex = {
    3: r'^[0-9]*$',
    -3: r'^[0-9]*$',
}

chList = {
    5: ['SAINTEK', 'SOSHUM'],
    6: ['PBT', 'CBT'],
    7: ['FMIPA', 'FTI', 'FTMD', 'FITB', 'FTTM', 'FTSL', 'FSRD', 'STEI', 'SBM', 'SITHR', 'SITHS', 'SAPPK', 'SF'],
    8: ['FMIPA', 'FTI', 'FTMD', 'FITB', 'FTTM', 'FTSL', 'FSRD', 'STEI', 'SBM', 'SITHR', 'SITHS', 'SAPPK', 'SF'],
    9: ['FMIPA', 'FTI', 'FTMD', 'FITB', 'FTTM', 'FTSL', 'FSRD', 'STEI', 'SBM', 'SITHR', 'SITHS', 'SAPPK', 'SF'],
    -5: ['SAINTEK', 'SOSHUM'],
    -6: ['PBT', 'CBT'],
    -7: ['FMIPA', 'FTI', 'FTMD', 'FITB', 'FTTM', 'FTSL', 'FSRD', 'STEI', 'SBM', 'SITHR', 'SITHS', 'SAPPK', 'SF'],
    -8: ['FMIPA', 'FTI', 'FTMD', 'FITB', 'FTTM', 'FTSL', 'FSRD', 'STEI', 'SBM', 'SITHR', 'SITHS', 'SAPPK', 'SF'],
    -9: ['FMIPA', 'FTI', 'FTMD', 'FITB', 'FTTM', 'FTSL', 'FSRD', 'STEI', 'SBM', 'SITHR', 'SITHS', 'SAPPK', 'SF'],
}

faultyReplies = {
    3: 'Coba periksa lagi nomor yang kamu tulis.\n\n',
    5: 'Sepertinya bidang yang kamu pilih tidak ada. Coba periksa lagi.\n\n',
    6: 'Sepertinya tipe test yang kamu pilih tidak ada. Coba periksa lagi.\n\n',
    7: 'Sepertinya fakultas yang kamu pilih tidak ada. Coba periksa lagi.\n\n',
    8: 'Sepertinya fakultas yang kamu pilih tidak ada. Coba periksa lagi.\n\n',
    9:  'Sepertinya fakultas yang kamu pilih tidak ada. Coba periksa lagi.\n\n',
}

kuotapresale = {
    1: 200,
    2: 400,
    3: 150,
}


def registCommand(message, user, firstrun):
    cursor.execute("select state from gst19 where user_id=%s", (user,))
    step = cursor.fetchone()[0]
    cursor.execute('select presale from glv where  uniq=%s', ('u',))
    nopresale = cursor.fetchone()[0]
    cursor.execute('select count from glv where  uniq=%s', ('u',))
    count = cursor.fetchone()[0]
    reply = ''

    if not firstrun:
        if (stepVar[step] is not False): # Normal processes
            if (step in optional and message == '-') or ((step not in reRegex) and (step not in chList)) or (step in reRegex and re.match(reRegex[step], message)) or ((step in chList) and (message.upper() in chList[step])):
                cursor.execute(sql.SQL("update gst19 set {}=%s where user_id=%s").format(sql.Identifier(stepVar[step])), (message, user))
                step = nextStep[step]
                cursor.execute("update gst19 set state=%s where user_id=%s", (step, user))
            else:
                if (abs(step) in faultyReplies):
                    reply += faultyReplies[abs(step)]
        else: # uniq processes
            if step == 10:
                if message.lower() == 'konfirmasi':
                    cursor.execute('SELECT count, countcbt from glv where  uniq=%s', ('u',))
                    fobjglv = cursor.fetchone()
                    cursor.execute('select test from gst19 where user_id=%s', (user,))
                    jtest = cursor.fetchone()[0]
                    count = fobjglv[0]
                    countcbt = fobjglv[1]
                    step += 1
                    count += 1
                    if jtest.upper() == 'CBT':
                        if countcbt < 150:
                            countcbt += 1
                            cursor.execute('update glv set countcbt=%s where uniq=%s', (countcbt, 'u'))
                        else:
                            cursor.execute('update gst19 set test=%s where user_id=%s', ('PBT', user))
                            reply += 'Kuota CBT penuh! kamu akan dialihkan ke PBT.\n\n'
                    cursor.execute("update gst19 set state=%s where user_id=%s", (step, user))
                    cursor.execute("update gst19 set stamp=statement_timestamp() where user_id=%s", (user,))
                    cursor.execute('update glv set count=%s where uniq=%s', (count, 'u'))
                    cursor.execute('update gst19 set noref=%s where user_id=%s', (str(190000 + int(count)), user))
                elif re.match(r'^edit [1-9]$', message.lower()):
                    sm = message.split()
                    step = -(int(sm[1]))
                    cursor.execute("update gst19 set state=%s where user_id=%s", (step, user))
                    cursor.execute("update gst19 set stamp=statement_timestamp() where user_id=%s", (user,))
    if abs(step) in questions: # Normal responses
        if step == 6: 
            cursor.execute('select countcbt from glv where uniq=%s', ('u'))
            countcbt = cursor.fetchone()[0]
            reply += questions[abs(step)] + '\n\nKuota untuk tes CBT tersisa ' + str(150 - int(countcbt))
            return reply 
        else:
            reply += questions[abs(step)]
            return reply
    else: # uniq responses
        if step == 10:
            cursor.execute("select state, nama, sekolah, no_hp, id_line, bidang, test, fakultas1, fakultas2, fakultas3 from gst19 where user_id=%s", (user,))
            data = cursor.fetchone()
            reply = (reply + 'Pastikan data kamu benar ya..:\n\n' +
                '1. Nama: ' + data[1] + '\n' +
                '2. Sekolah: ' + data[2] + '\n' +
                '3. No HP: ' + data[3] + '\n' +
                '4. ID Line: ' + data[4] + '\n' +
                '5. Bidang: ' + data[5] + '\n' +
                '6. Jenis Test: ' + data[6] + '\n' +
                '7. Pilihan 1: ' + data[7] + '\n' +
                '8. Pilihan 2: ' + data[8] + '\n' +
                '9. Pilihan 3: ' + data[9] + '\n\n' +
                'Jika sudah benar, silakan ketik \'konfirmasi\'. jika ada data yang ingin diubah, silakan ketik \'edit\' beserta poin yang ingin diubah. (Contoh: \'edit 4\' untuk mengubah data ID Line)')
            return reply
        if step == 11: 
            cursor.execute('select noref from gst19 where user_id=%s', (user,))
            noreft = cursor.fetchone()[0]
            reply += ('Terima kasih telah mendaftar Ganeshout 2019! Berikut adalah nomor referensi pembayaran kamu: ' + str(noreft) + '\n\nUntuk pembayaran tiketnya kamu bisa mentransfer ke rekening di bawah dan mengirimkan bukti pembayaran dengan nomor referensi yang kamu dapatkan barusan ke salah satu CP di bawah ini:\n\n' +
                'Vailovaya\nidline: vailovayash\n1330015264856 (mandiri) a.n. Vailovaya Sinya H\n\n' + 
                'Hanziz\nidline: hanziz\n2221-01-017359-50-1 (BRI) a.n. Muhammad Raihan Aziz\n\n' + 
                'Davita\nidline: davitaf9\n0953815611 (BCA) a.n. Davita Fauziyyah Widodo\n\n' + 
                'D\'lora\nidline: loraloreng\n733523132 (BNI) a.n. D\'lora Barada Wahab')
            return reply
                    
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']


    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)


    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)


    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    id = event.source.user_id
    reply = ""
    txsp = text.split()

    cursor.execute("select exists(select user_id from gst19 where user_id=%s)", (id,))
    # not in database
    if (not cursor.fetchone()[0]):
        if text.lower() == 'daftar':
            cursor.execute("insert into gst19(user_id, stamp, state) values (%s, statement_timestamp(), 1);", (id,))
            reply = registCommand(text, id, True)
        elif text.lower() == 'tiket':
            reply = 'Kamu belum melakukan pendaftaran! Silakan ketik \'daftar\' untuk mendaftar.'
        elif text.lower() == 'kuota':
            cursor.execute('select presale, count1, count2, count3 from glv where  uniq=%s;', ('u',))
            fobj = cursor.fetchone()
            nopresale = fobj[0]
            prescount = fobj[nopresale]
            reply = 'Tiket Ganeshout 2019 Presale ' + str(nopresale) + ' tersisa ' + str(kuotapresale[nopresale] - prescount) + ' lembar.'
        elif text.lower() == 'tutorial':
            reply = 'https://youtu.be/FPbLwgzQTeI'
        elif txsp[0] == '/gst19op':
            if txsp[1] == 'statref':
                cursor.execute('select exists(select user_id, nama, noref, bayar, notiket from gst19 where noref=%s);', (txsp[2],))
                udata = cursor.fetchone()
                if not udata[0]:
                    reply = 'tidak ada  user dengan noref ' + txsp[2]
                else:
                    cursor.execute('select * from gst19 where noref=%s;', (txsp[2],))
                    udata = cursor.fetchone()
                    for i in range(len(udata)):
                        reply += (str(udata[i]) + ' ')
                    #reply = str(udata[1]) + ' ' + str(udata[2]) + ' ' + str(udata[3]) + ' ' + str(udata[4])
            elif txsp[1] == 'validate':
                cursor.execute('select exists(select user_id, nama, noref, bayar, notiket from gst19 where noref=%s);', (txsp[2],))
                udata = cursor.fetchone()
                if not udata[0]:
                    reply = 'tidak ada  user dengan noref ' + str(txsp[2])
                else:
                    cursor.execute('select user_id, nama, noref, bayar, notiket from gst19 where noref=%s;', (txsp[2],))
                    udata = cursor.fetchone()
                    if udata[3] == 0:
                        cursor.execute('select presale, countb, count1, count2, count3 from glv where  uniq=%s;', ('u',))
                        fobj = cursor.fetchone()
                        nopresale = fobj[0]
                        countb = fobj[1]
                        countp = fobj[nopresale + 1]
                        countp += 1
                        countb += 1
                        cursor.execute('update glv set countb=%s where uniq=%s;', (countb, 'u'))
                        cursor.execute('update glv set count' + str(nopresale) + '=%s where uniq=%s;', (countp, 'u'))
                        cursor.execute('update gst19 set bayar=1 where noref=%s;', (txsp[2],))
                        cursor.execute('update gst19 set notiket=%s where noref=%s;', ('022-01-' + str(10000 + countb), txsp[2]))
                        reply = 'user dengan noref ' + str(txsp[2]) + 'valid id: ' + str(nopresale) + ' ' + str(countp) + ' notiket: ' + '022-01-' + str(10000 + countb)
                    else:
                        reply = 'user dengan noref ' + str(txsp[2]) + 'sudah membayar '
                        for i in range(len(udata)):
                            reply += (str(udata[i]) + ' ')
            elif txsp[1] == 'resetdatabase' and txsp[2] == 'iamresponsible':
                reply = 'Database direset!'
                cursor.execute('DELETE FROM gst19')
                cursor.execute('DELETE FROM glv')
                cursor.execute("INSERT into glv(uniq, presale, count, count1, countb, count2, count3) values (%s, 1, 0, 0, 0, 0, 0);", ('u',))
            elif txsp[1] == 'datastatus':
                cursor.execute('SELECT * FROM glv where uniq=%s', ('u'))
                fobj = cursor.fetchone()
                for i in range(len(fobj)):
                    reply += (str(fobj[i]) + ' ')
            elif txsp[1] == 'setpresale' and re.match(r'^[1-3]$', txsp[2]):
                prs = txsp[2]
                cursor.execute('UPDATE glv set presale=%s where uniq=%s', (int(prs), 'u'))
                reply = 'update ke presale' + txsp[2]
            else:
                reply = 'Hello there, you little sneaky...\n\nRelease 11-12-18'
        else:
            reply = "ketik \'daftar\' untuk mendaftar atau \'kuota\' untuk melihat kuota tiket."
    
    # in database
    else:
        cursor.execute("select state from gst19 where user_id=%s", (id,))
        step = abs(cursor.fetchone()[0])
        if text.lower() == 'daftar':
            if step > 0 and step < 11:
                reply = "Kamu sedang melakukan pendaftaran!"
            else:
                reply = "Kamu sudah melakukan pendaftaran! untuk melihat tiket kamu ketik \'tiket\'."
        elif text.lower() == 'tiket':
            cursor.execute('select bayar from gst19 where user_id=%s', (id,))
            bayar = cursor.fetchone()[0]
            cursor.execute('select nama from gst19 where user_id=%s', (id,))
            namalengkap = cursor.fetchone()[0]
            if step > 0 and step < 11:
                reply = "Kamu belum menyelesaikan pendaftaran!"
            elif bayar == 1:
                cursor.execute('select notiket, bidang, test from gst19 where user_id=%s', (id,))
                fobj = cursor.fetchone()
                nomortiket, jbidang, jtest = fobj[0], fobj[1], fobj[2]
                reply = ("Hai, " + namalengkap + '! ini tiket masuk Ganeshout kamu!\n\nPerlihatkan tiket ini ke kakak yang ada di meja registrasi ulang saat hari-H ya!\n\n' +
                    'Nama: ' + namalengkap + '\nNo. Tiket: ' + nomortiket + '\n' + jbidang + ' - ' + jtest)
                if jtest.upper() == 'CBT':
                    reply += '\n\nJangan lupa untuk membawa laptop atau smartphone saat hari-H!'
            else: #belum bayar
                cursor.execute('select noref from gst19 where user_id=%s', (id,))
                noreff = cursor.fetchone()[0]
                reply = ("Hai, " + namalengkap + '! Sepertinya kamu belum bayar tiket ya?\n\nKalo merasa udah bayar, segera lakukan konfirmasi pembayaran ke kakak CP nya ya..' +
                    '\n\nKalo udah konfirmasi juga, tunggu aja ya..\n\nNomor Referensi: ' + str(noreff))
        elif text.lower() == 'kuota':
            cursor.execute('select presale from glv where  uniq=%s', ('u',))
            nopresale = cursor.fetchone()[0]
            cursor.execute('select count' + str(nopresale) + ' from glv where  uniq=%s', ('u',))
            prescount = cursor.fetchone()[0]
            reply = 'Tiket Ganeshout 2019 Presale ' + str(nopresale) + ' tersisa ' + str(kuotapresale[nopresale] - prescount) + ' lembar.'
        elif text.lower() == 'tutorial':
            reply = 'https://youtu.be/FPbLwgzQTeI'
        elif text.lower() == 'ganti pbt':
            if step >= 11:
                cursor.execute('select test from gst19 where user_id=%s', (id,))
                jtest = cursor.fetchone()[0]
                if jtest.upper() == 'CBT':
                    reply += 'Kamu akan mengganti jenis test menjadi PBT. Perlu diketahui bahwa setelah mengganti jenis test, kamu tidak bisa mengembalikan jenis test ke CBT. Ketik \'Ganti PBT konfirmasi\' untuk konfirmasi.' 
        elif text.lower() == 'ganti pbt konfirmasi':
            if step >= 11:
                cursor.execute('SELECT countcbt from glv where  uniq=%s', ('u',))
                fobjglv = cursor.fetchone()
                cursor.execute('select test from gst19 where user_id=%s', (id,))
                jtest = cursor.fetchone()[0]
                countcbt = fobjglv[0]
                if jtest.upper() == 'CBT':
                    countcbt -= 1
                    cursor.execute('update glv set countcbt=%s where uniq=%s', (countcbt, 'u'))
                    cursor.execute('update gst19 set test=%s where user_id=%s', ('PBT', id))
                    reply += 'Kamu telah mengganti jenis test menjadi PBT.'
        elif txsp[0] == '/gst19op':
            if txsp[1] == 'statref':
                cursor.execute('select exists(select user_id, nama, noref, bayar, notiket from gst19 where noref=%s);', (txsp[2],))
                udata = cursor.fetchone()
                if not udata[0]:
                    reply = 'tidak ada  user dengan noref ' + txsp[2]
                else:
                    cursor.execute('select * from gst19 where noref=%s;', (txsp[2],))
                    udata = cursor.fetchone()
                    for i in range(len(udata)):
                        reply += (str(udata[i]) + ' ')
                    #reply = str(udata[1]) + ' ' + str(udata[2]) + ' ' + str(udata[3]) + ' ' + str(udata[4])
            elif txsp[1] == 'validate':
                cursor.execute('select exists(select user_id, nama, noref, bayar, notiket from gst19 where noref=%s);', (txsp[2],))
                udata = cursor.fetchone()
                if not udata[0]:
                    reply = 'tidak ada  user dengan noref ' + str(txsp[2])
                else:
                    cursor.execute('select user_id, nama, noref, bayar, notiket from gst19 where noref=%s;', (txsp[2],))
                    udata = cursor.fetchone()
                    if udata[3] == 0:
                        cursor.execute('select presale, countb, count1, count2, count3 from glv where  uniq=%s;', ('u',))
                        fobj = cursor.fetchone()
                        nopresale = fobj[0]
                        countb = fobj[1]
                        countp = fobj[nopresale + 1]
                        countp += 1
                        countb += 1
                        cursor.execute('update glv set countb=%s where uniq=%s;', (countb, 'u'))
                        cursor.execute('update glv set count' + str(nopresale) + '=%s where uniq=%s;', (countp, 'u'))
                        cursor.execute('update gst19 set bayar=1 where noref=%s;', (txsp[2],))
                        cursor.execute('update gst19 set notiket=%s where noref=%s;', ('022-01-' + str(10000 + countb), txsp[2]))
                        reply = 'user dengan noref ' + str(txsp[2]) + 'valid id: ' + str(nopresale) + ' ' + str(countp) + ' notiket: ' + '022-01-' + str(10000 + countb)
                    else:
                        reply = 'user dengan noref ' + str(txsp[2]) + 'sudah membayar '
                        for i in range(len(udata)):
                            reply += (str(udata[i]) + ' ')
            elif txsp[1] == 'resetdatabase' and txsp[2] == 'iamresponsible':
                reply = 'Database direset!'
                cursor.execute('DELETE FROM gst19')
                cursor.execute('DELETE FROM glv')
                cursor.execute("INSERT into glv(uniq, presale, count, count1, countb, count2, count3) values (%s, 1, 0, 0, 0, 0, 0);", ('u',))
            elif txsp[1] == 'datastatus':
                cursor.execute('SELECT * FROM glv where uniq=%s', ('u'))
                fobj = cursor.fetchone()
                for i in range(len(fobj)):
                    reply += (str(fobj[i]) + ' ')
            elif txsp[1] == 'setpresale' and re.match(r'^[1-3]$', txsp[2]):
                prs = txsp[2]
                cursor.execute('UPDATE glv set presale=%s where uniq=%s', (int(prs), 'u'))
                reply = 'update ke presale' + txsp[2]
            else:
                reply = 'Hello there, you little sneaky...\n\nRelease 11-12-18'
        else:
            # registration processor
            if step > 0 and step < 11:
                reply = registCommand(text, id, False)
            else:
                reply = "Ketik \'tiket\' untuk melihat tiket kamu."

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )



if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
