
import main
import pytest

from core.data_loader import load_learning_paths


@pytest.fixture
def paths():
    return load_learning_paths()


@pytest.fixture
def prepare_menu(monkeypatch, paths):
    generated = {}

    monkeypatch.setattr(main, "load_learning_paths", lambda: paths)
    monkeypatch.setattr(
        main,
        "generate_certificate",
        lambda **kwargs: generated.update(kwargs),
    )

    return generated


@pytest.mark.parametrize("selection_kind", ["number", "title", "id"])
def test_menu_certificado_accepts_catalog_selection(
    monkeypatch, paths, prepare_menu, selection_kind
):
    selected = paths[0]

    if selection_kind == "number":
        selection = "1"
    elif selection_kind == "title":
        selection = selected.title
    else:
        selection = selected.id

    monkeypatch.setattr(
    main,
    "_prompt_required",
    lambda message: (
        selection if "Escolha a trilha" in message else "Participante"
    ),
)
    monkeypatch.setattr(main, "_prompt", lambda message: "")

    main._menu_certificado()

    assert prepare_menu["participant"] == "Participante"
    assert prepare_menu["activity"] == selected.title
    assert prepare_menu["technology"] == selected.technology
    assert prepare_menu["level"] == selected.level.value
    assert prepare_menu["competencies"] == []
    assert prepare_menu["paths"] == paths



def test_menu_certificado_accepts_custom_competencies(
    monkeypatch, paths, prepare_menu
):
    monkeypatch.setattr(
        main,
        "_prompt_required",
        lambda message: (
            "1" if "Escolha a trilha" in message else "Participante"
        ),
    )
    monkeypatch.setattr(
        main,
        "_prompt",
        lambda message: "Python, APIs, , automação ",
    )

    main._menu_certificado()

    assert prepare_menu["competencies"] == [
        "Python",
        "APIs",
        "automação",
    ]



def test_menu_certificado_rejects_unknown_selection(
    monkeypatch, paths, prepare_menu
):
    inputs = iter(["trilha inexistente"])
    monkeypatch.setattr(
        main,
        "_prompt_required",
        lambda message: next(inputs),
    )

    main._menu_certificado()

    assert prepare_menu == {}


def test_menu_certificado_cancels_selection(
    monkeypatch, prepare_menu
):
    monkeypatch.setattr(
        main,
        "_prompt_required",
        lambda message: None,
    )

    main._menu_certificado()

    assert prepare_menu == {}


def test_menu_certificado_handles_empty_catalog(monkeypatch):
    monkeypatch.setattr(main, "load_learning_paths", lambda: [])
    monkeypatch.setattr(
        main,
        "generate_certificate",
        lambda **kwargs: pytest.fail("Não deveria gerar certificado"),
    )

    main._menu_certificado()


def test_menu_certificado_handles_catalog_loading_error(monkeypatch):
    def raise_error():
        raise RuntimeError("Erro simulado")

    monkeypatch.setattr(main, "load_learning_paths", raise_error)
    monkeypatch.setattr(
        main,
        "generate_certificate",
        lambda **kwargs: pytest.fail("Não deveria gerar certificado"),
    )

    main._menu_certificado()
