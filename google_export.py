# For catching rsa warnings
import warnings

import gspread
from oauth2client.service_account import ServiceAccountCredentials

warnings.filterwarnings("error")


def main(data):
    client = login(None)
    if client == -1:
        print("Проверьте файл аутентификации Google")
        exit()
    main_export(client, data, None, None)


def login(auth_file):
    client = -1
    try:
        if auth_file is None:
            auth_file = str(input("Введите имя файла аутентификации Google\n"))
        scope = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(auth_file, scope)
        client = gspread.authorize(creds)
    except Exception:
        client = -1
    finally:
        return client


def main_export(client, data, sheet_name, wsheet_name):
    if sheet_name is None: sheet_name = input("Введите имя файла таблицы")
    if wsheet_name is None: wsheet_name = input("Введите имя листа таблицы")
    sheet = client.open(sheet_name)
    worksheet = sheet.worksheet(wsheet_name)
    sheet_data = worksheet.get_all_values()

    max_score = data[0][2]
    max_score = int(max_score[max_score.find(" из ") + 4:])

    for answer in data:
        index = find_in_sublists(sheet_data, answer[1])
        iz_index = answer[2].find(" из ")
        answer[2] = int(answer[2][:iz_index])
        if index == -1:
            sheet_data.append(answer)
        else:
            if index < 5:
                answer[2] -= max_score - int(answer[2])
            if answer[0] != "": sheet_data[index][0] = answer[0]
            sheet_data[index][2] = int(sheet_data[index][2]) + answer[2]
    worksheet.update(sheet_data, value_input_option="USER_ENTERED")

    # Сортируем по убыванию баллов
    worksheet.sort([3, "des"])
    print("Вывод в облако произведен без ошибок")


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