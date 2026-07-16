from ..config import load_config, config_digest
def reload_config(path):
    config=load_config(path); return {'applied':False,'reason':'metrics_service_acknowledgement_required','config_digest':config_digest(config)}
