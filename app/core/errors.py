from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

MENSAGENS_ERRO = {
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


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    mensagem = _traduzir_erro(exc.errors()[0])
    return JSONResponse(status_code=422, content={"detail": mensagem})