from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.dominio import ErroDominio


def erro_http(status_code: int, code: str, message: str) -> HTTPException:
    """HTTPException com detail estruturado {code, message} — code é estável e nunca
    muda de texto (o frontend deve decidir com base nele, não em message). Usar nos
    routers; nos serviços usa-se ErroDominio (não depende do FastAPI)."""
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


async def erro_dominio_handler(request: Request, exc: ErroDominio) -> JSONResponse:
    """Traduz ErroDominio (levantada pelos serviços) para o mesmo formato {code, message,
    ctx} que erro_http/_formatar_erro produzem — o cliente vê sempre a mesma forma de erro,
    e pode traduzir usando "ctx" em vez de depender do "message" em português."""
    return JSONResponse(status_code=exc.status_code, content={"detail": {"code": exc.code, "message": exc.message, "ctx": exc.ctx}})


MENSAGENS_ERRO: dict[str, str] = {
    "missing": "Este campo é obrigatório.",
    "string_too_short": "Tem de ter pelo menos {min_length} caracteres.",
    "string_too_long": "Não pode ter mais de {max_length} caracteres.",
    "string_type": "Tem de ser texto.",
    "int_type": "Tem de ser um número inteiro.",
    "int_parsing": "Tem de ser um número inteiro válido.",
    "float_type": "Tem de ser um número.",
    "float_parsing": "Tem de ser um número válido.",
    "bool_type": "Tem de ser verdadeiro ou falso.",
    "bool_parsing": "Valor inválido — esperado verdadeiro ou falso.",
    "date_type": "Tem de ser uma data válida.",
    "date_from_datetime_parsing": "Tem de ser uma data válida (AAAA-MM-DD).",
    "date_from_datetime_inexact": "Tem de ser uma data, sem hora.",
}


def _traduzir_erro(erro: dict) -> str:
    tipo = erro["type"]
    if tipo == "value_error" and "email" in erro.get("loc", ()):
        return "Email inválido."
    template = MENSAGENS_ERRO.get(tipo)
    if not template:
        return erro["msg"]
    try:
        return template.format(**erro.get("ctx", {}))
    except (KeyError, IndexError):
        return template


def _formatar_erro(erro: dict) -> dict:
    # o "type" do Pydantic já é um código estável e sem língua — reaproveita-lo em vez
    # de só devolver a mensagem traduzida também deixa a porta aberta para i18n. "ctx" vai
    # em bruto (ex: {"min_length": 8}) para um cliente poder formatar a sua própria
    # mensagem, sem depender do texto português de "message" — ver analise-tesouraria.md,
    # secção "Internacionalização".
    return {
        "code": erro["type"].upper(),
        "message": _traduzir_erro(erro),
        "campo": ".".join(str(p) for p in erro.get("loc", ()) if p != "body"),
        "ctx": erro.get("ctx", {}),
    }


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    erros = [_formatar_erro(e) for e in exc.errors()]
    # code/message/campo no topo continuam a ser só o primeiro erro — é o contrato que já
    # existe e que o frontend já lê; "errors" é aditivo, para quem precisar de mostrar (ou
    # tratar) mais do que um campo inválido de uma vez, sem quebrar quem só lê o topo.
    return JSONResponse(status_code=422, content={"detail": {**erros[0], "errors": erros}})