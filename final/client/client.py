import requests
from ..reader import Reader
from ..utils import protocol, Logger

logger = Logger(__name__).logger


def get_parsers_from_server(host, port):
    r = requests.get(f'http://{host}:{port}/config')
    response = r.json()
    if r.status_code != 200:
        logger.error(f"could not get parsers from server due to error. Got {r.status_code} status code")
        return None
    elif response['result'] != 'accepted':
        logger.error(f"could not get parsers from server due to error: {response['error']}")
        return None
    return response['parsers']


def send_to_server(host, port, data, user_id):
    if user_id is None:
        r = requests.post(f'http://{host}:{port}/users', data=data)
    else:
        r = requests.post(f'http://{host}:{port}/snapshots/{user_id}', data=data)
    response = r.json()
    if r.status_code != 201:
        logger.error(f"server did not accept data due to error. Got {r.status_code} status code")
    if response['result'] != 'accepted':
        logger.error(f"server did not accept data due to error: {response['error']}")


def upload_sample(host, port, path):
    reader = Reader(path)
    user_message = protocol.init_protocol_user(reader.user.user_id, reader.user.username,
                                               reader.user.birthday, reader.user.gender)
    serialized_user_message = protocol.serialize(user_message)
    send_to_server(host, port, serialized_user_message, None)
    logger.info('starting to upload snapshots to server')
    for snapshot in reader:
        parsers = get_parsers_from_server(host, port)
        if parsers is None:
            logger.info("parsers is none")
            continue
        config = protocol.init_protocol_config(parsers)
        partial_snapshot = protocol.build_partial_snapshot(snapshot, config)
        serialized_snapshot_message = protocol.serialize(partial_snapshot)
        send_to_server(host, port, serialized_snapshot_message, user_message.user_id)
    logger.info('finished uploading snapshots to server')
    return 0
