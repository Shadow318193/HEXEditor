import sys

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QTableWidgetItem

import sqlite3


def hex_to_dec(n: str):
    """
    :param n:
    :return int:
    """

    # Функция возвращает шестнадцатиричное число в десятичном представлении.

    ns = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "a": 10,
        "b": 11,
        "c": 12,
        "d": 13,
        "e": 14,
        "f": 15
    }

    new_n = []
    for i in n:
        new_n.append(i.lower())
    new_n.reverse()

    s = 0
    for i in range(len(new_n)):
        s += ns[new_n[i]] * 16 ** i

    return s


def color_item(item: QTableWidgetItem, end: int, byte: int):
    """
    :param item:
    :param end:
    :param byte:
    :return QTableWidgetItem:
    """

    # Клетки окрашиваются в цвета, помогающие определить элементы файла (заголовок и описание).
    # Диапозон байтов зависит от типа файла.

    color = QColor()

    if 0 <= byte <= end:
        # Окраска заголовка.
        color.setRgb(255, 235, 235)
    else:
        # Окраска описания.
        color.setRgb(255, 255, 255)

    item.setBackground(color)  # Окраска ячейки в нужный цвет.

    return item


class HEXEditor(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('hex.ui', self)  # Загрузка интерфейса.
        self.initUI()

        self.can_update = True  # Защита от не нужных обновлений таблицы.

    def initUI(self):
        self.setGeometry(300, 100, 1000, 500)
        self.setWindowTitle('HEX Editor')

        self.opener.clicked.connect(self.open_file)  # Кнопка "Загрузить из файла".
        self.saver.clicked.connect(self.save_file)  # Кнопка "Сохранить файл".
        self.cleaner.clicked.connect(self.clear_data)  # Кнопка "Новый файл".
        self.addBytes.clicked.connect(self.add_byte)  # Кнопка "Добавить строку байтов".
        self.removeBytes.clicked.connect(self.remove_byte)  # Кнопка "Удалить строку байтов".
        self.spinBox.valueChanged.connect(self.update_data)  # Поле для смены кол-ва байт в строке.
        self.tableWidget.cellChanged.connect(self.update_data)  # Реакция на изменение данных в таблице.
        self.addType.clicked.connect(self.add_type)  # Кнопка "Добавить тип файла в БД"
        self.lineEdit.textChanged.connect(self.update_data)  # Реакция на изменение типа файла.

        # Установка шрифтов.
        self.tableWidget.setFont(QFont("MS Sans Serif", 12))
        self.listWidget.setFont(QFont("MS Sans Serif", 12))

        # "it's a beautiful day outside. birds are singing, flowers are blooming...
        #  on days like these, kids like you...
        #  Should be burning in hell."
        #                                           © Санс из Undertale™
        #
        #                      ░░░░░▄▄▀▀▀▀▀▀▀▀▀▄▄░░░░░
        #                      ░░░░█░░░░░░░░░░░░░█░░░░
        #                      ░░░█░░░░░░░░░░▄▄▄░░█░░░
        #                      ░░░█░░▄▄▄░░▄░░███░░█░░░
        #                      ░░░▄█░▄░░░▀▀▀░░░▄░█▄░░░
        #                      ░░░█░░▀█▀█▀█▀█▀█▀░░█░░░
        #                      ░░░▄██▄▄▀▀▀▀▀▀▀▄▄██▄░░░
        #                      ░▄█░█▀▀█▀▀▀█▀▀▀█▀▀█░█▄░
        #                      ▄▀░▄▄▀▄▄▀▀▀▄▀▀▀▄▄▀▄▄░▀▄
        #                      █░░░░▀▄░█▄░░░▄█░▄▀░░░░█
        #                      ░▀▄▄░█░░█▄▄▄▄▄█░░█░▄▄▀░
        #                      ░░░▀██▄▄███████▄▄██▀░░░
        #                      ░░░████████▀████████░░░
        #                      ░░▄▄█▀▀▀▀█░░░█▀▀▀▀█▄▄░░
        #                      ░░▀▄▄▄▄▄▀▀░░░▀▀▄▄▄▄▄▀░░

    def open_file(self):
        # Функция открывает файл и записывает двоичные данные файла в таблицу.

        file_name = QFileDialog.getOpenFileName(self, "Выбрать файл...", "")[0]  # Открытие файла.
        file_type = file_name.split("/")[-1]
        if "." in file_type:
            self.lineEdit.setText(file_type.split(".")[-1].lower())

        try:
            # Открытие файла.
            with open(file_name, mode="rb") as the_file:
                data = list(bytes(the_file.read()))  # Байты записываются в список data.
        except FileNotFoundError:
            # Если пользователь нажмёт кнопку "Отмена", вызовется исключение.
            self.label.setText("Операция отменена.")
        else:
            # Загрузка выполнена успешно.
            self.can_update = False  # Предотвращение выполнения функции update_data().

            # Проверка типа файла на присутсвие в БД
            data_base = sqlite3.connect("file_types.sqlite")
            cursor = data_base.cursor()
            header_end = cursor.execute(f'''
                            SELECT header_end from file_types
                            WHERE type = "{self.lineEdit.text()}"
                            ''').fetchall()

            if header_end:
                header_end_byte = header_end[0][0]
            else:
                header_end_byte = -1

            data_base.close()

            self.listWidget.clear()  # Стираются все символы в виджет-списке.
            self.tableWidget.clear()  # Стираются все данные в таблице.

            # Устанавливается значение байтов в строке из спин-бокса.
            bytes_in_row = int(self.spinBox.text())

            # Таблица подстраивается под размеры данных:
            self.tableWidget.setColumnCount(bytes_in_row)  # Кол-во столбцов.
            self.tableWidget.setRowCount(len(data) // bytes_in_row + 1)  # Кол-во строк.

            # Наименование столбцов шестнадцатиричными числами.
            self.tableWidget.setHorizontalHeaderLabels([hex(x)[2:].upper() for x in range(bytes_in_row)])
            for header in range(bytes_in_row):
                self.tableWidget.horizontalHeaderItem(header).setFont(QFont("MS Sans Serif", 12))

            # Наименование строк:
            if bytes_in_row > 1:
                # Промежутками шестнадцатиричных чисел, если значение из спин-бокса больше, чем 1.
                self.tableWidget.setVerticalHeaderLabels(
                    [f"{hex(x * bytes_in_row)[2:].rjust(2, '0')}-" +
                     f"{hex(x * bytes_in_row + bytes_in_row - 1)[2:].rjust(2, '0')}"
                     for x in range(len(data) // bytes_in_row + 1)]
                )
            else:
                # Шестнадцатиричными числами.
                self.tableWidget.setVerticalHeaderLabels([hex(x)[2:].upper()
                                                          for x in range(self.tableWidget.rowCount() + 1)])

            # Запись данных в таблицу и виджет-список.
            symbols = []

            # В этот список записываются байты, пока их кол-во не станет равно значению из спин-бокса - 1
            # или итератор не прочтёт весь список данных из файла, тогда список сбрасывается и цикл записи
            # начинается заново.

            can_write_start = True  # Защита от записи переменной row.
            row = -1  # Переменная отвечает за запись соответствующего заголовка строки таблицы в виджет-список.

            for byte in range(len(data)):
                # Запись байта в шестнадцатиричном представлении в таблицу.
                cell = QTableWidgetItem(str(hex(data[byte])[2:].rjust(2, "0")))
                cell.setTextAlignment(Qt.AlignCenter)
                cell = color_item(cell, header_end_byte, byte)
                self.tableWidget.setItem(byte // bytes_in_row, byte % bytes_in_row, cell)

                symbols.append(int(data[byte]))  # Запись байта для виджет-списка.
                if byte % bytes_in_row == bytes_in_row - 1 or byte == len(data) - 1:
                    # Длина списка составила достаточно байтов для начала новой строки или данные файла прочтены.

                    # Исправление багов с нумерацией.
                    if row < 0:
                        row = 0
                    if not byte % bytes_in_row and byte == len(data) - 1:
                        row += 1
                    if len(data) == 1:
                        row = 0

                    # Преобразование байтов в видимые основные символы ASCII.
                    symbols = list(map(lambda x: chr(x) if chr(x) in ' !"#$%&()*+,-./0123456789:;<=>?@' +
                                                                     "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`" +
                                                                     "abcdefghijklmnopqrstuvwxyz{|}~']))"
                                                                     else ".", symbols))

                    # Наименование строк:
                    if bytes_in_row > 1:
                        # Промежутками шестнадцатиричных чисел, если значение из спин-бокса больше, чем 1.
                        symbols.insert(0,
                                       f"{hex(row * bytes_in_row)[2:].rjust(2, '0')}-" +
                                       f"{hex(row * bytes_in_row + bytes_in_row - 1)[2:].rjust(2, '0')}")
                    else:
                        # Шестнадцатиричными числами.
                        symbols.insert(0, f"{hex(byte)[2:]}")

                    self.listWidget.addItem("\t".join([x for x in symbols]))  # Запись символов в виджет-список.

                    symbols = []  # Очистка cтроки.
                    can_write_start = True
                elif can_write_start:
                    row += 1
                    can_write_start = False

            # Уведомление пользователя.
            self.label.setText(f"Данные из файла {file_name} загружены!")

            if header_end:
                # Текст появляется, если тип файла присутствует в таблице.
                self.label_type.setText(f"Данный тип файла предусмотрен в программе, " +
                                        f"поэтому заголовок файла будет выделен светло-красным.")

        self.can_update = True

    def save_file(self):
        # Функция сохраняет данные в файл в двоичном виде.
        file_name = QFileDialog.getSaveFileName(self, "Сохранить файл...", "")[0]  # Файл, куда данные сохранятся.

        try:
            # Процесс записи всех байтов в файл.
            data = []
            with open(file_name, mode="wb") as the_file:
                for bytes_in_row in range(self.tableWidget.rowCount()):
                    for byte in range(self.tableWidget.columnCount()):
                        if self.tableWidget.item(bytes_in_row, byte) is not None:
                            data.append(hex_to_dec(self.tableWidget.item(bytes_in_row, byte).text().lower()))
                the_file.write(bytes(data))
        except FileNotFoundError:
            # Если пользователь нажмёт кнопку "Отмена", вызовется исключение.
            self.label.setText("Операция отменена.")
        else:
            # Уведомление пользователя.
            self.label.setText(f"Файл {file_name} сохранён успешно!")

    def add_byte(self):
        # Добавляется строка с конца.
        self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
        bytes_in_row = int(self.spinBox.text())
        # Наименование строк:
        if bytes_in_row > 1:
            # Промежутками шестнадцатиричных чисел, если значение из спин-бокса больше, чем 1.
            self.tableWidget.setVerticalHeaderLabels(
                [f"{hex(x * bytes_in_row)[2:]}-{hex(x * bytes_in_row + bytes_in_row - 1)[2:]}"
                 for x in range(self.tableWidget.rowCount())]
            )
        else:
            # Шестнадцатиричными числами.
            self.tableWidget.setVerticalHeaderLabels(
                [hex(x)[2:] for x in range(self.tableWidget.rowCount() + 1)])
        self.update_data()

    def remove_byte(self):
        # Удаляется строка с конца.
        self.tableWidget.setRowCount(self.tableWidget.rowCount() - 1)
        self.update_data()

    def update_data(self):
        # Активируется при ручном изменении таблицы или других виджетов.
        self.label.setText("")
        self.label_type.setText("")

        if self.can_update:
            self.can_update = False  # Защита от рекурсии.

            # Проверка типа файла на присутсвие в БД.
            data_base = sqlite3.connect("file_types.sqlite")
            cursor = data_base.cursor()
            header_end = cursor.execute(f'''
                            SELECT header_end from file_types
                            WHERE type = "{self.lineEdit.text()}"
                            ''').fetchall()

            if header_end:
                # Тип файла существует в базе.
                header_end_byte = header_end[0][0]
            else:
                header_end_byte = -1

            data_base.close()

            # Перезапись в таблицу.
            data = []

            for bytes_in_row in range(self.tableWidget.rowCount()):
                for byte in range(self.tableWidget.columnCount()):
                    if self.tableWidget.item(bytes_in_row, byte) is not None:
                        the_byte = self.tableWidget.item(bytes_in_row, byte).text()
                        if 1 <= len(the_byte) <= 2:
                            # Проверка числа на правильность.
                            is_correct = True

                            for i in the_byte.lower():
                                if i not in "0123456789abcdef":
                                    is_correct = False
                                    break

                            if is_correct:
                                # Число — шестнадцатиричное.
                                data.append(hex_to_dec(the_byte))
                            else:
                                # Введено не шестнадцатиричное число.
                                data.append(255)
                        elif the_byte != "":
                            # Длина числа не 1 и не 2.
                            data.append(255)

            # Устанавливается значение байтов в строке из спин-бокса.
            bytes_in_row = int(self.spinBox.text())

            self.listWidget.clear()  # Стираются все символы в виджет-списке.

            try:
                button = self.sender().text()
            except AttributeError:
                button = ""  # Превращаем None в пустую строку.

            # Защита некоторых кнопок от не нужного обновления всей таблицы.
            if button != "Добавить строку" and button != "Удалить строку":
                self.tableWidget.clear()
                self.tableWidget.setColumnCount(bytes_in_row)
                self.tableWidget.setRowCount(len(data) // bytes_in_row + 1)
                self.tableWidget.setHorizontalHeaderLabels([hex(x)[2:].upper() for x in range(bytes_in_row)])

                # Наименование строки:
                if bytes_in_row > 1:
                    # Промежутками шестнадцатиричных чисел, если значение из спин-бокса больше, чем 1.
                    self.tableWidget.setVerticalHeaderLabels(
                        [f"{hex(x * bytes_in_row)[2:].rjust(2, '0')}-" +
                         f"{hex(x * bytes_in_row + bytes_in_row - 1)[2:].rjust(2, '0')}"
                         for x in range(len(data) // bytes_in_row + 1)]
                    )
                else:
                    # Шестнадцатиричными числами.
                    self.tableWidget.setVerticalHeaderLabels([hex(x)[2:] for x in range(len(data) + 1)])

            # Установка шрифта.
            for header in range(bytes_in_row):
                self.tableWidget.horizontalHeaderItem(header).setFont(QFont("MS Sans Serif", 12))

            # Запись данных в таблицу и виджет-список.
            symbols = []

            # В этот список записываются байты, пока их кол-во не станет равно значению из спин-бокса - 1
            # или итератор не прочтёт весь список данных из файла, тогда список сбрасывается и цикл записи
            # начинается заново.

            can_write_start = True  # Защита от записи переменной row.
            row = -1  # Переменная отвечает за запись соответствующего заголовка строки таблицы в виджет-список.

            for byte in range(len(data)):
                if button != "Добавить строку" and button != "Удалить строку":
                    # Запись байта в шестнадцатиричном представлении в таблицу.
                    cell = QTableWidgetItem(str(hex(data[byte])[2:].rjust(2, "0")))
                    cell.setTextAlignment(Qt.AlignCenter)
                    cell = color_item(cell, header_end_byte, byte)
                    self.tableWidget.setItem(byte // bytes_in_row, byte % bytes_in_row, cell)

                symbols.append(int(data[byte]))  # Запись байта для виджет-списка.

                if byte % bytes_in_row == bytes_in_row - 1 or byte == len(data) - 1:
                    # Длина списка составила достаточно байтов для начала новой строки или данные файла прочтены.

                    # Исправление багов с нумерацией.
                    if row < 0:
                        row = 0
                    if not byte % bytes_in_row and byte == len(data) - 1:
                        row += 1
                    if len(data) == 1:
                        row = 0

                    # Преобразование байтов в видимые основные символы ASCII.
                    symbols = list(map(lambda x: chr(x) if chr(x) in ' !"#$%&()*+,-./0123456789:;<=>?@' +
                                                                     "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`" +
                                                                     "abcdefghijklmnopqrstuvwxyz{|}~']))"
                                                                     else ".", symbols))

                    # Наименование строк:
                    if bytes_in_row > 1:
                        # Промежутками шестнадцатиричных чисел, если значение из спин-бокса больше, чем 1.
                        symbols.insert(0,
                                       f"{hex(row * bytes_in_row)[2:].rjust(2, '0')}-" +
                                       f"{hex(row * bytes_in_row + bytes_in_row - 1)[2:].rjust(2, '0')}")
                    else:
                        # Шестнадцатиричными числами.
                        symbols.insert(0, f"{hex(byte)[2:]}")

                    self.listWidget.addItem("\t".join([x for x in symbols]))  # Запись символов в виджет-список.

                    symbols = []  # Очистка cтроки.

                    can_write_start = True
                elif can_write_start:
                    row += 1
                    can_write_start = False

            self.can_update = True

    def clear_data(self):
        # Возвращает таблицу, виджет-список и спинбокс в изначальное состояние.

        self.lineEdit.setText("")  # Тип файла.
        self.spinBox.setValue(8)  # Спинбокс.

        self.can_update = False  # Защита от обновления (не нужно).

        # Таблица.
        self.tableWidget.clear()

        # Восстановление количества строк и столбцов.
        self.tableWidget.setColumnCount(8)
        self.tableWidget.setRowCount(1)

        # Восстановление заголовков строк и столбцов.
        self.tableWidget.setHorizontalHeaderLabels([str(x) for x in range(8)])
        for header in range(8):
            self.tableWidget.horizontalHeaderItem(header).setFont(QFont("MS Sans Serif", 12))
        self.tableWidget.setVerticalHeaderLabels([f"00-07"])

        # Восстановление значения 00.
        cell = QTableWidgetItem("00")
        cell.setTextAlignment(Qt.AlignCenter)

        # Востановление цвета.
        color = QColor()
        color.setRgb(255, 255, 255)
        cell.setBackground(color)

        # Вставка значения.
        self.tableWidget.setItem(0, 0, cell)

        # Виджет-список.
        self.listWidget.clear()
        self.listWidget.addItem("00-07\t.")

        self.can_update = True

    def add_type(self):
        # Открывается форма добавления типа файла в таблицу.

        self.add_type_form = AddTypeForm()
        self.add_type_form.show()  # Открытие формы.


class AddTypeForm(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('add_type.ui', self)  # Загрузка интерфейса.
        self.initUI()

    def initUI(self):
        self.setGeometry(325, 125, 75, 175)
        self.setWindowTitle('Добавить тип файла...')

        self.add.clicked.connect(self.add_type)  # Кнопка "Добавить".
        self.lineEdit.textChanged.connect(self.update_data)
        self.spinBox.valueChanged.connect(self.update_data)
        self.yes.clicked.connect(self.dialogue)  # Кнопка "Поменять значение".
        self.no.clicked.connect(self.dialogue)  # Кнопка "Отменить действие".
        self.yes.hide()
        self.no.hide()

    def add_type(self):
        # Добавление типа файла в БД.
        data_base = sqlite3.connect("file_types.sqlite")  # Подключение к БД.
        cursor = data_base.cursor()

        try:
            id_of_type = cursor.execute('''
            SELECT id FROM file_types
            ''').fetchall()  # Просмотр всех существующих ID.

            id_of_type = max([x[0] for x in id_of_type]) + 1  # Установка нового ID типу файла.

            cursor.execute(f'''
            INSERT INTO file_types VALUES({id_of_type},"{self.lineEdit.text()}",{self.spinBox.text()})
            ''')  # Добавление типа файла.
        except sqlite3.IntegrityError:
            # Формат файла уже есть в БД.

            # Заморозка некоторых кнопок.
            self.add.setEnabled(False)
            self.spinBox.setEnabled(False)
            self.lineEdit.setEnabled(False)

            # Показ диалоговых кнопок.
            self.yes.show()
            self.no.show()

            data_base.close()

            # Оповещение о существовании типа файла в БД.
            self.label_2.setText("Такой тип файла уже есть в базе данных. " +
                                 "Поменять значение конца заголовка у этого типа файла?")
        else:
            # Успешно добавлено.
            data_base.commit()  # Подтверждение добавки типа в БД. Без этой команды он не сохранится.
            data_base.close()
            self.label_2.setText("Данный тип файла успешно добавлен в базу данных!")

    def update_data(self):
        # При смене параметров оповещение пропадает, а текстовая линия делает текст маленького регистра.
        self.lineEdit.setText(self.lineEdit.text().lower())
        self.label_2.setText("")

    def dialogue(self):
        if self.sender().text() == "Поменять значение":
            data_base = sqlite3.connect("file_types.sqlite")  # Подключение к БД.
            cursor = data_base.cursor()

            cursor.execute(f'''
            UPDATE file_types
            SET header_end = {self.spinBox.text()}
            WHERE type = "{self.lineEdit.text()}"
            ''')  # Обновление формата.

            data_base.commit()  # Подтверждение изменения типа в БД. Без этой команды он не изменится.
            data_base.close()
            self.label_2.setText(f"Значение конца заголовка типа файла {self.lineEdit.text()} успешно изменено!")
        else:
            # Возникает при нажатии кнопки "Отменить действие".
            self.label_2.setText("Операция отменена.")

        # Разморозка замороженных объектов.
        self.add.setEnabled(True)
        self.spinBox.setEnabled(True)
        self.lineEdit.setEnabled(True)

        # Скрытие диалоговых кнопок.
        self.yes.hide()
        self.no.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = HEXEditor()
    ex.show()
    sys.exit(app.exec())
