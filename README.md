# Project 6

## Configuração do Projeto

1. Clone o repositório:

   ```bash
   git clone $repos-url project-five
   cd project-five
   ```

## Ex00 – Configuração do ambiente Continue.dev

## Ex01 – Análise de codebase do ChromaDB

## Ex02 - Ex02 – Quebra estratégica de informações para uma busca ainda melhor

Este projeto é uma API para gerenciamento de currículos que utiliza Flask, ChromaDB e Flask-Limiter. O sistema permite realizar upload de currículos, buscar currículos armazenados e deletar currículos, com diferentes níveis de permissão de acordo com a role do usuário.

## Configuração do Projeto

1. Clone o repositório e entre no diretório `ex02`:
    ```bash
    cd ex02
    ```

2. Crie um ambiente virtual Python:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # No Windows, use `venv\Scripts\activate`
    ```

3. Instale os requerimentos:
    ```bash
    pip install -r requirements.txt
    ```

4. Execute a aplicação:
    ```bash
    python secure_resume_api.py
    ```

A aplicação estará disponível em `http://localhost:5000`.

## Operações da API

### 1. **Upload de Currículos**

- Endpoint: `POST /upload_pdf`
- Descrição: Permite o upload de um arquivo PDF contendo o currículo.
- Restrições: Apenas usuários sem a role `candidato` podem enviar currículos.

Exemplo de requisição como `user`:

```bash
curl -u user:user -F "file=@curriculos/curriculo_1.pdf" http://localhost:5000/upload_pdf
```

Exemplo de requisição como `user2`:

```bash
curl -u user2:user2 -F "file=@curriculos/curriculo_2.pdf" http://localhost:5000/upload_pdf
```

Exemplo de requisição como `user3`:

```bash
curl -u user3:user3 -F "file=@curriculos/curriculo_3.pdf" http://localhost:5000/upload_pdf
```

Exemplo de requisição como `admin` (para os demais currículos):

```bash
curl -u admin:admin -F "file=@curriculos/curriculo_4.pdf" http://localhost:5000/upload_pdf
curl -u admin:admin -F "file=@curriculos/curriculo_5.pdf" http://localhost:5000/upload_pdf
curl -u admin:admin -F "file=@curriculos/curriculo_6.pdf" http://localhost:5000/upload_pdf
curl -u admin:admin -F "file=@curriculos/curriculo_7.pdf" http://localhost:5000/upload_pdf
curl -u admin:admin -F "file=@curriculos/curriculo_8.pdf" http://localhost:5000/upload_pdf
curl -u admin:admin -F "file=@curriculos/curriculo_9.pdf" http://localhost:5000/upload_pdf
curl -u admin:admin -F "file=@curriculos/curriculo_10.pdf" http://localhost:5000/upload_pdf
```

Exemplo de requisição como `rh`:
```bash
curl -u rh:rh -F "file=@curriculos/curriculo_4.pdf" http://localhost:5000/upload_pdf
```

### 2. **Busca de Currículos**

- Endpoint: `GET /search`
- Descrição: Permite realizar uma busca semântica nos currículos processados.
- Parâmetros:
  - `query`: A consulta a ser realizada.
  - `limit`: Número de resultados a serem retornados (padrão é 3).
- Permissões:
  - `candidato`: Pode buscar apenas seus próprios currículos.
  - `recrutador`: Pode buscar todos os currículos.
  - `admin`: Pode buscar todos os currículos.

Exemplo de requisição como `user`:

```bash
curl -u user:user "http://localhost:5000/search?query=Python&limit=3"
```

Exemplo de requisição como `rh` (recrutador):

```bash
curl -u rh:rh "http://localhost:5000/search?query=Engenharia&limit=3"
```

Exemplo de requisição como `admin`:

```bash
curl -u admin:admin "http://localhost:5000/search?query=Data Science&limit=3"
```

### 3. **Deletar Currículo**

- Endpoint: `DELETE /delete_curriculum/<file_id>`
- Descrição: Permite excluir um currículo com base no seu `file_id`.
- Restrições: Apenas usuários com a role `admin` podem deletar currículos.

Exemplo de requisição como `admin` para deletar o currículo com ID `curriculo_1.pdf`:

```bash
curl -u admin:admin -X DELETE "http://localhost:5000/delete_curriculum/curriculo_1.pdf"
```

Exemplo de requisição como `rh` para deletar o currículo com ID `curriculo_2.pdf`:

```bash
curl -u rh:rh -X DELETE "http://localhost:5000/delete_curriculum/curriculo_1.pdf"
```

Exemplo de requisição como `user` para deletar o currículo com ID `curriculo_2.pdf`:

```bash
curl -u user:user -X DELETE "http://localhost:5000/delete_curriculum/curriculo_1.pdf"
```



### 4. **Limite de Taxa**

Para evitar abusos e ataques DoS, há limites de taxa configurados para as rotas:
- **Upload de PDF**: Limite de **10 requisições por minuto**.
- **Busca**: Limite de **10 requisições por minuto**.
- **Deleção de Currículo**: Limite de **3 requisições por minuto**.

Caso o limite de taxa seja excedido, a resposta será:

```json
{
    "error": "Limite de taxa excedido. Tente novamente mais tarde."
}
```

## Considerações Finais

- Os currículos devem estar localizados na pasta `ex02/curriculos`.
- Certifique-se de que cada upload seja feito com as credenciais corretas, conforme descrito acima.
- Para simular diferentes permissões, altere o usuário utilizado no comando `curl` e observe como a API responde de acordo com a role atribuída ao usuário.


---