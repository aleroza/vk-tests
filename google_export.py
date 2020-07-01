import gspread
from oauth2client.service_account import ServiceAccountCredentials

data = []

def main_export():
    print("Ну что, пешка Навального")
    scope = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("vk-quiz-f13e549a1583.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open("Auto-Mediika")
    worksheet = sheet.worksheet("3 сезон 2020")
    sheet_data = worksheet.get_all_values()

    max_score = data[0][2]
    iz_index = max_score.find(" из ")
    max_score = int(max_score[iz_index + 4:])

    for answer in data:
        index = find_in_sublists(sheet_data, answer[1])
        print(index)
        if index == -1: sheet_data.append(answer)
        else:
            answer[2] = int(answer[2][:iz_index])
            if index < 5:
                answer[2] -= max_score - int(answer[2])
            sheet_data[index][0]=answer[0]
            sheet_data[index][2]= int(sheet_data[index][2]) + answer[2]
            print(type(sheet_data[index][2]))
    worksheet.update(sheet_data, value_input_option="USER_ENTERED")

    # Сортируем по убыванию баллов
    worksheet.sort([3, "des"])

def find_in_sublists(lst, value):
    for i, sublist in enumerate(lst):
        if value in sublist:
            return i
    return -1

    # Google API limit, meh
    # max_score = 0
    # for answer in data:
    #     try:
    #         cell = worksheet.find(answer[1], None, 2)
    #         name, score = worksheet.cell(cell.row, 1), worksheet.cell(cell.row, 3)
    #         if cell.row < 5:
    #             score -= max_score - answer[2]
    #         worksheet.update_cell(cell.row, 3, score)
    #         if name != answer[0]: worksheet.update_cell(cell.row, 1, answer[0])
    #     except gspread.exceptions.CellNotFound:
    #         print("wow, new ppl")
    #         worksheet.insert_row(answer, 2)

    # потом доделать для руры вычитание баллов ошибившихся топов
    # i = 2
    # top = []
    # for i in range(2, 5):
    #     top.append(worksheet.cell(int(i), 2).value)
    #
    # max_score = data[0][2]
    # iz_index = max_score.find(" из ")
    # max_score = int(max_score[iz_index + 4:])
    #
    # Убераем лишнее из баллов. Можно не убирать, но раскомментировать другой вариант score_end_index.
    # for item in data:
    #     sub_item = item[2]
    #     item[2] = sub_item[:iz_index]
    #     if item[1] in top:
    #         print(item[2])
    #         item[2] = (-max_score + int(item[2]))
    #         if item[2] == 0: item[2] = max_score
    #         print(item[1], item[2])
    #         print(max_score)


if __name__ == '__main__':
    main_export()