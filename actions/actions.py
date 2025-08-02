import yaml
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset

class ActionAdicionarRemedio(Action):
    def __init__(self):
        """
        Carrega a base de conhecimento de medicamentos uma vez na inicialização.
        Isso é mais eficiente do que carregar o arquivo a cada chamada.
        """
        with open('data/expliqueMec.yml', 'r', encoding='utf-8') as file:
            # Padroniza todas as chaves (nomes dos remédios) para minúsculas
            # para evitar erros de case-sensitive (ex: "Dipirona" vs "dipirona")
            self.db_remedios = {k.lower(): v for k, v in yaml.safe_load(file).items()}

    def name(self) -> Text:
        return "action_adicionar_remedio"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Pega o remédio que o Rasa extraiu da fala do usuário
        remedio_entity = next(tracker.get_latest_entity_values("remedio"), None)

        if not remedio_entity:
            dispatcher.utter_message(response="utter_remedio_nao_identificado")
            return []

        # Padroniza o nome do remédio para busca (minúsculas)
        remedio_normalizado = remedio_entity.lower()

        # Verifica se o remédio existe na nossa base de conhecimento
        if remedio_normalizado not in self.db_remedios:
            dispatcher.utter_message(response="utter_remedio_nao_existe", remedio=remedio_entity)
            return []

        # Pega a lista de remédios atual do "slot" (memória do bot)
        remedios_list = tracker.get_slot("remedios_list") or []

        # Adiciona o novo remédio (já normalizado) à lista
        if remedio_normalizado not in remedios_list:
            remedios_list.append(remedio_normalizado)
            dispatcher.utter_message(response="utter_remedio_adicionado", remedio=remedio_entity.capitalize())
        else:
            dispatcher.utter_message(response="utter_remedio_ja_adicionado", remedio=remedio_entity.capitalize())

        # Devolve a lista atualizada para o slot, salvando o estado
        return [SlotSet("remedios_list", remedios_list)]

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
            # Formata a lista para uma apresentação mais clara
            lista_formatada = "\n".join([f"- {remedio.capitalize()}" for remedio in remedios_list])
            dispatcher.utter_message(response="utter_listar_remedios", lista_remedios=lista_formatada)

        return []


class ActionExplicarRemedio(Action):
    def __init__(self):
        with open('data/expliqueMec.yml', 'r', encoding='utf-8') as file:
            self.db_remedios = {k.lower(): v for k, v in yaml.safe_load(file).items()}

    def name(self) -> Text:
        return "action_explicar_remedio"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        remedio_entity = next(tracker.get_latest_entity_values("remedio"), None)

        if not remedio_entity:
            dispatcher.utter_message(response="utter_remedio_nao_identificado")
            return []

        remedio_normalizado = remedio_entity.lower()
        explicacao = self.db_remedios.get(remedio_normalizado)

        if explicacao:
            resposta = f"Claro! O medicamento {remedio_entity.capitalize()} serve para o seguinte:\n\n{explicacao}"
            dispatcher.utter_message(text=resposta)
        else:
            dispatcher.utter_message(response="utter_explicacao_nao_encontrada", remedio=remedio_entity)

        return []

class ActionVerificarInteracoes(Action):
    def __init__(self):
        with open('data/interacoes.yml', 'r', encoding='utf-8') as file:
            self.db_interacoes = yaml.safe_load(file).get('interacoes', [])

    def name(self) -> Text:
        return "action_verificar_interacoes"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        remedios_list = tracker.get_slot("remedios_list")

        if not remedios_list or len(remedios_list) < 2:
            dispatcher.utter_message(response="utter_interacao_lista_insuficiente")
            return []

        interacoes_encontradas = []
        for i in range(len(remedios_list)):
            for j in range(i + 1, len(remedios_list)):
                remedio1 = remedios_list[i]
                remedio2 = remedios_list[j]

                for interacao in self.db_interacoes:
                    pair = set(interacao['pair'])
                    if set([remedio1, remedio2]) == pair:
                        interacoes_encontradas.append(
                            f"- **Risco entre {remedio1.capitalize()} e {remedio2.capitalize()}:** {interacao['risco']}"
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
