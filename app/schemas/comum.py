from pydantic import BaseModel


class OkResponse(BaseModel):
    """Resposta partilhada pelos endpoints de escrita que só confirmam sucesso."""
    ok: bool = True
