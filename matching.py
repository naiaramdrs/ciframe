def normalizar_acordes(acordes):
    return [acorde.lower() for acorde in acordes]


def sequencia_aparece_em(sequencia, cifra):
    if not sequencia or not cifra:
        return False

    seq = normalizar_acordes(sequencia)
    cifra_norm = normalizar_acordes(cifra)
    seq_tokens = set(seq)

    if any(acorde not in seq_tokens for acorde in cifra_norm):
        return False

    tamanho = len(seq)
    for inicio in range(len(cifra_norm) - tamanho + 1):
        if cifra_norm[inicio:inicio + tamanho] == seq:
            return True

    return False
