from logic import Logic


def main():
    logic = Logic()
    logic.start()

    # Запускаем приложение.
    logic.app.run_polling()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
