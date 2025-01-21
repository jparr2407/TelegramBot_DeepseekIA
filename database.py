import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os
import requests

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD')
            )
            print("Conexão com o banco de dados estabelecida com sucesso!")
        except Error as e:
            print(f"Erro ao conectar ao MySQL: {e}")

    def executar_query(self, query, params=None):
        """Executa uma query e retorna os resultados"""
        try:
            if self.connection.is_connected():
                cursor = self.connection.cursor(dictionary=True)
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                resultado = cursor.fetchall()
                cursor.close()
                return resultado
        except Error as e:
            print(f"Erro ao executar query: {e}")
            return None

    def buscar_resposta(self, pergunta):
        """Processa a pergunta do usuário e retorna os dados do banco"""
        try:
            if self.connection.is_connected():
                # Extrai a pergunta atual do contexto se existir
                pergunta_atual = pergunta
                if "Pergunta atual:" in pergunta:
                    pergunta_atual = pergunta.split("Pergunta atual:")[-1].strip()
                
                # Schema fixo do seu banco de dados
                schema_context = """
                Aqui você pode colocar o(s) schema(s) do seu banco de dados, os DDLs das tabelas/views e contextualizar
                o uso de cada tabela (não necessariamente os dados contidos nelas, mas sim como os dodos são utilizados), quanto mais informação
                mais precisa será a resposta.
                """
                
                # Monta o prompt para o Deepseek com o contexto da conversa
                prompt = f"""
                Com base no seguinte schema de banco de dados:
                {schema_context}
                
                Contexto da conversa:
                {pergunta}
                
                Gere APENAS a query SQL para responder à pergunta atual: {pergunta_atual}
                Retorne SOMENTE o comando SQL.
                A query deve seguir estas regras:
                1. Use apenas as tabelas e colunas definidas no schema
                2. Retorne apenas as informações necessárias
                3. Use tipos de joins que achar melhor quando necessário
                4. Não use comandos DDL ou DML (apenas SELECT), mas pode usar funções de agregação.
                5. Se necessário, faça alguns selects para você entender se os dados retornados são os corretos.
                6. Pode mostrar a resposta ao usuário de uma maneira que fique bonita e organizada.
                7. Para colunas separadas com _, utilize ALIAS para tornar mais legível a resposta e não utilize underline nos ALIAS.
                8. Quando for retonar datas, retorne no formato brasileiro (DD/MM/YYYY).
                9. Tente sempre montar a query mais performatica possivel, mas sempre respeitando as regras.
                
                Retorne o resultado explicado em formato de texto para que o usuário possa entender.
                """
                
                # Chama a API do Deepseek
                response = requests.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "model": "deepseek-chat",
                        "temperature": 0.3,
                        "max_tokens": 300
                    }
                )
                
                if response.status_code == 200:
                    # Extrai apenas a query SQL da resposta
                    resposta_completa = response.json()['choices'][0]['message']['content'].strip()
                    
                    # Tenta extrair apenas o SQL se estiver entre ```sql e ```
                    if "```sql" in resposta_completa:
                        query = resposta_completa.split("```sql")[1].split("```")[0].strip()
                    else:
                        query = resposta_completa.strip()
                    
                    print(f"Query a ser executada: {query}")  # Para debug
                    
                    resultado = self.executar_query(query)
                    return self._format_response(resultado)
                    
                return "Não foi possível gerar uma query para sua pergunta."
                
        except Error as e:
            print(f"Erro ao buscar resposta: {e}")
            return "Ocorreu um erro ao processar sua pergunta."

    def _format_response(self, resultado):
        """Formata o resultado da query em uma resposta legível"""
        if not resultado:
            return "Não encontrei informações para responder sua pergunta."
        
        # Formata o resultado em texto
        response_lines = []
        for row in resultado:
            response_lines.append(" | ".join(f"{k}: {v}" for k, v in row.items()))
        
        return "\n".join(response_lines)

    def salvar_mensagem_historico(self, user_id, mensagem):
        """Salva uma mensagem no histórico do usuário"""
        try:
            if self.connection.is_connected():
                # Primeiro, conta quantas mensagens o usuário já tem
                count_query = """
                    SELECT COUNT(*) as total 
                    FROM historico_mensagens 
                    WHERE user_id = %s
                """
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(count_query, (user_id,))
                result = cursor.fetchone()
                total_mensagens = result['total']

                # Se já tiver 5 mensagens, deleta a mais antiga
                if total_mensagens >= 5:
                    delete_query = """
                        DELETE FROM historico_mensagens 
                        WHERE id = (
                            SELECT id 
                            FROM (
                                SELECT id 
                                FROM historico_mensagens 
                                WHERE user_id = %s 
                                ORDER BY created_at ASC 
                                LIMIT 1
                            ) as subquery
                        )
                    """
                    cursor.execute(delete_query, (user_id,))

                # Insere a nova mensagem
                insert_query = """
                    INSERT INTO historico_mensagens (user_id, mensagem) 
                    VALUES (%s, %s)
                """
                cursor.execute(insert_query, (user_id, mensagem))
                self.connection.commit()
                cursor.close()
                return True
        except Error as e:
            print(f"Erro ao salvar mensagem no histórico: {e}")
            return False

    def buscar_historico_usuario(self, user_id):
        """Retorna as últimas 5 mensagens do usuário"""
        try:
            if self.connection.is_connected():
                query = """
                    SELECT mensagem 
                    FROM historico_mensagens 
                    WHERE user_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """
                cursor = self.connection.cursor(dictionary=True)
                cursor.execute(query, (user_id,))
                resultado = cursor.fetchall()
                cursor.close()
                return [row['mensagem'] for row in resultado]
        except Error as e:
            print(f"Erro ao buscar histórico: {e}")
            return []

    def fechar_conexao(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Conexão com o banco de dados fechada.") 