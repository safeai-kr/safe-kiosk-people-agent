def deny_uplink_mutation(argv:list[str],uplink_identifiers:set[str])->None:
    if any(value in uplink_identifiers for value in argv): raise PermissionError('uplink mutation denied')
