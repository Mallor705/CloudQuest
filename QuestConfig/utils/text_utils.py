#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitários para manipulação de texto do QuestConfig.
Fornece funções para normalização e processamento de texto.
"""

import re
import unicodedata

def remove_accents(input_string):
    """
    Remove acentos de uma string
    
    Args:
        input_string (str): String com acentos
        
    Returns:
        str: String sem acentos
    """
    normalized = unicodedata.normalize('NFKD', input_string)
    return ''.join([c for c in normalized if not unicodedata.combining(c)])

def normalize_game_name(game_name):
    """
    Normaliza o nome do jogo para uso em arquivos e caminhos
    
    Args:
        game_name (str): Nome original do jogo
        
    Returns:
        str: Nome normalizado
    """
    # Remove acentos
    normalized = remove_accents(game_name)
    
    # Substitui caracteres especiais por underscore
    normalized = re.sub(r'[^\w\s-]', '_', normalized)
    
    # Substitui espaços por underscore
    normalized = re.sub(r'\s+', '_', normalized)
    
    return normalized