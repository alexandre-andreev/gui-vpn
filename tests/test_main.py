from awg_gui.__main__ import main


def test_main_prints_ok(capsys):
    main()
    assert capsys.readouterr().out.strip() == "ok"
