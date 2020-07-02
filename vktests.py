import csv
import json
import math
import sys
# Disabling ResourceWarning about unclosed socket
import warnings

import vk

warnings.simplefilter("ignore", ResourceWarning)

# vk-auth.json вида:
# {
# "TOKEN": "",
# "ADMIN_ID": ""
# }
import google_export

with open("vk-auth.json") as vkcredsfile:
    vkcreds = json.load(vkcredsfile)
TOKEN = vkcreds["TOKEN"]
ADMIN_ID = vkcreds["ADMIN_ID"]
v = 5.103


def main():
    data = []
    vkapi = login(TOKEN)
    nums = starting_info(vkapi, ADMIN_ID)
    print(
        f"Выбранная группа — {nums['grpname']}\nВыбранный админ — {nums['admname']}\nВсего сообщений в диалоге — {nums['num']}")
    target_q = str(input("Введите любой вопрос из теста, который нужно проверить...\n\tПример вопроса для "
                         "ввода:\n\t\"Q: У него в сумке лежали учебники для сегодняшних уроков, обед и...\"\n"))
    # target_q = "Q: У него в сумке лежали учебники для сегодняшних уроков, обед и..."
    data = all_for_msgs(vkapi, data, target_q, ADMIN_ID)
    if len(data) == 0:
        print("По запросу не найдено результатов")
    else:
        output(data)


def output(data):
    k = -1
    try:
        k = int(input(
            "Выберите способ вывода:\n1) *.TXT-файл\n2) *.CSV-файл\n3) Экспорт в сводную таблицу Google\nВведите 0 "
            "для выхода\n"))
        if k == 1:
            save_to_txt(data)
        elif k == 2:
            save_to_csv(data)
        elif k == 3:
            status = google_export.main(data)
            print(status)
    except Exception as e:
        print(e)
        pass
    finally:
        if k == 0: sys.exit(0)
        output(data)


def all_for_msgs(vkapi, data, target_q, ADMIN_ID):
    data = taking_msgs(vkapi, data, target_q, ADMIN_ID, "search")
    print(f"Ответов на выбранный тест — {len(data)}")
    data = checking_results(data)
    print(f"Ответов после обработки — {len(data)}")
    return data


def checking_results(data):
    i = 0
    # Сортируем по возрастанию айдишников
    data = sorted(data, key=lambda idsort: idsort[1])
    # Удаляем тех, кто перепроходил тест
    while i + 1 < len(data):
        k = 1
        shit_num = 0
        comp_orig = data[i]
        while k < len(data):
            if i + 1 + shit_num < len(data):
                comp_comp = data[i + 1 + shit_num]
            else:
                break
            if comp_orig[1] == comp_comp[1]:
                shit_num += 1
            else:
                break
            k += 1
        if shit_num > 0:
            del (data[i:i + shit_num + 1])
        else:
            i += 1

    # Удаляем набравших 0 баллов
    i = 0
    while i + 1 < len(data):
        result_text = data[i]
        result_text = result_text[2]
        if result_text[:1] == "0":
            del data[i]
        else:
            i += 1
    # Сортируем по убыванию баллов
    data = sorted(data, key=lambda idsort: idsort[2], reverse=True)

    # Фиксим баги кодировки (приложение "Тесты" не может адекватно выводить восточноазиатские символы)
    i = 0
    while i < len(data):
        name = data[i]
        if "\\u" in name[0]:
            name[0] = name[0].replace("\\/", "/").encode().decode("unicode_escape")
            data[i] = name
        i += 1
    return data


def taking_msgs(vkapi, data, target_q, ADMIN_ID, mode):
    try:
        if mode == "search":
            search_count = vkapi.messages.search(q=target_q, peer_id=ADMIN_ID, count=0)['count']
            if search_count > 10000: raise TooManyAnswersEx
        else:
            # if 'all'
            search_count = vkapi.messages.getHistory(peer_id=ADMIN_ID, user_id=ADMIN_ID, count=0)['count']
        offset = 0
        for _ in range(math.ceil(search_count / 100)):
            if mode == "search":
                msgs = vkapi.messages.search(q=target_q, peer_id=ADMIN_ID, count=100, offset=offset)['items']
            else:
                # if 'all'
                msgs = vkapi.messages.getHistory(peer_id=ADMIN_ID, user_id=ADMIN_ID, count=200, offset=offset)['items']
            offset += len(msgs)
            msgs_len = len(msgs) - 1
            while msgs_len != -1:
                if msgs[msgs_len]["out"] == 1:
                    msg = msgs[msgs_len]["text"]
                    name_start_index = 20
                    name_end_index = msg.find(" vk.com/")
                    id_start_index = msg.find("/id") + 1
                    id_end_index = msg.find("Диалог:") - 1
                    score_start_index = msg.find("Набрано баллов ") + 15
                    # score_end_index = msg.find(" из ")
                    score_end_index = msg.find("Q: ") - 2

                    name = msg[name_start_index:name_end_index]
                    id_ = msg[id_start_index:id_end_index]
                    score = msg[score_start_index:score_end_index]
                    if target_q in msg:
                        data.append([name, id_, score])
                    msgs_len -= 1
                else:
                    msgs_len -= 1


    except TooManyAnswersEx:
        data = taking_msgs(vkapi, data, target_q, ADMIN_ID, "all")
    finally:
        return data


def login(TOKEN):
    session = vk.Session(access_token=TOKEN)
    return vk.API(session, v=v)


def starting_info(vkapi, ADMIN_ID):
    num_of_msgs = vkapi.messages.getHistory(peer_id=ADMIN_ID, user_id=ADMIN_ID, count=0)["count"]
    grpname = vkapi.messages.search(q="Новый ответ в тесте", peer_id=ADMIN_ID, count=1)["items"][0]['from_id']
    grpname = vkapi.groups.getById(grop_id=grpname)[0]['name']
    admname = vkapi.users.get(user_ids=ADMIN_ID, name_case="Nom")[0]
    admname = admname["first_name"] + " " + admname["last_name"]
    return {"grpname": grpname, "admname": admname, "num": num_of_msgs}


def save_to_txt(data):
    try:
        with open("test-results.txt", "w") as file:
            for item in data:
                k = 1
                for sub_item in item:
                    if k == 1:
                        file.write("| " + sub_item.ljust(25, " ") + " | ")
                    elif k == 2:
                        file.write(sub_item.ljust(13, " ") + " | ")
                    else:
                        file.write(sub_item.ljust(4, " ") + " |\n")
                    k += 1
        print("Вывод в test-results.txt прошел успешно")
    except Exception:
        print("Что-то пошло не так...")


def save_to_csv(data):
    try:
        with open("test-results.csv", "w") as file:
            write_file = csv.writer(file, dialect="excel")

            for item in data:
                write_file.writerow(item)
        print("Вывод в test-results.csv прошел успешно")
    except Exception:
        print("Что-то пошло не так...")


class TooManyAnswersEx(Exception):
    """Raised when the number of searched answers exceeds 10,000"""
    pass


if __name__ == "__main__":
    main()
