def main() -> None:
    from awg_gui import logger as _logger
    from awg_gui.ui import App

    _logger.setup()
    App().run()


if __name__ == "__main__":
    main()
