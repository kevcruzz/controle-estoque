from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///estoque.db"

engine = create_engine(DATABASE_URL, echo=True)


def criar_tabelas():
    SQLModel.metadata.create_all(engine)



def get_session():
    with Session(engine) as session:
        yield session

