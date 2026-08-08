from sqlmodel import Session, select
 
 
def buscar_do_tenant(session: Session, Modelo, registro_id: int, empresa_id: int):
    """
    Substituto seguro de session.get().
 
    session.get(Produto, 5) busca so pelo id: uma empresa conseguiria ler
    o registro de outra apenas chutando numeros. Esta funcao exige que o
    registro pertenca a empresa do usuario logado.
    """
    if registro_id is None:
        return None
    return session.exec(
        select(Modelo)
        .where(Modelo.id == registro_id)
        .where(Modelo.empresa_id == empresa_id)
    ).first()