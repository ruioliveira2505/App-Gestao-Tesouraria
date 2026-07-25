class ErroDominio(Exception):
    """Excepção de negócio, levantada pelos serviços — nunca pelos routers directamente.

    Não depende do FastAPI de propósito: um serviço deve poder ser chamado (e testado)
    sem precisar de um pedido HTTP a sério. O router nem sequer precisa de a apanhar —
    o exception handler global (ver app/main.py) trata da tradução para JSON.
    """

    def __init__(self, status_code: int, code: str, message: str, ctx: dict | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        # dados em bruto por trás de "message" (ex.: {"n": 3}) — "message" já vem formatada
        # em português para quem não traduzir; "ctx" é para quem traduzir (o frontend) poder
        # construir a sua própria frase com o valor certo, em vez de repetir o texto
        # português ou perder a informação. Mesma ideia já usada nos erros de validação do
        # Pydantic (ver core/errors.py::_formatar_erro), agora também aqui.
        self.ctx = ctx or {}
        super().__init__(message)
