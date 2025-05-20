#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitários para manipulação de texto.
"""

import re
import unicodedata
from typing import Optional


def remove_accents(text: str) -> str:
    """
    Remove acentos de um texto.
    
    Args:
        text: Texto com acentos
        
    Returns:
        str: Texto sem acentos
    """
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if not unicodedata.combining(c))


def normalize_game_name(game_name: str) -> str:
    """
    Normaliza o nome do jogo para uso interno.
    
    Args:
        game_name: Nome do jogo
        
    Returns:
        str: Nome normalizado
    """
    # Remove acentos
    name_no_accents = remove_accents(game_name)
    
    # Remove caracteres especiais
    name_clean = re.sub(r'[^\w\s-]', '_', name_no_accents)
    
    # Substitui espaços por underscore
    name_clean = re.sub(r'\s+', '_', name_clean)
    
    # Remove underscores múltiplos
    name_clean = re.sub(r'_+', '_', name_clean)
    
    # Remove underscores no início e fim
    name_clean = name_clean.strip('_')
    
    return name_clean


def sanitize_process_name(process_name: Optional[str]) -> str:
    """
    Sanitiza o nome do processo.
    
    Args:
        process_name: Nome do processo
        
    Returns:
        str: Nome do processo sanitizado sem extensão .exe
    """
    if not process_name:
        return ""
    
    # Remove espaços e remove extensão .exe
    sanitized = process_name.strip()
    
    # Remove extensão .exe se existir
    if sanitized.lower().endswith('.exe'):
        sanitized = sanitized[:-4]  # Remove os últimos 4 caracteres (.exe)
    
    return sanitized