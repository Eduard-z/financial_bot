from aiogram.fsm.state import State, StatesGroup


# Cоздаем класс StatesGroup для нашей машины состояний
class FSMAddFamilyAccount(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодействия с пользователем
    fill_family_account = State()  # Состояние ожидания ввода telegram ID
