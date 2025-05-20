

def get_lead_id_from_movements(movements, status_to_id):
    """movements - список передвижений клиентов за указанный период
       status_to_id - этап который нас интересует
       возвращаем список id лидов, которые находятся на этом этапе"""
    result = list()
    for movement in movements:
        if movement['to'] == status_to_id:
            result.append(movement['lead_id'])
    return result

def get_phone_from_lead(lead):
    return lead['phones'][0]['value']

def get_source_id_from_lead(lead):
    return lead['lead']['source_id']

def get_valid_lead_phones(leads, source_id_list):
    result = list()
    for lead in leads:
        if get_source_id_from_lead(lead) in source_id_list:
            result.append(get_phone_from_lead(lead))
    return result