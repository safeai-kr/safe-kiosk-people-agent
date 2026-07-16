from ..config import config_digest, load_config
def check_config(path,live=False):
    config=load_config(path); return {'config_schema':'v1','config_digest':config_digest(config),'live':bool(live)}
