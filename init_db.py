from app import create_app

# Importar create_app ja executa o bootstrap_database dentro da factory.
# Este script existe para ser chamado antes do Gunicorn no Railway.
app = create_app()

if __name__ == '__main__':
    print('Banco inicializado com sucesso.')
