import vk
import csv

# from google_export import main_export
# v -- версия API VK
#
# APP_ID -- номер приложения разработчика (меню "Управление")
# GROUP_ID -- айдишник группы
# TOKEN -- токен доступа группы
# ADMIN_ID -- айдишник админа, которому присылаются ответы

v = 5.103
APP_ID = 0
GROUP_ID = 43340456
TOKEN = ""
ADMIN_ID = 0


def main():
    data = []
    offset = 0
    # offset представляет кол-во обработанных сообщений. По нему определяется сдвиг для нового запроса сообщений

    print("Логинимся")
    vkapi = login()
    print("Получаем кол-во сообщений")
    nums = taking_num_of_msgs(vkapi)
    print("Пример вопроса для ввода...")
    print("Q: У него в сумке лежали учебники для сегодняшних уроков, обед и...")
    target_q = str(input("Введите любой вопрос из теста, который нужно проверить: "))
    print("Вытаскиваем ворох сообщений")
    data, offset = taking_msgs(vkapi, nums["iter_num"], 200, offset, data, target_q)
    data, offset = taking_msgs(vkapi, 1, nums["plus_iter_num"], offset, data, target_q)
    print("Ответов на тест --", len(data))
    print("Сортируем результаты")
    data = checking_results(data)
    print("Итоги")
    print(data)
    print("Ответов после обработки --", len(data))

    print("Сохраняем в файл")
    k = int(input(
        "Выберите способ вывода:\n1) *.TXT-файл\n2) *.CSV-файл\n3) Экспорт в сводную таблицу Google (не реализовано)\n"))
    if k == 1:
        save_to_txt(data)
    elif k == 2:
        save_to_csv(data)
    elif k == 3:
        # save_to_google(data)
        print("Брысь отсюда")
        # main_export()
    else:
        print("Что-то не то ввел.")


def login():
    session = vk.Session(access_token=TOKEN)
    return vk.API(session, v=v)


def taking_num_of_msgs(vkapi):
    num_of_msgs = vkapi.messages.getHistory(group_id=GROUP_ID, start_message_id=-1, peer_id=ADMIN_ID, user_id=ADMIN_ID,
                                            count=1,
                                            offset=0)
    print(num_of_msgs)
    iter_num = num_of_msgs["count"] // 200
    plus_iter_num = num_of_msgs["count"] % 200
    return {"iter_num": iter_num, "plus_iter_num": plus_iter_num}


def taking_msgs(vkapi, iter_num, count, offset, data, target_q):
    for i in range(iter_num):
        messages = vkapi.messages.getHistory(group_id=GROUP_ID, start_message_id=-1, peer_id=ADMIN_ID,
                                             user_id=ADMIN_ID,
                                             count=count,
                                             offset=offset)
        msg_items = messages["items"]

        k = 0
        # Определяем индексы начала и конца нужных нам данных, делаем срезы
        while k <= count - 1:
            msg_item = msg_items[k]
            print(k)
            if msg_item["out"] == 1:
                msg = msg_item["text"]

                name_start_index = 20
                name_end_index = msg.find(" vk.com/")
                id_start_index = msg.find("/id") + 1
                id_end_index = msg.find("Диалог") - 1
                score_start_index = msg.find("Набрано баллов ") + 15
                score_end_index = msg.find(" из ")

                name = msg[name_start_index:name_end_index]
                id_ = msg[id_start_index:id_end_index]
                score = msg[score_start_index:score_end_index]
                # print(score)
                # score=int(score)
                if target_q in msg:
                    data.append([name, id_, score])
                k += 1
            else:
                k += 1
        offset += count
    return data, offset


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
        if result_text[0] == "0":
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


def save_to_txt(data):
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


def save_to_csv(data):
    with open("test-results.csv", "w") as file:
        write_file = csv.writer(file, dialect="excel")

        for item in data:
            write_file.writerow(item)


if __name__ == "__main__":
    main()
