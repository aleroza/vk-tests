import vk

v = 5.103 # Версия API VK
APP_ID =  # <—— Номер приложения разработчика
GROUP_ID = 43340456  # <—— Айдишник группы
TOKEN = ""  # <—— Токен доступа группы
ADMIN_ID =  # <—— Айдишник админа, которому присылаются ответы
DATA = []
offset = 0 # Кол-во обработанных сообщений. По нему определяется сдвиг для нового запроса сообщений


def main():
    global TARGET_Q

    print("Логинимся")
    __login__()
    print("Получаем кол-во сообщений")
    __numOfMsgs__()
    print("Пример вопроса для ввода...")
    print("Q: У него в сумке лежали учебники для сегодняшних уроков, обед и...")
    TARGET_Q = str(input("Введите любой вопрос из теста, который нужно проверить: "))
    print("Вытаскиваем ворох сообщений")
    __takingMsgs__(iter20Num, 20)
    __takingMsgs__(1, plusIter20Num)
    print("Ответов на тест --", len(DATA))
    print("Сортируем результаты")
    __checkingResults__()
    print("Итоги")
    print(DATA)
    print("Ответов после обработки --", len(DATA))

    print("Сохраняем в файл")
    __save__()



def __login__():
    global vkapi
    session = vk.Session(access_token=TOKEN)
    vkapi = vk.API(session, v=v)


def __numOfMsgs__():
    global iter20Num
    global plusIter20Num
    numOfMsgs = vkapi.messages.getHistory(group_id=GROUP_ID, start_message_id=-1, peer_id=ADMIN_ID, user_id=ADMIN_ID,
                                          count=1,
                                          offset=0)
    iter20Num = numOfMsgs["count"] // 20
    plusIter20Num = numOfMsgs["count"] % 20


def __takingMsgs__(iterNum, count):
    global offset
    global DATA

    for i in range(iterNum):
        messages = vkapi.messages.getHistory(group_id=GROUP_ID, start_message_id=-1, peer_id=ADMIN_ID,
                                             user_id=ADMIN_ID,
                                             count=count,
                                             offset=offset)
        msgItems = messages["items"]

        k = 0
        while k <= count-1: # Определяем индексы начала и конца нужных нам данных, делаем срезы
            msgItem = msgItems[k]
            msg = msgItem["text"]

            nameStartIndex = 20
            nameEndIndex = msg.find(" vk.com/")
            idStartIndex = msg.find("/id")
            idEndIndex = msg.find("Диалог") - 1
            scoreStartIndex = msg.find("Набрано баллов ") + 15
            scoreEndIndex = msg.find("Q: ") - 2

            name = msg[nameStartIndex:nameEndIndex]
            id = msg[idStartIndex:idEndIndex]
            score = msg[scoreStartIndex:scoreEndIndex]
            if TARGET_Q in msg:
                DATA.append([name, id, score])
            k += 1
        offset += count


def __checkingResults__():
    global DATA
    i=0
    DATA=sorted(DATA, key=lambda idsort: idsort[1]) # Сортируем по возрастанию айдишников
    # Удаляем тех, кто перепроходил тест
    while i + 1 < len(DATA):
        k = 1
        shitNum = 0
        compOrig = DATA[i]
        while k < len(DATA):
            if i + 1 + shitNum<len(DATA):
                compComp = DATA[i + 1 + shitNum]
            else: break
            if compOrig[1] == compComp[1]:
                shitNum += 1
            else:
                break
            k += 1
        if shitNum > 0:
            del (DATA[i:i+shitNum + 1])
        else:
            i += 1

    # Удаляем набравших 0 баллов
    i = 0
    while i + 1 < len(DATA):
        resultText=DATA[i]
        resultText=resultText[2]
        if  resultText[0]=="0":
            del DATA[i]
        else: i+=1
    DATA = sorted(DATA, key=lambda idsort: idsort[2], reverse=True) #Сортируем по убыванию баллов

def __save__():
    file = open("test-results.txt", "w")
    for item in DATA:
        file.write("\n|")
        for subItem in item:
            file.write(subItem + " | ")
    file.close()

if __name__ == "__main__":
    main()
