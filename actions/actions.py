# actions/actions.py

# Importações necessárias
import yaml
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset

# Importa a biblioteca que remove acentos
from unidecode import unidecode

# --- AÇÃO PRINCIPAL: EXPLICAR REMÉDIO (VERSÃO CORRIGIDA) ---
class ActionExplicarRemedio(Action):
    def name(self) -> Text:
        return "action_explicar_remedio"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Tenta carregar o ficheiro de explicações
        try:
            with open('data/expliqueMec.yml', 'r', encoding='utf-8') as file:
                dados_yaml = yaml.safe_load(file)
                # CORREÇÃO: Agora lemos um dicionário, onde a chave é o nome do remédio
                # e o valor é a string da explicação.
                base_de_remedios = dados_yaml.get("explicacoes", {})
        except FileNotFoundError:
            dispatcher.utter_message(text="Desculpe, não consegui aceder à minha base de dados de medicamentos agora.")
            return []
        except Exception as e:
            print(f"Erro ao ler ou processar o ficheiro expliqueMec.yml: {e}")
            dispatcher.utter_message(text="Ocorreu um erro inesperado ao buscar as informações do medicamento.")
            return []

        # Pega a entidade 'remedio' que o Rasa extraiu
        remedio_extraido = next(tracker.get_latest_entity_values("remedio"), None)

        if not remedio_extraido:
            dispatcher.utter_message(response="utter_remedio_nao_identificado")
            return []

        # --- LÓGICA DE BUSCA CORRIGIDA E SIMPLIFICADA ---
        # 1. Normaliza a entrada do utilizador
        remedio_usuario_normalizado = unidecode(remedio_extraido).lower().strip()

        explicacao_encontrada = None
        nome_original_encontrado = None

        # 2. Percorre os itens (chave, valor) do dicionário de remédios
        for nome_original_db, explicacao_db in base_de_remedios.items():
            # 3. Normaliza a chave (nome do remédio) do nosso banco de dados
            nome_db_normalizado = unidecode(nome_original_db).lower().strip()

            # 4. Compara as duas versões normalizadas
            if remedio_usuario_normalizado == nome_db_normalizado:
                explicacao_encontrada = explicacao_db
                nome_original_encontrado = nome_original_db
                break # Para a busca assim que encontrar

        # 5. Responde ao utilizador
        if explicacao_encontrada:
            dispatcher.utter_message(
                text=f"Claro! O medicamento {nome_original_encontrado.capitalize()} serve para o seguinte:\n{explicacao_encontrada}"
            )
        else:
            dispatcher.utter_message(response="utter_explicacao_nao_encontrada", remedio=remedio_extraido)

        return []


# --- OUTRAS AÇÕES (Mantidas como estavam) ---

class ActionAdicionarRemedio(Action):
    def name(self) -> Text:
        return "action_adicionar_remedio"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        remedio_entity = next(tracker.get_latest_entity_values("remedio"), None)

        if not remedio_entity:
            dispatcher.utter_message(response="utter_remedio_nao_identificado")
            return []

        remedio_normalizado = unidecode(remedio_entity).lower().strip()
        lista_atual = tracker.get_slot("remedios_list") or []
        nova_lista = lista_atual.copy()

        if remedio_normalizado not in [unidecode(r).lower().strip() for r in nova_lista]:
            nova_lista.append(remedio_entity.strip())
            dispatcher.utter_message(response="utter_remedio_adicionado", remedio=remedio_entity.strip().capitalize())
        else:
            dispatcher.utter_message(response="utter_remedio_ja_adicionado", remedio=remedio_entity.strip().capitalize())

        return [SlotSet("remedios_list", nova_lista)]


class ActionListarRemedios(Action):
    def name(self) -> Text:
        return "action_listar_remedios"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        remedios_list = tracker.get_slot("remedios_list")

        if not remedios_list:
            dispatcher.utter_message(response="utter_lista_vazia")
        else:
            lista_formatada = "\n".join([f"- {remedio.capitalize()}" for remedio in remedios_list])
            dispatcher.utter_message(response="utter_listar_remedios", lista_remedios=lista_formatada)

        return []


class ActionVerificarInteracoes(Action):
    def name(self) -> Text:
        return "action_verificar_interacoes"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        remedios_list = tracker.get_slot("remedios_list")

        if not remedios_list or len(remedios_list) < 2:
            dispatcher.utter_message(response="utter_interacao_lista_insuficiente")
            return []

        try:
            with open('data/interacoes.yml', 'r', encoding='utf-8') as file:
                db_interacoes = yaml.safe_load(file).get('interacoes', [])
        except FileNotFoundError:
            dispatcher.utter_message(text="Desculpe, não consegui aceder à minha base de dados de interações agora.")
            return []

        remedios_normalizados = [unidecode(r).lower().strip() for r in remedios_list]
        interacoes_encontradas = []

        for i in range(len(remedios_normalizados)):
            for j in range(i + 1, len(remedios_normalizados)):
                remedio1_norm = remedios_normalizados[i]
                remedio2_norm = remedios_normalizados[j]

                for interacao in db_interacoes:
                    pair_norm = {unidecode(p).lower().strip() for p in interacao['pair']}
                    if {remedio1_norm, remedio2_norm} == pair_norm:
                        remedio1_original = remedios_list[i]
                        remedio2_original = remedios_list[j]
                        interacoes_encontradas.append(
                            f"- **Risco entre {remedio1_original.capitalize()} e {remedio2_original.capitalize()}:** {interacao['risco']}"
                        )

        if not interacoes_encontradas:
            dispatcher.utter_message(response="utter_sem_interacoes")
        else:
            texto_interacoes = "\n".join(interacoes_encontradas)
            dispatcher.utter_message(response="utter_interacoes_encontradas", interacoes=texto_interacoes)

        return []


class ActionResetarLista(Action):
    def name(self) -> Text:
        return "action_resetar_lista"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="Ok, a sua lista de medicamentos foi limpa.")
        return [AllSlotsReset()]
